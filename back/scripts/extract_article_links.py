from __future__ import annotations

import argparse
import re

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Document, DocumentContent, DocumentLink, DocumentVersion
from app.services.document_content import utf16_length

DATABASE_URL = "sqlite:///D:/Codes/Dongguk_University/2026-da-al-g/data/data_graph/daalgi.db"
ARTICLE_RE = re.compile(r"(?m)^[ \t]*제(\d+)조\(")
REFERENCE_RE = re.compile(r"제(\d+)조(?!의\d)")
DELETED_STUB_RE = re.compile(r"(?s)^제\d+조\([^)]*\)\s*(?:삭제|<삭제[^>]*>)\s*$")


def article_ranges(text: str) -> dict[int, dict[str, int | str]]:
    matches = list(ARTICLE_RE.finditer(text))
    articles = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw = text[match.start() : end]
        article = raw.strip()
        if (
            not article
            or DELETED_STUB_RE.fullmatch(article)
            or re.fullmatch(rf"제{match.group(1)}조\(\s*삭제\s*\)", article)
        ):
            continue
        start = match.start() + len(raw) - len(raw.lstrip())
        articles[int(match.group(1))] = {
            "start": utf16_length(text[:start]),
            "end": utf16_length(text[:start]) + utf16_length(article),
            "exact": article,
        }
    return articles


def build_proposals(version_id: str, text: str) -> list[tuple[int, int, DocumentLink]]:
    articles = article_ranges(text)
    proposals = []
    seen = set()
    for source_number, source_range in articles.items():
        for match in REFERENCE_RE.finditer(source_range["exact"]):
            target_number = int(match.group(1))
            pair = (source_number, target_number)
            if target_number not in articles or target_number == source_number or pair in seen:
                continue
            seen.add(pair)
            proposals.append(
                (
                    source_number,
                    target_number,
                    DocumentLink(
                        source_version_id=version_id,
                        target_version_id=version_id,
                        source_selection={
                            "kind": "text",
                            "version_id": version_id,
                            "ranges": [source_range],
                        },
                        target_selection={
                            "kind": "text",
                            "version_id": version_id,
                            "ranges": [articles[target_number]],
                        },
                        relation_type="REFERENCES",
                        status="draft",
                        created_by="article-xref",
                    ),
                )
            )
    return proposals


def _selection_range(selection: dict) -> tuple[tuple[int, int], ...]:
    ranges = selection.get("ranges") or [selection]
    return tuple((part["start"], part["end"]) for part in ranges)


def missing_proposals(
    db: Session, proposals: list[tuple[int, int, DocumentLink]]
) -> list[tuple[int, int, DocumentLink]]:
    version_ids = {link.source_version_id for _, _, link in proposals}
    existing = (
        db.scalars(select(DocumentLink).where(DocumentLink.source_version_id.in_(version_ids)))
        if version_ids
        else []
    )
    signatures = {
        (
            link.source_version_id,
            _selection_range(link.source_selection),
            link.target_version_id,
            _selection_range(link.target_selection),
            link.relation_type,
        )
        for link in existing
    }
    missing = []
    for source_number, target_number, link in proposals:
        signature = (
            link.source_version_id,
            _selection_range(link.source_selection),
            link.target_version_id,
            _selection_range(link.target_selection),
            link.relation_type,
        )
        if signature not in signatures:
            missing.append((source_number, target_number, link))
            signatures.add(signature)
    return missing


def insert_missing_links(db: Session, proposals: list[tuple[int, int, DocumentLink]]) -> int:
    missing = missing_proposals(db, proposals)
    db.add_all(link for _, _, link in missing)
    db.commit()
    return len(missing)


def main() -> None:
    parser = argparse.ArgumentParser(description="Propose same-regulation article reference links.")
    parser.add_argument("--filename", default="운전취급규정.hwp")
    parser.add_argument("--apply", action="store_true", help="Insert proposed draft links.")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    with Session(engine) as db:
        document = db.scalars(
            select(Document)
            .where(Document.filename == args.filename)
            .order_by(Document.updated_at.desc())
        ).first()
        if document is None:
            parser.error(f"Document not found: {args.filename}")
        version_and_content = db.execute(
            select(DocumentVersion, DocumentContent)
            .join(DocumentContent, DocumentContent.version_id == DocumentVersion.id)
            .where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.status.in_(("completed", "ready")),
                DocumentContent.kind == "text",
            )
            .order_by(DocumentVersion.version_number.desc())
        ).first()
        if version_and_content is None:
            parser.error(f"No completed text content for: {args.filename}")
        version, content = version_and_content
        proposals = build_proposals(version.id, content.text)
        missing = missing_proposals(db, proposals)
        print(f"articles: {len(article_ranges(content.text))}")
        print(f"reference pairs: {len(proposals)}")
        print(f"already exist: {len(proposals) - len(missing)}")
        print(f"proposals: {len(missing)}")
        for source, target, _ in missing[:30]:
            print(f"{source} -> {target}")
        if args.apply:
            print(f"inserted: {insert_missing_links(db, proposals)}")


if __name__ == "__main__":
    main()
