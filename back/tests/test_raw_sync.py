from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import Mock

from docx import Document as WordDocument
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import Base
from app.models import Document, DocumentVersion
from app.services.embedding import HashEmbeddingProvider
from app.services.ingestion import IngestionService
from app.services.raw_sync import RawSync


def _write_docx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = WordDocument()
    document.add_paragraph(text)
    document.save(path)


def _age(path: Path, seconds: int = 20) -> None:
    past = time.time() - seconds
    os.utime(path, (past, past))


def _sync(tmp_path: Path, *, document_root: Path | None = None):
    raw_root = tmp_path / "data_raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    settings = Settings(
        _env_file=None,
        storage_root=tmp_path / "store",
        local_document_roots=str(document_root or raw_root),
        embedding_dimensions=64,
        raw_sync_interval_seconds=0,
    )
    ingestion = IngestionService(settings, HashEmbeddingProvider(64))
    pdf = Mock()
    pdf.convert.side_effect = lambda source, key: (source, "stub")
    sync = RawSync(settings, ingestion, pdf, sessions)
    return sync, sessions, pdf, engine, raw_root


def test_new_file_is_ingested_once(tmp_path: Path) -> None:
    sync, sessions, pdf, engine, raw_root = _sync(tmp_path)
    path = raw_root / "sample.docx"
    _write_docx(path, "First version")
    _age(path)

    sync.run_once()
    sync.run_once()

    with sessions() as db:
        assert db.scalar(select(func.count(Document.id))) == 1
        assert db.scalar(select(func.count(DocumentVersion.id))) == 1
    assert pdf.convert.call_count == 1
    engine.dispose()


def test_modified_file_becomes_a_version_of_the_same_document(tmp_path: Path) -> None:
    sync, sessions, _pdf, engine, raw_root = _sync(tmp_path)
    path = raw_root / "sample.docx"
    _write_docx(path, "First version")
    _age(path)
    sync.run_once()

    _write_docx(path, "Second version with changed content")
    sync.run_once()  # The changed stat is observed and deferred.
    sync.run_once()  # The stable changed file becomes the next version.

    with sessions() as db:
        documents = db.scalars(select(Document)).all()
        versions = db.scalars(
            select(DocumentVersion).order_by(DocumentVersion.version_number)
        ).all()
        assert len(documents) == 1
        assert [version.version_number for version in versions] == [1, 2]
        assert all(version.document_id == documents[0].id for version in versions)
        assert documents[0].sha256 == versions[-1].sha256
    engine.dispose()


def test_file_changed_between_passes_is_deferred_until_stable(tmp_path: Path) -> None:
    sync, sessions, _pdf, engine, raw_root = _sync(tmp_path)
    path = raw_root / "copying.docx"
    _write_docx(path, "Initial contents")

    sync.run_once()  # A just-created file is too young.
    _write_docx(path, "Contents changed while being copied")
    sync.run_once()  # The changed size/mtime is deferred.
    with sessions() as db:
        assert db.scalar(select(func.count(Document.id))) == 0

    sync.run_once()
    with sessions() as db:
        assert db.scalar(select(func.count(Document.id))) == 1
    engine.dispose()


def test_pdf_prewarm_uses_data_pdf_twin(tmp_path: Path) -> None:
    sync, _sessions, pdf, engine, raw_root = _sync(tmp_path)
    path = raw_root / "rules" / "sample.docx"
    _write_docx(path, "Twin conversion")
    _age(path)
    twin = tmp_path / "data_pdf" / "rules" / "sample.pdf"
    twin.parent.mkdir(parents=True)
    twin.write_bytes(b"%PDF-1.4")

    sync.run_once()

    assert pdf.convert.call_args.args[0] == twin
    assert pdf.convert.call_args.args[1].endswith("-pdf")
    engine.dispose()


def test_failed_file_does_not_stop_pass_or_retry_unchanged_file(tmp_path: Path) -> None:
    sync, sessions, pdf, engine, raw_root = _sync(tmp_path)
    failed_path = raw_root / "a-fails.docx"
    good_path = raw_root / "b-works.docx"
    _write_docx(failed_path, "Fail conversion")
    _write_docx(good_path, "Continue conversion")
    _age(failed_path)
    _age(good_path)

    def convert(source: Path, key: str):
        if source.name == failed_path.name:
            raise RuntimeError("conversion failed")
        return source, key

    pdf.convert.side_effect = convert
    sync.run_once()
    sync.run_once()

    with sessions() as db:
        assert db.scalar(select(func.count(Document.id))) == 2
    assert [call.args[0].name for call in pdf.convert.call_args_list].count(failed_path.name) == 1
    engine.dispose()


def test_scanner_accepts_data_raw_root_and_its_parent(tmp_path: Path) -> None:
    sync, _sessions, _pdf, engine, raw_root = _sync(tmp_path)
    path = raw_root / "sample.docx"
    _write_docx(path, "Root scan")
    assert sync.files() == [path.resolve()]

    sync.settings.local_document_roots = str(tmp_path)
    assert sync.files() == [path.resolve()]
    engine.dispose()
