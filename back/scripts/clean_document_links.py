"""Remove known noise from approved links to 운전취급규정.hwp."""

from __future__ import annotations

import argparse
import re
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, aliased

from app.config import get_settings
from app.models import Document, DocumentContent, DocumentLink, DocumentVersion
from app.services.document_content import text_ranges, utf16_length, utf16_slice

TARGET_FILENAME = "운전취급규정.hwp"
SOURCE_FILENAME = "6호선 전동차고장조치 길라잡이-1.pptx"
DROP_ARTICLES = {119, 163, 164, 165, 166, 167, 168, 194, 145, 146, 26}
ARTICLE = re.compile(r"^제(\d+)조")
TRAILING_HEADING = re.compile(
    r"(?m)^제\d+(?:장|절)(?:[ \t]+|$)|^제\d+조[ \t]*(?:\(|<삭제\b)"
)


def article_number(part: dict) -> int | None:
    match = ARTICLE.match(part.get("exact", ""))
    return int(match.group(1)) if match else None


def trim_range(part: dict, content: DocumentContent) -> tuple[dict, int]:
    start, end = int(part["start"]), int(part["end"])
    exact = utf16_slice(content.text, start, end)
    if exact != part["exact"]:
        raise ValueError(f"Range at UTF-16 offset {start} does not match document content")

    heading = TRAILING_HEADING.search(exact, 1)
    cleaned = (exact[:heading.start()] if heading else exact).rstrip()
    removed = len(exact) - len(cleaned)
    if not removed:
        return part, 0

    new_end = start + utf16_length(cleaned)
    updated = {**part, "end": new_end, "exact": cleaned}
    if "suffix" in part:
        updated["suffix"] = content.text.encode("utf-16-le")[new_end * 2 :].decode("utf-16-le")[:40]
    return updated, removed


def find_article_35(db: Session, target_version_id: str, excluded_link_id: str) -> dict:
    links = db.scalars(
        select(DocumentLink).where(DocumentLink.target_version_id == target_version_id)
    )
    for candidate in links:
        if candidate.id == excluded_link_id:
            continue
        for part in text_ranges(candidate.target_selection):
            if article_number(part) == 35:
                return dict(part)
    raise ValueError(f"No article 35 range found for target version {target_version_id}")


def clean_links(db: Session) -> tuple[int, int, int, int]:
    source_version = aliased(DocumentVersion)
    target_version = aliased(DocumentVersion)
    source_document = aliased(Document)
    target_document = aliased(Document)
    rows = db.execute(
        select(DocumentLink, source_document.filename)
        .join(source_version, DocumentLink.source_version_id == source_version.id)
        .join(source_document, source_version.document_id == source_document.id)
        .join(target_version, DocumentLink.target_version_id == target_version.id)
        .join(target_document, target_version.document_id == target_document.id)
        .where(
            DocumentLink.status == "approved",
            DocumentLink.relation_type == "REFERENCES",
            target_document.filename == TARGET_FILENAME,
        )
    ).all()

    changed = zero_ranges = trimmed_chars = 0
    for link, source_filename in rows:
        selection = link.target_selection
        content = db.get(DocumentContent, link.target_version_id)
        if content is None or content.kind != "text" or selection.get("kind") != "text":
            raise ValueError(f"Missing text content for link {link.id}")

        old_ranges = text_ranges(selection)
        before = ",".join(str(n) for part in old_ranges if (n := article_number(part)) is not None)
        ranges: list[dict] = []
        trimmed = 0
        for part in old_ranges:
            if article_number(part) in DROP_ARTICLES:
                continue
            cleaned, removed = trim_range(part, content)
            ranges.append(cleaned)
            trimmed += removed

        pages = link.source_selection.get("pages", [])
        add_article_35 = (
            source_filename == SOURCE_FILENAME
            and pages == [35, 36]
            and not any(article_number(part) == 35 for part in ranges)
        )
        if add_article_35:
            ranges.append(find_article_35(db, link.target_version_id, link.id))
        ranges.sort(key=lambda part: part["start"])

        label = f"{source_filename} pages={pages}"
        if not ranges:
            zero_ranges += 1
            print(f"{label} | articles {before} -> {before} (zero-range guard; unchanged) | trimmed chars 0")
            continue

        after = ",".join(str(n) for part in ranges if (n := article_number(part)) is not None)
        new_selection = {"kind": "text", "version_id": link.target_version_id, "ranges": ranges}
        if new_selection != selection:
            link.target_selection = new_selection
            changed += 1
        trimmed_chars += trimmed
        print(f"{label} | articles {before} -> {after} | trimmed chars {trimmed}")

    return len(rows), changed, zero_ranges, trimmed_chars


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Clean approved document link selections")
    parser.add_argument("--db", default=None, help="SQLAlchemy database URL")
    parser.add_argument("--apply", action="store_true", help="Write the cleanup to the database")
    args = parser.parse_args()
    database_url = args.db or get_settings().database_url
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
    )
    try:
        with Session(engine) as db:
            print("Mode: APPLY" if args.apply else "Mode: DRY RUN")
            links, changed, zero_ranges, trimmed_chars = clean_links(db)
            if args.apply:
                db.commit()
            else:
                db.rollback()
            print(
                f"Summary: links={links}, changed={changed}, zero-range={zero_ranges}, "
                f"trimmed_chars={trimmed_chars}"
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
