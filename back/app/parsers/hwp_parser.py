from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import DocumentParser, ParsedDocument, ParsedFragment, ParserError, clean_text, get_attr


def _provenance(block: Any) -> dict[str, Any]:
    provenance = get_attr(block, "prov", "provenance", default=None)
    result: dict[str, Any] = {}
    for key, names in {
        "section": ("section_idx", "section", "section_index"),
        "paragraph": ("para_idx", "paragraph", "paragraph_index"),
        "page": ("page", "page_idx", "page_index"),
    }.items():
        value = get_attr(provenance, *names, default=None)
        if value is not None:
            result[key] = value
    return result


def _block_text(block: Any) -> str:
    for name in ("text", "plain_text", "content", "value"):
        value = get_attr(block, name, default=None)
        if value is not None and not callable(value):
            text = clean_text(value)
            if text:
                return text
    for name in ("to_text", "extract_text"):
        method = get_attr(block, name, default=None)
        if callable(method):
            try:
                text = clean_text(method())
                if text:
                    return text
            except (AttributeError, RuntimeError, TypeError, ValueError):
                continue
    return ""


class HwpParser(DocumentParser):
    name = "rhwp-python"
    version = "0.8.x"

    def parse(self, path: Path) -> ParsedDocument:
        try:
            import rhwp
        except Exception as exc:
            fallback = self._fallback_hwp5txt(path)
            if fallback is not None:
                return fallback
            raise ParserError(
                "rhwp-python could not be loaded; install the HWP extra or use a compatible runtime: "
                f"{exc}"
            ) from exc

        try:
            document = rhwp.parse(str(path))
            ir = document.to_ir()
            fragments: list[ParsedFragment] = []
            for ordinal, block in enumerate(ir.iter_blocks(scope="body")):
                text = _block_text(block)
                class_name = type(block).__name__.lower()
                if "table" in class_name:
                    kind = "table"
                elif "picture" in class_name or "image" in class_name:
                    kind = "image"
                elif "equation" in class_name or "formula" in class_name:
                    kind = "equation"
                else:
                    kind = "paragraph"
                if not text and kind == "paragraph":
                    continue
                table_json = None
                html = None
                if kind == "table":
                    html = clean_text(get_attr(block, "html", default=None)) or None
                    rows = get_attr(block, "rows", default=None)
                    cols = get_attr(block, "cols", "columns", default=None)
                    table_json = {"rows": rows, "columns": cols, "text": text}
                fragments.append(
                    ParsedFragment(
                        stable_key=f"block:{ordinal}",
                        kind=kind,
                        ordinal=ordinal,
                        text=text or None,
                        html=html,
                        table_json=table_json,
                        locator=_provenance(block),
                    )
                )

            if not fragments:
                text = clean_text(document.extract_text())
                if text:
                    fragments.append(
                        ParsedFragment(
                            stable_key="document",
                            kind="document",
                            ordinal=0,
                            text=text,
                            locator={"document": True},
                        )
                    )
            return ParsedDocument(
                parser_name=self.name,
                parser_version=self.version,
                fragments=fragments,
                metadata={
                    "section_count": getattr(document, "section_count", None),
                    "paragraph_count": getattr(document, "paragraph_count", None),
                    "page_count": getattr(document, "page_count", None),
                },
            )
        except Exception as exc:
            fallback = self._fallback_hwp5txt(path)
            if fallback is not None:
                fallback.metadata["degraded"] = True
                fallback.metadata["degraded_reason"] = str(exc)
                return fallback
            raise ParserError(f"HWP parsing failed: {exc}") from exc

    def _fallback_hwp5txt(self, path: Path) -> ParsedDocument | None:
        try:
            result = subprocess.run(
                ["hwp5txt", str(path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
        text = clean_text(result.stdout)
        if not text:
            return None
        return ParsedDocument(
            parser_name="pyhwp-hwp5txt-fallback",
            parser_version="0.1b15",
            fragments=[
                ParsedFragment(
                    stable_key="document",
                    kind="document",
                    ordinal=0,
                    text=text,
                    locator={"document": True},
                )
            ],
            metadata={"degraded": True, "degraded_reason": "structured HWP parser unavailable"},
        )
