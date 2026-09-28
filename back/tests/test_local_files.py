from pathlib import Path

import pytest

from app.config import Settings
from app.services.local_files import LocalFileService


def test_local_file_service_lists_supported_files_and_blocks_escape(tmp_path) -> None:
    document_dir = tmp_path / "규정"
    document_dir.mkdir()
    hwp_path = document_dir / "운전규정.hwp"
    hwp_path.write_bytes(b"sample")
    (document_dir / "notes.txt").write_text("ignore", encoding="utf-8")

    service = LocalFileService(Settings(local_document_roots=str(tmp_path)))
    files = service.list_files()

    assert len(files) == 1
    assert files[0].relative_path == "규정/운전규정.hwp"
    assert service.resolve("root-0", files[0].relative_path).path == hwp_path.resolve()
    with pytest.raises(ValueError):
        service.resolve("root-0", "../outside.hwp")


def test_local_file_service_manages_folders_and_moves_files_safely(tmp_path) -> None:
    source = tmp_path / "문서군"
    source.mkdir()
    (source / "규정.pdf").write_bytes(b"pdf")
    service = LocalFileService(Settings(_env_file=None, local_document_roots=str(tmp_path)))

    service.create_folder("root-0", "보관")
    assert service.folders("root-0") == ["문서군", "보관"]
    service.move("root-0", "문서군/규정.pdf", "보관/규정.pdf")
    assert service.resolve("root-0", "보관/규정.pdf").path.read_bytes() == b"pdf"
    with pytest.raises(OSError):
        service.delete_empty_folder("root-0", "보관")
    with pytest.raises(ValueError):
        service.move("root-0", "보관", "보관/하위")
    with pytest.raises(ValueError):
        service.create_folder("root-0", "../탈출")
    service.delete_empty_folder("root-0", "문서군")
    service.delete_file("root-0", "보관/규정.pdf")
    service.delete_empty_folder("root-0", "보관")


def test_move_updates_indexed_document_source_without_changing_its_id(tmp_path, monkeypatch) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app import main
    from app.db import Base
    from app.models import Document
    from app.schemas import LocalMoveRequest

    source = tmp_path / "문서군"
    source.mkdir()
    file = source / "규정.pdf"
    file.write_bytes(b"pdf")
    (tmp_path / "이동처").mkdir()
    monkeypatch.setattr(main, "local_file_service", LocalFileService(
        Settings(_env_file=None, local_document_roots=str(tmp_path))))
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        document = Document(filename="규정.pdf", source_path=str(file), sha256="a" * 64)
        db.add(document)
        db.commit()
        original_id = document.id
        main.move_local_entry(LocalMoveRequest(root_id="root-0", source_path="문서군/규정.pdf",
                                               destination_path="이동처/규정.pdf"), db, None)
        db.refresh(document)
        assert document.id == original_id
        assert document.source_path == str(tmp_path / "이동처" / "규정.pdf")
        assert (tmp_path / "이동처" / "규정.pdf").is_file()


def test_document_folder_mirrors_data_pdf_tree(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app import main
    from app.config import Settings

    monkeypatch.setattr(main, "settings", Settings(_env_file=None, storage_root=tmp_path,
                                                   local_document_roots=str(tmp_path)))
    source = tmp_path / "data_raw" / "규정" / "관제업무" / "관제업무내규" / "관제업무내규.hwp"

    assert main._document_folder(SimpleNamespace(source_path=str(source))) == "규정/관제업무/관제업무내규"
    assert main._document_folder(SimpleNamespace(source_path=str(tmp_path / "a.pdf"))) == ""
    assert main._document_folder(SimpleNamespace(source_path="/elsewhere/a.pdf")) is None
    assert main._document_folder(SimpleNamespace(source_path=None)) is None


def test_pdf_twin_prefers_data_pdf_copy(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app import main

    source = tmp_path / "data_raw" / "규정" / "운전취급규정.hwp"
    twin = tmp_path / "data_pdf" / "규정" / "운전취급규정.pdf"
    twin.parent.mkdir(parents=True)
    twin.write_bytes(b"%PDF-1.4")
    version = SimpleNamespace(sha256="abc")

    assert main._pdf_twin(SimpleNamespace(source_path=str(source)), version) == (twin, "abc-pdf")

    monkeypatch.setattr(main, "verified_source", lambda _version: Path("stored.hwp"))
    other = SimpleNamespace(source_path=str(tmp_path / "data_raw" / "없음.hwp"))
    assert main._pdf_twin(other, version) == (Path("stored.hwp"), "abc")
