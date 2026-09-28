import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import Base
from app.models import Document, DocumentContent, DocumentVersion, Fragment, KnowledgeEdge
from app.services.document_content import overlaps, utf16_length
from app.services.embedding import HashEmbeddingProvider
from app.services.rag import (
    Evidence,
    GraphRAGService,
    _search_tokens,
    _slide_sections,
    answer_options,
    drop_invalid_citations,
)


def _fragment(version_id: str, stable_key: str, text: str, embedding: list[float]) -> Fragment:
    return Fragment(
        version_id=version_id,
        stable_key=stable_key,
        kind="paragraph",
        ordinal=0,
        text=text,
        locator_json={"stable_key": stable_key},
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        embedding_json=embedding,
        embedding_vector=embedding,
        embedding_model="hash:hash-v1",
    )


def test_rag_splits_rule_chunks_by_article(tmp_path) -> None:
    service = GraphRAGService(
        Settings(storage_root=tmp_path, embedding_dimensions=64),
        HashEmbeddingProvider(dimensions=64),
    )
    fragment = _fragment(
        "version",
        "chunk",
        "\uc81c325\uc870(\uc0c1)\n\nold\n\n\uc81c326\uc870(\ucc28\ub7c9\uace0\uc7a5)\n\nreport",
        [0.0] * 64,
    )
    fragment.kind = "document"
    fragment.metadata_json = {"text_start": 1000, "text_end": 1040}

    units = service._article_units([fragment])

    assert [unit.locator_json["article"] for unit in units] == ["\uc81c325\uc870", "\uc81c326\uc870"]
    assert units[1].metadata_json["text_start"] > units[0].metadata_json["text_start"]


def test_rag_reconstructs_cross_chunk_article_with_unicode_offsets(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = HashEmbeddingProvider(dimensions=64)
    service = GraphRAGService(Settings(storage_root=tmp_path, embedding_dimensions=64), provider)
    canonical = "서문😀\n\n제1조(첫째)\n앞부분😀\n중간 내용\n끝부분\n\n제2조(둘째)\n두 번째 내용"
    first_heading = canonical.index("제1조")

    with Session(engine) as db:
        document = Document(filename="규정.hwp", sha256="b" * 64, status="ready")
        db.add(document)
        db.flush()
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            sha256="b" * 64,
            storage_path="/tmp/규정.hwp",
            status="completed",
        )
        db.add(version)
        db.flush()
        db.add(DocumentContent(version_id=version.id, kind="text", text=canonical, pages=[]))
        split = first_heading + 18
        chunks = []
        for index, (start, end) in enumerate(((0, split), (split - 5, len(canonical)))):
            chunk = _fragment(
                version.id,
                f"canonical:chunk:{index}",
                canonical[start:end],
                provider.embed([canonical[start:end]])[0],
            )
            chunk.kind = "document"
            chunk.metadata_json = {
                "chunk_start": start,
                "chunk_end": end,
                "text_start": utf16_length(canonical[:start]),
                "text_end": utf16_length(canonical[:end]),
            }
            chunks.append(chunk)
        db.add_all(chunks)
        db.flush()

        units = service._article_units(chunks, db)
        article = next(unit for unit in units if unit.locator_json.get("article") == "제1조")
        content = db.get(DocumentContent, version.id)

    assert article.text.endswith("끝부분")
    assert "😀" in article.text
    assert article.metadata_json["text_start"] == utf16_length(canonical[:first_heading])
    assert article.metadata_json["text_end"] == article.metadata_json["text_start"] + utf16_length(article.text)
    selection = {
        "kind": "text",
        "version_id": version.id,
        "ranges": [
            {
                "start": article.metadata_json["text_start"],
                "end": article.metadata_json["text_end"],
                "exact": article.text,
            }
        ],
    }
    assert overlaps(article, selection, content)
    assert any(unit.locator_json.get("article") == "제2조" for unit in units)


def test_rag_expands_only_approved_edges(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = HashEmbeddingProvider(dimensions=64)
    settings = Settings(storage_root=tmp_path, embedding_dimensions=64, default_graph_hops=2)
    service = GraphRAGService(settings, provider)

    with Session(engine) as db:
        document = Document(filename="규정.hwp", sha256="a" * 64, status="ready")
        db.add(document)
        db.flush()
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            sha256="a" * 64,
            storage_path="/tmp/규정.hwp",
            status="completed",
        )
        db.add(version)
        db.flush()
        seed_embedding = provider.embed(["ATC 고장 조치"])[0]
        seed = _fragment(version.id, "seed", "ATC 고장 조치", seed_embedding)
        approved_target = _fragment(
            version.id,
            "approved-target",
            "관련 규정에 따른 운전 절차",
            provider.embed(["운전 절차"])[0],
        )
        draft_target = _fragment(
            version.id,
            "draft-target",
            "아직 승인되지 않은 예외 절차",
            provider.embed(["예외 절차"])[0],
        )
        db.add_all([seed, approved_target, draft_target])
        db.flush()
        db.add_all(
            [
                KnowledgeEdge(
                    source_fragment_id=seed.id,
                    target_fragment_id=approved_target.id,
                    relation_type="REFERENCES",
                    status="approved",
                ),
                KnowledgeEdge(
                    source_fragment_id=seed.id,
                    target_fragment_id=draft_target.id,
                    relation_type="RELATED",
                    status="draft",
                ),
            ]
        )
        db.commit()

        evidence = service.retrieve(db, "ATC 고장 조치", top_k=1, max_hops=1)

    evidence_ids = {item.fragment.id for item in evidence}
    assert seed.id in evidence_ids
    assert approved_target.id in evidence_ids
    assert draft_target.id not in evidence_ids
    assert any(item.fragment.id == approved_target.id and item.hop == 1 for item in evidence)


