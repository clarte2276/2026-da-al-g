import hashlib
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import DocumentContent, DocumentVersion, Fragment
from ..parsers import ParsedDocument, ParserError, get_parser


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def utf16_slice(text: str, start: int, end: int) -> str:
    encoded = text.encode("utf-16-le")
    if not 0 <= start < end <= len(encoded) // 2:
        raise ValueError("선택 범위가 본문을 벗어났습니다.")
    try:
        return encoded[start * 2:end * 2].decode("utf-16-le")
    except UnicodeDecodeError as exc:
        raise ValueError("선택 범위가 문자 중간에서 끝납니다.") from exc


def verified_source(version: DocumentVersion) -> Path:
    path = Path(version.storage_path)
    if not path.is_file():
        raise HTTPException(404, "보존된 원본 파일이 없습니다.")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != version.sha256:
        raise HTTPException(409, "원본 파일이 변경되었습니다. 새 문서 버전으로 열어 주세요.")
    return path


def build_content(version: DocumentVersion, parsed: ParsedDocument) -> DocumentContent:
    suffix = Path(version.storage_path).suffix.lower()
    if suffix in {".pdf", ".pptx"}:
        key = "page" if suffix == ".pdf" else "slide"
        regions = {int(f.locator[key]): f for f in parsed.fragments
                   if f.kind == key and key in f.locator}
        count = parsed.metadata.get(f"{key}_count") or max(regions, default=0)
        return DocumentContent(
            version_id=version.id, kind="pages", text="",
            pages=[{"number": number, "text": regions[number].text or ""
                    if number in regions else ""} for number in range(1, count + 1)],
        )
    text = parsed.plain_text
    if text is None:
        whole = next((f for f in parsed.fragments if f.kind == "document" and f.text), None)
        text = whole.text if whole else "\n\n".join(
            f.text for f in parsed.fragments if f.text
        )
    return DocumentContent(version_id=version.id, kind="text", text=text or "", pages=[])


def ensure_content(db: Session, version: DocumentVersion) -> DocumentContent:
    content = db.get(DocumentContent, version.id)
    if content is None:
        path = verified_source(version)
        try:
            content = build_content(version, get_parser(path).parse(path))
        except (ParserError, ValueError, RuntimeError) as exc:
            raise HTTPException(422, f"문서 내용을 준비하지 못했습니다: {exc}") from exc
        db.add(content)
        db.flush()
    return content


def validate_selection(db: Session, selection: dict) -> dict:
    version = db.get(DocumentVersion, selection["version_id"])
    if not version or version.status not in {"completed", "ready"}:
        raise HTTPException(404, "사용할 수 있는 문서 버전이 없습니다.")
    verified_source(version)
    content = ensure_content(db, version)
    if content.kind != selection["kind"]:
        raise HTTPException(422, "문서 형식과 선택 방식이 일치하지 않습니다.")
    if content.kind == "text":
        encoded = content.text.encode("utf-16-le")
        ranges: list[dict] = []
        for part in sorted(text_ranges(selection), key=lambda r: (r["start"], r["end"])):
            try:
                exact = utf16_slice(content.text, part["start"], part["end"])
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
            if not exact.strip() or exact != part["exact"]:
                raise HTTPException(422, "선택한 인용문이 본문과 일치하지 않습니다. 다시 선택해 주세요.")
            if ranges and part["start"] < ranges[-1]["end"]:
                raise HTTPException(422, "선택한 구절이 서로 겹칩니다. 하나로 합쳐 주세요.")
            before = encoded[:part["start"] * 2].decode("utf-16-le")
            after = encoded[part["end"] * 2:].decode("utf-16-le")
            ranges.append({"start": part["start"], "end": part["end"], "exact": exact,
                           "prefix": before[-40:], "suffix": after[:40]})
        return {"kind": "text", "version_id": version.id, "ranges": ranges}
    pages = sorted(set(selection["pages"]))
    if not pages or pages[0] < 1 or pages[-1] > len(content.pages):
        raise HTTPException(422, "존재하는 페이지를 선택해 주세요.")
    return {"kind": "pages", "version_id": version.id, "pages": pages}


def text_ranges(selection: dict) -> list[dict]:
    """A text selection holds several ranges; links saved earlier stored one inline."""
    return selection.get("ranges") or [selection]


def selection_text(content: DocumentContent, selection: dict) -> str:
    if selection["kind"] == "text":
        return "\n\n".join(part["exact"] for part in text_ranges(selection))
    return "\n\n".join(content.pages[n - 1]["text"] for n in selection["pages"])


def overlaps(fragment: Fragment, selection: dict, content: DocumentContent) -> bool:
    if fragment.version_id != selection["version_id"]:
        return False
    if selection["kind"] == "pages":
        return fragment.locator_json.get("page", fragment.locator_json.get("slide")) in selection["pages"]
    metadata = fragment.metadata_json or {}
    start, end = metadata.get("text_start"), metadata.get("text_end")
    if start is None or end is None:
        # Legacy chunks have no canonical offsets. Only an unambiguous exact match is safe.
        text = fragment.text or ""
        index = content.text.find(text) if text else -1
        if index < 0 or content.text.find(text, index + 1) >= 0:
            return False
        start = utf16_length(content.text[:index])
        end = start + utf16_length(text)
    return any(start < part["end"] and end > part["start"] for part in text_ranges(selection))
