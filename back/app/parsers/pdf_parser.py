from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from .base import DocumentParser, ParsedDocument, ParsedFragment, clean_text


class PdfParser(DocumentParser):
    """Extract one logical source region per PDF page for indexing and anchoring."""

    name = "pypdf"
    version = "5.x"

    def parse(self, path: Path) -> ParsedDocument:
        reader = PdfReader(str(path))
        fragments: list[ParsedFragment] = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = clean_text(page.extract_text() or "")
            if not text:
                # A scanned/image-only page is still represented in parser metadata, but
                # is not indexed as a text fragment until OCR is configured.
                continue
            fragments.append(
                ParsedFragment(
                    stable_key=f"page:{page_number}",
                    kind="page",
                    ordinal=page_number - 1,
                    title=f"페이지 {page_number}",
                    text=text,
                    locator={"page": page_number},
                    metadata={"page": page_number},
                )
            )

        return ParsedDocument(
            parser_name=self.name,
            parser_version=self.version,
            fragments=fragments,
            metadata={
                "page_count": len(reader.pages),
                "text_page_count": len(fragments),
                "ocr_required": len(fragments) < len(reader.pages),
            },
        )