def test_relevant_target_selections_keep_question_specific_ranges() -> None:
    selection = {
        "kind": "text",
        "version_id": "version",
        "ranges": [
            {"start": index, "end": index + 1, "exact": text}
            for index, text in enumerate(
                ("제34조 운전시각 기록", "제66조 ATC 고장 보고", "제144조 ATC 회송", "제194조 선로전환기")
            )
        ],
    }

    selected = GraphRAGService._relevant_target_selections(
        selection, _search_tokens("ATC 장치 고장 회송")
    )

    assert [part["exact"] for item in selected for part in item["ranges"]] == [
        "제66조 ATC 고장 보고",
        "제144조 ATC 회송",
    ]

    # A longer rewritten query must not squeeze out a passage that still matches well.
    long_selection = {
        **selection,
        "ranges": [
            {"start": index, "end": index + 1, "exact": text}
            for index, text in enumerate((
                "제34조 운전시각 기록",
                "제66조 ATC 고장 보고",
                "제67조 ATC 고장 지령식 운전 45km/h",
                "제144조 ATC 고장 지령식 회송 승객 하차",
            ))
        ],
    }
    selected = GraphRAGService._relevant_target_selections(
        long_selection, _search_tokens("ATC 고장 지령식 회송 승객 하차 운전")
    )
    exacts = [part["exact"] for item in selected for part in item["ranges"]]
    assert "제67조 ATC 고장 지령식 운전 45km/h" in exacts and "제34조 운전시각 기록" not in exacts


def test_rag_expands_synthetic_article_edges(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = HashEmbeddingProvider(dimensions=64)
    settings = Settings(storage_root=tmp_path, embedding_dimensions=64, default_graph_hops=2)
    service = GraphRAGService(settings, provider)

    with Session(engine) as db:
        document = Document(filename="규정.hwp", sha256="c" * 64, status="ready")
        db.add(document)
        db.flush()
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            sha256="c" * 64,
            storage_path="/tmp/규정.hwp",
            status="completed",
        )
        db.add(version)
        db.flush()

        seed_embedding = provider.embed(["구원열차 방호"])[0]
        seed = _fragment(version.id, "seed", "제321조(구원열차 방호)\n구원열차 요구 시 방호 조치한다.", seed_embedding)
        seed.kind = "document"

        target_embedding = provider.embed(["연결 운전"])[0]
        target = _fragment(version.id, "target", "제322조(연결 운전)\n구원열차 연결 운전 절차.", target_embedding)
        target.kind = "document"

        db.add_all([seed, target])
        db.flush()
        db.add(
            KnowledgeEdge(
                source_fragment_id=seed.id,
                target_fragment_id=target.id,
                relation_type="REFERENCES",
                status="approved",
            )
        )
        db.commit()

        evidence = service.retrieve(db, "구원열차 방호", top_k=1, max_hops=1)

    assert any(item.hop == 1 and "제322조" in (item.fragment.text or "") for item in evidence)



def test_location_label_names_page_article_or_heading():
    from app.models import Fragment
    from app.services.rag import _location_label

    assert _location_label(Fragment(locator_json={"page": 3}, text="본문")) == "페이지 3"
    assert _location_label(Fragment(locator_json={"slide": 2}, text="본문")) == "슬라이드 2"
    assert _location_label(Fragment(locator_json={"slide": 80, "chunk": 1}, text="표")) == "슬라이드 80 (2부)"
    assert _location_label(Fragment(locator_json={"document": True}, text="제12조(조치)\n내용")) == "제12조"
    assert _location_label(
        Fragment(locator_json={"ranges": []}, text="제66조(고장)\n가.\n\n제67조(해제)\n①\n\n제144조(지령식)\n③")
    ) == "제66조·제67조·제144조"
    assert _location_label(Fragment(locator_json={}, text="운전취급 절차\n내용")) == "「운전취급 절차」 부분"
    assert _location_label(
        Fragment(locator_json={}, text="x"), {"kind": "pages", "pages": [4, 5]}
    ) == "페이지 4-5"


def test_last_article_stops_at_appendix(tmp_path) -> None:
    service = GraphRAGService(
        Settings(storage_root=tmp_path, embedding_dimensions=64),
        HashEmbeddingProvider(dimensions=64),
    )
    fragment = _fragment("version", "chunk", "제364조(출입금지) 본문\n부 칙\n(시행일) 시행한다.", [0.0] * 64)
    fragment.kind = "document"

    units = service._article_units([fragment])

    article = next(unit for unit in units if unit.locator_json.get("article") == "제364조")
    assert article.text == "제364조(출입금지) 본문"
    assert any("시행한다" in unit.text for unit in units)


