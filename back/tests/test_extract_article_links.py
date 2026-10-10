from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Document, DocumentContent, DocumentLink, DocumentVersion
from app.services.document_content import utf16_length, utf16_slice
from scripts.extract_article_links import build_proposals, insert_missing_links


def test_proposals_use_utf16_article_ranges_and_ignore_self_or_missing_articles():
    text = (
        "머리말 😀\n"
        "제1조(첫째)\n이 조는 제1조, 제2조 및 제99조를 따른다. 제2항과 제3호는 무시한다.\n"
        "제2조(둘째)\n제2조의 규정과 제1조를 따른다.\n"
        "제3조 삭제\n"
        "제4조(넷째)\n제3조와 제4항은 대상이 아니다.\n"
    )

    proposals = build_proposals("version-1", text)

    assert [(source, target) for source, target, _ in proposals] == [(1, 2), (2, 1)]
    for _, _, link in proposals:
        for selection in (link.source_selection, link.target_selection):
            part = selection["ranges"][0]
            assert part["start"] == utf16_length(text[: text.index(part["exact"])])
            assert utf16_slice(text, part["start"], part["end"]) == part["exact"]
            assert selection["version_id"] == "version-1"


def test_insert_missing_links_is_idempotent_in_sqlite():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    text = "제1조(첫째)\n제2조에 따른다.\n제2조(둘째)\n제1조에 따른다.\n"
    with Session(engine) as db:
        document = Document(filename="regulation.hwp", sha256="d" * 64)
        db.add(document)
        db.flush()
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            sha256="v" * 64,
            storage_path="regulation.hwp",
            status="completed",
        )
        db.add(version)
        db.flush()
        db.add(DocumentContent(version_id=version.id, kind="text", text=text))
        db.commit()

        proposals = build_proposals(version.id, text)
        assert insert_missing_links(db, proposals) == 2
        assert insert_missing_links(db, proposals) == 0
        links = list(db.scalars(select(DocumentLink)))
        assert len(links) == 2
        assert {(link.relation_type, link.status, link.created_by) for link in links} == {
            ("REFERENCES", "draft", "article-xref")
        }
    engine.dispose()
