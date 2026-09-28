"""Ingest every supported original under the document roots' data_raw folders.

Same steps as POST /api/local/open, one file at a time. Files already ingested (same
sha256) are skipped by the ingestion service, so the script can be re-run safely::

    uv run --extra hwp python -m scripts.ingest_all --dry-run
    uv run --extra hwp python -m scripts.ingest_all
"""

from __future__ import annotations

import mimetypes
import sys
import time

from app.main import ingestion_service, settings
from app.db import SessionLocal

SUFFIXES = {".hwp", ".hwpx", ".docx", ".pptx", ".pdf"}


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    files = sorted(
        path
        for root in settings.document_roots()
        for path in (root / "data_raw").rglob("*")
        if path.is_file() and path.suffix.lower() in SUFFIXES
    )
    print(f"대상 {len(files)}개", flush=True)
    if dry_run:
        for path in files:
            print(path)
        return

    done = failed = 0
    for index, path in enumerate(files, start=1):
        start = time.time()
        with SessionLocal() as db:
            try:
                mime = mimetypes.guess_type(path.name)[0]
                document, _ = ingestion_service.ingest_new_file(db, path, path.name, mime)
                document.source_path = str(path)
                document.filename = path.name
                document.mime_type = mime
                db.commit()
                done += 1
                print(f"[{index}/{len(files)}] 완료 {path.name} ({time.time() - start:.1f}s)", flush=True)
            except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
                db.rollback()
                failed += 1
                print(f"[{index}/{len(files)}] 실패 {path.name}: {exc}", flush=True)
    print(f"끝: 완료 {done}, 실패 {failed}", flush=True)


if __name__ == "__main__":
    main()
