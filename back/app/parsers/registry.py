from pathlib import Path

from .base import DocumentParser, ParserError
from .docx_parser import DocxParser
from .hwp_parser import HwpParser
from .hwpx_parser import HwpxParser
from .pdf_parser import PdfParser
from .pptx_parser import PptxParser


def get_parser(path: str | Path) -> DocumentParser:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return DocxParser()
    if suffix == ".pptx":
        return PptxParser()
    if suffix == ".pdf":
        return PdfParser()
    if suffix == ".hwpx":
        return HwpxParser()
    if suffix == ".hwp":
        return HwpParser()
    raise ParserError(f"Unsupported document format: {suffix or '(no extension)'}")
