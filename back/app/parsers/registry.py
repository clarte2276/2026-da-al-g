from pathlib import Path

from .base import DocumentParser, ParserError


def get_parser(path: str | Path) -> DocumentParser:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        from .docx_parser import DocxParser

        return DocxParser()
    if suffix == ".pptx":
        from .pptx_parser import PptxParser

        return PptxParser()
    if suffix == ".pdf":
        from .pdf_parser import PdfParser

        return PdfParser()
    if suffix == ".hwpx":
        from .hwpx_parser import HwpxParser

        return HwpxParser()
    if suffix == ".hwp":
        from .hwp_parser import HwpParser

        return HwpParser()
    raise ParserError(f"Unsupported document format: {suffix or '(no extension)'}")
