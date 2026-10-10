"""Convert every latest document version to its display PDF ahead of time."""

from __future__ import annotations

import time

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Document, DocumentVersion
from app.services.document_content import pdf_twin
from app.services.pdf_conversion import PdfConversionService


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
            if not document:
                print(f"Missing document for version {version.id}")
                continue
            start = time.time()
            try:
                source, cache_key = pdf_twin(document, version)
                _, converter = service.convert(source, cache_key)
            except Exception as exc:  # noqa: BLE001 - one bad document must not stop the batch
                print(f"Failed {document.filename}: {exc}")
                continue
            print(f"Ready {document.filename} ({converter}, {time.time() - start:.1f}s)")


if __name__ == "__main__":
    main()
