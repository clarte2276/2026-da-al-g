from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import time
from pathlib import Path
from types import ModuleType

import pytest

from app.config import Settings
from app.services.pdf_conversion import PdfConversionService

DATA_RAW = Path(r"D:\Codes\Dongguk_University\2026-da-al-g\data\data_raw")


def test_real_hwp_uses_rhwp_and_caches_pdf(tmp_path: Path) -> None:
    source = next(DATA_RAW.rglob("*.hwp"), None) if DATA_RAW.is_dir() else None
    if source is None:
        pytest.skip("No HWP samples found in the configured data_raw directory")

    service = PdfConversionService(Settings(storage_root=tmp_path / "storage"))
    output, converter = service.convert(source, "rhwp-test")

    assert converter == "rhwp"
    assert output.read_bytes().startswith(b"%PDF")
    assert service.convert(source, "rhwp-test")[1] == "cached-rhwp"
    assert service.page_count(source, "rhwp-test") >= 1


def test_rhwp_render_uses_its_own_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "sample.hwpx"
    source.touch()
    rhwp = ModuleType("rhwp")

    class Document:
        def render_pdf(self) -> bytes:
            return b"%PDF-1.7\nrendered"

    monkeypatch.setattr(rhwp, "parse", lambda _: Document(), raising=False)
    monkeypatch.setitem(sys.modules, "rhwp", rhwp)
    service = PdfConversionService(Settings(storage_root=tmp_path / "storage"))

    output, converter = service.convert(source, "rhwp-cache-test")

    assert converter == "rhwp"
    assert output.name.startswith("rhwp-v1-")
    assert output.read_bytes().startswith(b"%PDF")
    assert service.convert(source, "rhwp-cache-test")[1] == "cached-rhwp"


def test_rhwp_failure_falls_back_to_libreoffice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "sample.hwp"
    source.touch()
    rhwp = ModuleType("rhwp")

    def fail_parse(_: str) -> None:
        raise RuntimeError("render failed")

    monkeypatch.setattr(rhwp, "parse", fail_parse, raising=False)
    monkeypatch.setitem(sys.modules, "rhwp", rhwp)

    service = PdfConversionService(Settings(storage_root=tmp_path / "storage"))
    converter = tmp_path / "soffice"
    service._find_converter = lambda: converter  # type: ignore[method-assign]
    attempted: list[Path] = []

    def fake_convert(source_path: Path, output: Path, converter_path: Path) -> None:
        attempted.append(source_path)
        assert converter_path == converter
        output.write_bytes(b"%PDF-1.7\n")

    service._convert_with_libreoffice = fake_convert  # type: ignore[method-assign]

    output, used_converter = service.convert(source, "fallback-test")

    assert used_converter == "libreoffice"
    assert attempted == [source]
    assert output.read_bytes().startswith(b"%PDF")


def test_libreoffice_conversions_are_serialized_and_reuse_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "sample.docx"
    source.touch()
    service = PdfConversionService(Settings(storage_root=tmp_path / "storage"))
    converter = tmp_path / "soffice"
    start = threading.Barrier(2)
    counters = {"active": 0, "maximum": 0, "calls": 0}
    counters_lock = threading.Lock()

    def find_converter() -> Path:
        start.wait(timeout=5)
        return converter

    def fake_convert(source_path: Path, output: Path, converter_path: Path) -> None:
        assert source_path == source
        assert converter_path == converter
        with counters_lock:
            counters["calls"] += 1
            counters["active"] += 1
            counters["maximum"] = max(counters["maximum"], counters["active"])
        time.sleep(0.1)
        output.write_bytes(b"%PDF-1.7\n")
        with counters_lock:
            counters["active"] -= 1

    monkeypatch.setattr(service, "_find_converter", find_converter)
    monkeypatch.setattr(service, "_convert_with_libreoffice", fake_convert)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: service.convert(source, "same-docx"), range(2)))

    assert counters["maximum"] == 1
    assert counters["calls"] == 1
    assert {converter for _, converter in results} == {"libreoffice", "cached-libreoffice"}
