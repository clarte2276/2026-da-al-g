from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class ParserError(RuntimeError):
    """Raised when a document cannot be parsed safely."""


@dataclass(slots=True)
class ParsedAsset:
    key: str
    data: bytes
    extension: str
    media_type: str | None = None


@dataclass(slots=True)
class ParsedFragment:
    stable_key: str
    kind: str
    ordinal: int
    text: str | None = None
    title: str | None = None
    html: str | None = None
    table_json: list[dict[str, Any]] | dict[str, Any] | None = None
    locator: dict[str, Any] = field(default_factory=dict)
    bbox: dict[str, Any] | None = None
    parent_key: str | None = None
    asset_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    parser_name: str
    parser_version: str
    fragments: list[ParsedFragment]
    assets: list[ParsedAsset] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    plain_text: str | None = None


class DocumentParser(Protocol):
    name: str
    version: str

    def parse(self, path: Path) -> ParsedDocument: ...


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def get_attr(value: Any, *names: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default
