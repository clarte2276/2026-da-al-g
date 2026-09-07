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
