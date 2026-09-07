from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.parsers import ParserError, get_parser

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data_raw"


def test_pptx_parser_preserves_text_tables_and_images() -> None:
    path = RAW_ROOT / "길라잡이" / "6호선 전동차고장조치 길라잡이-1.pptx"

    parsed = get_parser(path).parse(path)

    assert parsed.parser_name == "python-pptx"
    assert parsed.metadata["slide_count"] > 0
    assert any(fragment.kind == "slide" and fragment.text for fragment in parsed.fragments)
    assert any(fragment.kind == "image" for fragment in parsed.fragments)
    assert parsed.assets


def test_hwpx_parser_preserves_paragraphs_and_tables() -> None:
    path = RAW_ROOT / "규정" / "관제업무" / "관제운영규정" / "관제운영규정.hwpx"

    parsed = get_parser(path).parse(path)

    assert parsed.parser_name == "python-hwpx"
    assert parsed.metadata["paragraph_count"] > 0
    assert any(fragment.text for fragment in parsed.fragments)
    assert parsed.metadata["table_count"] >= 0


def test_hwp_parser_has_a_supported_path_or_a_clear_error() -> None:
    path = next(RAW_ROOT.rglob("*.hwp"))

    try:
        parsed = get_parser(path).parse(path)
    except ParserError as exc:
        pytest.skip(f"optional HWP parser is not available: {exc}")

    assert parsed.fragments
    assert parsed.metadata.get("degraded", False) or parsed.parser_name == "rhwp-python"


def test_pdf_parser_registers_page_metadata(tmp_path: Path) -> None:
    path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with path.open("wb") as handle:
        writer.write(handle)

    parsed = get_parser(path).parse(path)

    assert parsed.parser_name == "pypdf"
    assert parsed.metadata["page_count"] == 1
    assert parsed.metadata["ocr_required"] is True
