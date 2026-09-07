from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import DocumentParser, ParsedDocument, ParsedFragment, clean_text


def _value(value: Any) -> str:
    if value is None:
        return ""
    for attr in ("text", "value", "content"):
        if hasattr(value, attr):
            candidate = getattr(value, attr)
            if not callable(candidate):
                return clean_text(candidate)
    return clean_text(value)


class HwpxParser(DocumentParser):
    name = "python-hwpx"
    version = "6.x"

    def parse(self, path: Path) -> ParsedDocument:
        try:
            from hwpx import HwpxDocument
        except ImportError as exc:
            raise RuntimeError("python-hwpx is required for .hwpx files") from exc

        document = HwpxDocument.open(str(path))
        fragments: list[ParsedFragment] = []
        ordinal = 0

        try:
            markdown_method = getattr(getattr(document, "text", None), "markdown", None)
            markdown = clean_text(
                markdown_method() if callable(markdown_method) else document.export_markdown()
            )
        except Exception:  # noqa: BLE001 - use the library's plain-text fallback
            plain_method = getattr(getattr(document, "text", None), "plain", None)
            markdown = clean_text(plain_method() if callable(plain_method) else document.export_text())
        if markdown:
            fragments.append(
                ParsedFragment(
                    stable_key="document",
                    kind="document",
                    ordinal=ordinal,
                    text=markdown,
                    html=None,
                    locator={"document": True},
                    metadata={"representation": "markdown"},
                )
            )
            ordinal += 1

        for paragraph_index, paragraph in enumerate(getattr(document, "paragraphs", [])):
            text = _value(paragraph)
            if not text:
                continue
            fragments.append(
                ParsedFragment(
                    stable_key=f"paragraph:{paragraph_index}",
                    kind="paragraph",
                    ordinal=ordinal,
                    text=text,
                    locator={"paragraph": paragraph_index},
                    parent_key="document",
                )
            )
            ordinal += 1

        for table_index, table in enumerate(getattr(document, "tables", [])):
            rows: list[list[str]] = []
            for row in getattr(table, "rows", []) or []:
                cells = getattr(row, "cells", row if isinstance(row, (list, tuple)) else [])
                rows.append([_value(cell) for cell in cells])
            table_text = "\n".join(" | ".join(row) for row in rows if any(row))
            if not table_text:
                continue
            fragments.append(
                ParsedFragment(
                    stable_key=f"table:{table_index}",
                    kind="table",
                    ordinal=ordinal,
                    text=table_text,
                    table_json=rows,
                    locator={"table": table_index},
                    parent_key="document",
                )
            )
            ordinal += 1

        return ParsedDocument(
            parser_name=self.name,
            parser_version=self.version,
            fragments=fragments,
            plain_text=document.text.plain(),
            metadata={
                "paragraph_count": len(getattr(document, "paragraphs", [])),
                "table_count": len(getattr(document, "tables", [])),
            },
        )
