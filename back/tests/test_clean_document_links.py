from copy import deepcopy

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Document, DocumentContent, DocumentLink, DocumentVersion
from app.services.document_content import utf16_length, utf16_slice
from scripts.clean_document_links import DROP_ARTICLES, clean_links


def make_range(text, exact):
    index = text.index(exact)
    start = utf16_length(text[:index])
    end = start + utf16_length(exact)
    return {
        "start": start,
        "end": end,
        "exact": exact,
        "prefix": text[:index][-40:],
        "suffix": text[index + len(exact) :][:40],
    }


@pytest.fixture
def link_db():
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        target = Document(filename="운전취급규정.hwp", sha256="target-hash", status="ready")
        source_one = Document(
            filename="6호선 전동차고장조치 길라잡이-1.pptx", sha256="source-one-hash", status="ready"
        )
        source_two = Document(filename="guide-2.pptx", sha256="source-two-hash", status="ready")
        db.add_all([target, source_one, source_two])
        db.flush()
        target_version = DocumentVersion(
            document_id=target.id, version_number=1, sha256="target-version", storage_path="unused",
            status="completed",
        )
        source_versions = [
            DocumentVersion(document_id=doc.id, version_number=1, sha256=f"v-{i}",
                            storage_path="unused", status="completed")
            for i, doc in enumerate((source_one, source_two))
        ]
        db.add_all([target_version, *source_versions])
        db.flush()

        article_texts = {
            number: f"제{number}조(제외)\n제외 후보 {number}"
            for number in DROP_ARTICLES
        }
        article_texts.update(
            {
                35: "제35조(판토그래프 상승불능)\n정상 내용 😀",
                46: "제46조(신호)\n정상 내용 😀\n\n제5절 신호의 지시",
                328: "제328조(운행)\n정상 내용\n\n제329조 <삭제 2017.12.21.>",
            }
        )
        text = "\n\n".join(article_texts[number] for number in sorted(article_texts))
        db.add(DocumentContent(version_id=target_version.id, kind="text", text=text, pages=[]))
        db.flush()

        def add_link(source_index, pages, ranges):
            link = DocumentLink(
                source_version_id=source_versions[source_index].id,
                target_version_id=target_version.id,
                source_selection={"kind": "pages", "version_id": source_versions[source_index].id,
                                 "pages": pages},
                target_selection={
                    "kind": "text",
                    "version_id": target_version.id,
                    "ranges": ranges,
                },
                relation_type="REFERENCES",
                status="approved",
            )
            db.add(link)
            db.flush()
            return link

        first_ranges = [make_range(text, article_texts[number])
                        for number in sorted(DROP_ARTICLES | {46, 328}, reverse=True)]
        special_link = add_link(0, [35, 36], first_ranges)
        donor_link = add_link(1, [1], [make_range(text, article_texts[35])])
        zero_link = add_link(1, [2], [make_range(text, article_texts[26])])
        db.commit()
        yield db, text, special_link, donor_link, zero_link
    engine.dispose()


def test_cleanup_drops_trims_adds_35_and_keeps_zero_range_link(link_db):
    db, text, special_link, donor_link, zero_link = link_db
    zero_selection = deepcopy(zero_link.target_selection)

    links, changed, zero_ranges, trimmed_chars = clean_links(db)

    assert (links, changed, zero_ranges) == (3, 1, 1)
    assert trimmed_chars == len("\n\n제5절 신호의 지시") + len("\n\n제329조 <삭제 2017.12.21.>")
    ranges = special_link.target_selection["ranges"]
    assert [int(part["exact"].split("조", 1)[0][1:]) for part in ranges] == [35, 46, 328]
    assert ranges[0] == donor_link.target_selection["ranges"][0]
    assert ranges[1]["exact"] == "제46조(신호)\n정상 내용 😀"
    assert ranges[2]["exact"] == "제328조(운행)\n정상 내용"
    for part in ranges:
        assert part["end"] == part["start"] + utf16_length(part["exact"])
        assert utf16_slice(text, part["start"], part["end"]) == part["exact"]
    assert ranges[1]["suffix"] == text[text.index(ranges[1]["exact"]) + len(ranges[1]["exact"]) :][:40]
    assert zero_link.target_selection == zero_selection


def test_cleanup_is_idempotent(link_db):
    db, _text, special_link, _donor_link, _zero_link = link_db
    clean_links(db)
    first_result = deepcopy(special_link.target_selection)

    links, changed, zero_ranges, trimmed_chars = clean_links(db)

    assert (links, changed, zero_ranges, trimmed_chars) == (3, 0, 1, 0)
    assert special_link.target_selection == first_result
