from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Document, DocumentContent, DocumentVersion, Fragment, IngestionJob
from ..parsers import ParsedDocument, ParsedFragment, get_parser
from .document_content import build_content, utf16_length
from .embedding import EmbeddingProvider


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_asset_name(key: str, extension: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", key).strip("._") or "asset"
    return f"{stem}.{extension.lstrip('.') or 'bin'}"


def _fragment_content(fragment: ParsedFragment) -> str:
    parts = [fragment.title or "", fragment.text or "", fragment.html or ""]
    if fragment.table_json:
        parts.append(json.dumps(fragment.table_json, ensure_ascii=False, sort_keys=True))
    return "\n".join(part for part in parts if part).strip()


def _chunks(fragment: ParsedFragment, max_chars: int = 1800, overlap: int = 220) -> list[ParsedFragment]:
    text = fragment.text or ""
    if len(text) <= max_chars:
        return [fragment]
    results: list[ParsedFragment] = []
    start = 0
    chunk_number = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            boundary = text.rfind("\n", start + max_chars // 2, end)
            if boundary > start:
                end = boundary
        child = ParsedFragment(
            stable_key=f"{fragment.stable_key}:chunk:{chunk_number}",
            kind=fragment.kind,
            ordinal=fragment.ordinal * 1000 + chunk_number,
            text=text[start:end],
            title=fragment.title,
            html=fragment.html if chunk_number == 0 else None,
            table_json=fragment.table_json if chunk_number == 0 else None,
            locator={**fragment.locator, "chunk": chunk_number},
            bbox=fragment.bbox,
            parent_key=fragment.parent_key,
            asset_key=fragment.asset_key if chunk_number == 0 else None,
            metadata={**fragment.metadata, "chunk_start": start, "chunk_end": end,
                      **({"text_start": utf16_length(text[:start]),
                          "text_end": utf16_length(text[:end])}
                         if fragment.stable_key == "canonical" else {})},
        )
        results.append(child)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        chunk_number += 1
    return results


class IngestionService:
    def __init__(self, settings: Settings, embedding_provider: EmbeddingProvider) -> None:
        self.settings = settings
        self.embedding_provider = embedding_provider

    def ingest_existing_document(self, db: Session, document_id: str) -> DocumentVersion:
        document = db.get(Document, document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        path = Path(document.source_path or "")
        if not path.exists():
            raise FileNotFoundError(path)
        version_number = int(
            db.scalar(
                select(DocumentVersion.version_number)
                .where(DocumentVersion.document_id == document.id)
                .order_by(DocumentVersion.version_number.desc())
                .limit(1)
            )
            or 0
        ) + 1
        version = DocumentVersion(
            document_id=document.id,
            version_number=version_number,
            sha256=document.sha256,
            storage_path=str(path),
            status="pending",
        )
        db.add(version)
        db.flush()
        return self._run(db, document, version, path)

    def ingest_new_file(
        self,
        db: Session,
        path: Path,
        filename: str,
        mime_type: str | None = None,
    ) -> tuple[Document, DocumentVersion]:
        sha256 = _sha256_file(path)
        existing = db.scalar(select(Document).where(Document.sha256 == sha256))
        if existing:
            version = db.scalar(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == existing.id)
                .order_by(DocumentVersion.version_number.desc())
                .limit(1)
            )
            if version:
                return existing, version

        document = Document(
            filename=filename,
            mime_type=mime_type or mimetypes.guess_type(filename)[0],
            source_path=str(path),
            sha256=sha256,
            status="ingesting",
        )
        db.add(document)
        db.flush()
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            sha256=sha256,
            storage_path=str(path),
            status="pending",
        )
        db.add(version)
        db.flush()
        self._run(db, document, version, path)
        return document, version

    def _run(
        self,
        db: Session,
        document: Document,
        version: DocumentVersion,
        path: Path,
    ) -> DocumentVersion:
        job = IngestionJob(document_version_id=version.id, status="running")
        db.add(job)
        version.status = "processing"
        document.status = "processing"
        db.flush()
        try:
            preserved = self.settings.storage_root / "originals" / version.id / path.name
            preserved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, preserved)
            if _sha256_file(preserved) != version.sha256:
                raise ValueError("문서가 처리 중 변경되었습니다. 다시 열어 주세요.")
            path = preserved
            version.storage_path = str(preserved.resolve())
            parser = get_parser(path)
            parsed = parser.parse(path)
            version.parser_name = parsed.parser_name
            version.parser_version = parsed.parser_version
            version.metadata_json = parsed.metadata
            self._persist_parsed(db, version, parsed)
            job.fragment_count = len(parsed.fragments)
            job.status = "completed"
            job.completed_at = _utcnow()
            version.status = "completed"
            document.status = "ready"
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = _utcnow()
            version.status = "failed"
            version.error_message = str(exc)
            document.status = "failed"
            db.flush()
            raise
        db.flush()
        return version

    def _persist_parsed(self, db: Session, version: DocumentVersion, parsed: ParsedDocument) -> None:
        content = build_content(version, parsed)
        existing_content = db.get(DocumentContent, version.id)
        if existing_content:
            if (existing_content.kind, existing_content.text, existing_content.pages) != (
                content.kind, content.text, content.pages
            ):
                raise ValueError("보존된 본문을 변경하려면 새 문서 버전을 만들어야 합니다.")
            content = existing_content
        else:
            db.add(content)
        indexing_fragments = parsed.fragments
        if content.kind == "text":
            indexing_fragments = [ParsedFragment(
                stable_key="canonical", kind="document", ordinal=0, text=content.text,
                metadata={"text_start": 0, "text_end": utf16_length(content.text)},
            )]
        expanded: list[ParsedFragment] = []
        for fragment in indexing_fragments:
            expanded.extend(_chunks(fragment))

        texts = [_fragment_content(fragment) for fragment in expanded]
        nonempty_texts = [text for text in texts if text.strip()]
        embeddings: list[list[float]] = []
        batch_size = max(self.settings.embedding_batch_size, 1)
        for start in range(0, len(nonempty_texts), batch_size):
            embeddings.extend(self.embedding_provider.embed(nonempty_texts[start : start + batch_size]))
        embedding_iterator = iter(embeddings)
        asset_paths: dict[str, str] = {}
        asset_root = self.settings.storage_root / "assets" / version.id
        asset_root.mkdir(parents=True, exist_ok=True)
        for asset in parsed.assets:
            filename = _safe_asset_name(asset.key, asset.extension)
            asset_path = asset_root / filename
            asset_path.write_bytes(asset.data)
            asset_paths[asset.key] = str(asset_path)

        by_key: dict[str, Fragment] = {}
        rows: list[tuple[Fragment, ParsedFragment]] = []
        for ordinal, (fragment, content) in enumerate(zip(expanded, texts)):
            embedding = next(embedding_iterator) if content.strip() else None
            if not content and not fragment.asset_key:
                continue
            row = Fragment(
                version_id=version.id,
                stable_key=fragment.stable_key,
                kind=fragment.kind,
                ordinal=fragment.ordinal if fragment.ordinal is not None else ordinal,
                title=fragment.title,
                text=fragment.text,
                html=fragment.html,
                table_json=fragment.table_json,
                locator_json=fragment.locator,
                bbox_json=fragment.bbox,
                asset_path=asset_paths.get(fragment.asset_key or ""),
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                embedding_json=embedding,
                embedding_vector=embedding,
                embedding_model=f"{self.embedding_provider.name}:{self.embedding_provider.model}",
                metadata_json=fragment.metadata,
            )
            db.add(row)
            rows.append((row, fragment))
            by_key[fragment.stable_key] = row
        db.flush()
        for row, parsed_fragment in rows:
            parent = by_key.get(parsed_fragment.parent_key or "")
            if parent and parent.id != row.id:
                row.parent_id = parent.id