def test_link_passages_are_shown_once() -> None:
    content = DocumentContent(version_id="v", kind="text", text="제46조 감시\n제328조 출입문\n제242조 전호")
    shared = {"start": 0, "end": 7, "exact": "제46조 감시"}
    evidence = {}
    for key, score, extra in (("a", 0.9, {"start": 8, "end": 18, "exact": "제328조 출입문"}),
                              ("b", 0.5, {"start": 19, "end": 28, "exact": "제242조 전호"})):
        selection = {"kind": "text", "version_id": "v", "ranges": [shared, extra]}
        evidence[key] = Evidence(fragment=Fragment(id=key, text=""), score=score, hop=1,
                                 path=[], link_id=key, selection=selection)
    evidence["c"] = Evidence(fragment=Fragment(id="c", text=""), score=0.4, hop=1, path=[],
                             link_id="c", selection={"kind": "text", "version_id": "v", "ranges": [shared]})

    GraphRAGService._dedupe_link_passages(evidence, {"v": content})

    assert set(evidence) == {"a", "b"}
    assert len(evidence["a"].selection["ranges"]) == 2
    assert evidence["b"].fragment.text == "제242조 전호"


def test_invalid_citations_are_dropped() -> None:
    answer = "보고한다 [근거 2]. 정차한다 [근거 2, 근거 9]. 없음 [근거 7]."

    assert drop_invalid_citations(answer, 5) == "보고한다 [근거 2]. 정차한다 [근거 2]. 없음 ."


def test_guide_slides_inherit_their_section_heading() -> None:
    def slide(number: int, text: str) -> Fragment:
        return Fragment(id=str(number), version_id="deck", kind="slide", text=text,
                        locator_json={"slide": number})

    units = [slide(47, "10 ) ATC 장치 고장 시 ̶ 점검사항\n도형"), slide(48, "현 상\n고장메세지"),
             slide(49, "원 인\n통신고장"), slide(50, "ADU 제어 해설도"), slide(51, "현 상\nADU")]

    assert list(_slide_sections(units).values()) == ["ATC 장치 고장 시"] * 3 + ["", ""]

    # A slide that names its own section keeps it even when its first line is not a heading.
    tc_slide = slide(37, "전부 AP.CBSU1TC 차단 시\n조 치 사 항\n지령식 45Km/h 이하\n\n"
                         "5 ) 전부 TC1 및 후부 TC1 • 2 동시 고장 시 ̶ 길라잡이\n101")
    assert list(_slide_sections([tc_slide]).values()) == ["전부 TC1 및 후부 TC1 • 2 동시 고장 시"]


def test_answer_options_stay_deterministic_unless_reasoning_is_configured(tmp_path) -> None:
    settings = Settings(storage_root=tmp_path, answer_reasoning_effort="none")
    assert answer_options(settings, "gpt-5.6-luna") == {"reasoning_effort": "none", "temperature": 0}

    settings.answer_reasoning_effort = "low"
    assert answer_options(settings, "gpt-5.6-luna") == {"reasoning_effort": "low"}
    assert answer_options(settings, "gpt-4o") == {"temperature": 0}


def test_renumbered_citations_point_back_at_their_passage() -> None:
    from app.services.rag import fix_citations

    passages = [
        "제305조(열차방호를 하는 경우) ① 선로 고장으로 급히 열차를 정차시킬 때 제1종 방호를 하여야 한다.",
        "제315조(구원열차를 요구한 경우의 조치) 고장열차는 구원열차 도착할 때까지 이동할 수 없다.",
        (
            "제321조(구원열차에 대한 정차열차의 방호) 정거장외에서 정차한 경우 구원열차를 요구하였을 때에는 "
            "제2종 방호를 하여야 한다. 다만, 구원열차가 오지 않음이 확실한 방향은 이를 생략할 수 있다."
        ),
    ]
    # The model numbered by first use: 제321조 came out as [근거 1].
    answer = "정거장 외에서 구원열차를 요구하면 제2종 방호를 하여야 합니다. 구원열차가 오지 않음이 확실한 방향은 생략할 수 있습니다. [근거 1]"

    assert fix_citations(answer, passages).endswith("[근거 3]")
    # Run 20260919_staff_i: a paraphrase that only partly repeats the article (coverage ≈ 0.69).
    loose = ("정거장 외에서 사고로 정차한 열차가 구원열차를 요구하거나 구원열차 운전 통보를 받으면 제2종 방호를 "
             "하여야 합니다. 다만, 구원열차가 오지 않음이 확실한 방향은 생략할 수 있습니다. [근거 1]")
    assert fix_citations(loose, passages).endswith("[근거 3]")
    # A citation that already points at its passage, or shares a sentence with another, is left alone.
    assert fix_citations(answer.replace("[근거 1]", "[근거 3]"), passages).endswith("[근거 3]")
    assert fix_citations(answer.replace("[근거 1]", "[근거 1][근거 3]"), passages).endswith("[근거 1][근거 3]")
