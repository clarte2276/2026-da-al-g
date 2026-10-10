from __future__ import annotations

import hashlib
import logging
import mimetypes
import threading
import time
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Document, DocumentVersion
from .document_content import pdf_twin
from .ingestion import IngestionService
from .pdf_conversion import PdfConversionService

logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = {".hwp", ".hwpx", ".docx", ".pptx", ".pdf"}
_SETTLE_SECONDS = 10


class RawSync:
    def __init__(
        self,
        settings: Settings,
        ingestion_service: IngestionService,
        pdf_conversion_service: PdfConversionService,
        session_factory: Callable[[], Session],
    ) -> None:
        self.settings = settings
        self.ingestion_service = ingestion_service
        self.pdf_conversion_service = pdf_conversion_service
        self.session_factory = session_factory
        self._observed: dict[Path, tuple[int, int]] = {}
        self._failed: dict[Path, tuple[int, int]] = {}
        self._pass_lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def files(self) -> list[Path]:
        paths: set[Path] = set()
        for root in self.settings.document_roots():
            raw_root = root if root.name.lower() == "data_raw" else root / "data_raw"
            if not raw_root.is_dir():
                continue
            paths.update(
                path.resolve()
                for path in raw_root.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
            )
        return sorted(paths)

    def start(self) -> None:
        if self.settings.raw_sync_interval_seconds <= 0:
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="raw-sync", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while True:
            self.run_once()
            time.sleep(self.settings.raw_sync_interval_seconds)

    def run_once(self) -> None:
        if not self._pass_lock.acquire(blocking=False):
            return
        try:
            self._run_once()
        finally:
            self._pass_lock.release()

    def _run_once(self) -> None:
        try:
            files = self.files()
        except OSError:
            logger.exception("Could not scan configured data_raw folders")
            return
        logger.info("raw_sync found %d supported files", len(files))
        with self.session_factory() as db:
            documents = db.scalars(select(Document).where(Document.source_path.is_not(None))).all()
            by_path = {_path_key(document.source_path): document for document in documents}

        now_ns = time.time_ns()
        for path in files:
            try:
                stat = path.stat()
                fingerprint = (stat.st_size, stat.st_mtime_ns)
            except OSError:
                logger.exception("Could not stat raw document %s", path)
                continue

            previous = self._observed.get(path)
            self._observed[path] = fingerprint
            if self._failed.get(path) == fingerprint:
                continue
            if previous is not None and previous != fingerprint:
                continue
            if previous is None and now_ns - stat.st_mtime_ns < _SETTLE_SECONDS * 1_000_000_000:
                continue
            if stat.st_size > self.settings.max_upload_bytes:
                self._failed[path] = fingerprint
                logger.error("raw_sync skipped oversized document %s (%d bytes)", path, stat.st_size)
                continue

            try:
                result = self._ingest_if_changed(db_path=path, fingerprint=fingerprint, by_path=by_path)
                if result:
                    document, version = result
                    try:
                        source, cache_key = pdf_twin(document, version)
                        self.pdf_conversion_service.convert(source, cache_key)
                    except Exception:
                        self._clear_fingerprint(version.id)
                        raise
                    logger.info("raw_sync processed %s as %s v%s", path, document.id, version.version_number)
            except Exception:
                self._failed[path] = fingerprint
                logger.exception("raw_sync failed for %s", path)

    def _ingest_if_changed(
        self,
        *,
        db_path: Path,
        fingerprint: tuple[int, int],
        by_path: dict[Path, Document],
    ) -> tuple[Document, DocumentVersion] | None:
        mime_type = mimetypes.guess_type(db_path.name)[0]
        with self.session_factory() as db:
            indexed = by_path.get(db_path)
            document = db.get(Document, indexed.id) if indexed else None
            version = _latest_version(db, document) if document else None
            if document and version and _saved_fingerprint(version) == fingerprint:
                return None

            digest = _sha256_file(db_path)
            if document:
                document.source_path = str(db_path)
                document.filename = db_path.name
                document.mime_type = mime_type
                if version and document.sha256 == digest:
                    needs_prewarm = _saved_fingerprint(version) is None
                    _save_fingerprint(version, fingerprint)
                    db.commit()
                    return (document, version) if needs_prewarm else None
                document.sha256 = digest
                version = self.ingestion_service.ingest_existing_document(db, document.id)
            else:
                document, version = self.ingestion_service.ingest_new_file(
                    db, db_path, db_path.name, mime_type
                )
                document.source_path = str(db_path)
                document.filename = db_path.name
                document.mime_type = mime_type

            _save_fingerprint(version, fingerprint)
            db.commit()
            by_path[db_path] = document
            return document, version

    def _clear_fingerprint(self, version_id: str) -> None:
        with self.session_factory() as db:
            version = db.get(DocumentVersion, version_id)
            if version:
                version.metadata_json = {
                    key: value for key, value in (version.metadata_json or {}).items()
                    if key != "raw_sync"
                }
                db.commit()


def _path_key(path: str | None) -> Path:
    return Path(path or "").resolve()


def _latest_version(db: Session, document: Document) -> DocumentVersion | None:
    return db.scalar(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    )


def _saved_fingerprint(version: DocumentVersion) -> tuple[int, int] | None:
    marker = (version.metadata_json or {}).get("raw_sync")
    if not isinstance(marker, dict):
        return None
    try:
        return int(marker["size"]), int(marker["mtime_ns"])
    except (KeyError, TypeError, ValueError):
        return None


def _save_fingerprint(version: DocumentVersion, fingerprint: tuple[int, int]) -> None:
    version.metadata_json = {
        **(version.metadata_json or {}),
        "raw_sync": {"size": fingerprint[0], "mtime_ns": fingerprint[1]},
    }


def _sha256_file(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()
