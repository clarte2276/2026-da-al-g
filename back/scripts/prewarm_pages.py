"""Convert every document to its PDF rendition ahead of time.

The chat client renders evidence pages from that PDF. A large HWP takes minutes to
convert, so run this once after ingestion instead of making the first reader wait::

    uv run --extra hwp python -m scripts.prewarm_pages
"""

from __future__ import annotations

import time

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Document, DocumentVersion
from app.services.document_content import verified_source
from app.services.pdf_conversion import PdfConversionError, PdfConversionService


def main() -> None:
    service = PdfConversionService(get_settings())
    with SessionLocal() as db:
        versions = db.scalars(
            select(DocumentVersion).order_by(DocumentVersion.created_at.desc())
        ).all()
        seen: set[str] = set()
        for version in versions:
            if version.document_id in seen:
                continue
            seen.add(version.document_id)
            document = db.get(Document, version.document_id)
            name = document.filename if document else version.id
            try:
                source = verified_source(version)
            except Exception as exc:  # noqa: BLE001 - a missing original is not fatal here
                print(f"건너뜀 {name}: {exc}")
                continue
            start = time.time()
            try:
                _, converter = service.convert(source, version.sha256)
            except PdfConversionError as exc:
                print(f"실패 {name}: {exc}")
                continue
            print(f"완료 {name} ({converter}, {time.time() - start:.1f}s)")


if __name__ == "__main__":
    main()
