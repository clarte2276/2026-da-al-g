"""Run one raw_sync pass, or list supported originals with --dry-run::

    uv run --extra hwp python -m scripts.ingest_all --dry-run
    uv run --extra hwp python -m scripts.ingest_all
"""

from __future__ import annotations

import logging
import sys

from app.main import raw_sync_service


def main() -> None:
    if "--dry-run" in sys.argv:
        files = raw_sync_service.files()
        print(f"Found {len(files)} supported files")
        for path in files:
            print(path)
        return
    logging.basicConfig(level=logging.INFO)
    raw_sync_service.run_once()


if __name__ == "__main__":
    main()
