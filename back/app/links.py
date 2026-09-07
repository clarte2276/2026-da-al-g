from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import AuditEvent, Document, DocumentLink, DocumentVersion, Fragment
from .parsers import ParsedDocument
from .schemas import EdgeDecision, LinkWrite
from .services.document_content import ensure_content, validate_selection, verified_source
from .services.embedding import get_embedding_provider
from .services.ingestion import IngestionService

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[str | None, Header(alias="X-Admin-Actor")]


@lru_cache
def content_indexer() -> IngestionService:
    settings = get_settings()
    return IngestionService(settings, get_embedding_provider(settings))


def get_version(db: Session, document_id: str, version_id: str | None) -> DocumentVersion:
    version = db.get(DocumentVersion, version_id) if version_id else db.scalar(
        select(DocumentVersion).where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc()).limit(1)
    )
    if not version or version.document_id != document_id:
        raise HTTPException(404, "문서 버전을 찾을 수 없습니다.")
    return version


@router.get("/documents/{document_id}/content")
def get_content(document_id: str, db: DB,
                indexer: Annotated[IngestionService, Depends(content_indexer)],
                version_id: str | None = None) -> dict:
    version = get_version(db, document_id, version_id)
    if version.status not in {"completed", "ready"}:
        raise HTTPException(409, "문서 처리가 완료되지 않았습니다.")
    verified_source(version)
    content = ensure_content(db, version)
    if content.kind == "text" and not db.scalar(select(Fragment.id).where(
        Fragment.version_id == version.id,
        (Fragment.stable_key == "canonical") | Fragment.stable_key.like("canonical:chunk:%"),
    ).limit(1)):
        # Add complete indexing for older documents without touching their fragments or links.
        indexer._persist_parsed(db, version, ParsedDocument(
            parser_name=version.parser_name or "legacy", parser_version=version.parser_version or "",
            fragments=[], plain_text=content.text,
        ))
    document = db.get(Document, document_id)
    db.commit()
    return {"document_id": document_id, "version_id": version.id,
            "version_number": version.version_number,
            "filename": document.filename, "kind": content.kind,
            "text": content.text, "pages": [{"number": p["number"]} for p in content.pages]}


def link_out(db: Session, link: DocumentLink) -> dict:
    result = {column.name: getattr(link, column.name) for column in link.__table__.columns}
    for side in ("source", "target"):
        version = db.get(DocumentVersion, getattr(link, f"{side}_version_id"))
        document = db.get(Document, version.document_id)
        result[f"{side}_document_id"] = document.id
        result[f"{side}_filename"] = document.filename
    return result


def require_link(db: Session, link_id: str) -> DocumentLink:
    link = db.get(DocumentLink, link_id)
    if not link:
        raise HTTPException(404, "연결을 찾을 수 없습니다.")
    return link


def write_link(db: Session, link: DocumentLink, payload: LinkWrite, actor: str | None) -> dict:
    source = validate_selection(db, payload.source_selection.model_dump())
    target = validate_selection(db, payload.target_selection.model_dump())
    if source == target:
        raise HTTPException(422, "동일한 선택을 자기 자신과 연결할 수 없습니다.")
    link.source_version_id = source["version_id"]
    link.target_version_id = target["version_id"]
    link.source_selection, link.target_selection = source, target
    link.note, link.relation_type = payload.note, payload.relation_type
    link.status, link.approved_by, link.approved_at = "draft", None, None
    action = "link.updated" if link.id else "link.created"
    db.add(link)
    db.flush()
    db.add(AuditEvent(actor=actor, action=action, entity_type="document_link", entity_id=link.id))
    db.commit()
    return link_out(db, link)


@router.post("/links", status_code=201)
def create_link(payload: LinkWrite, db: DB, actor: Actor = None) -> dict:
    return write_link(db, DocumentLink(created_by=actor), payload, actor)


@router.get("/links")
def list_links(db: DB, status: Literal["draft", "approved", "rejected"] | None = None) -> list:
    query = select(DocumentLink).order_by(DocumentLink.created_at.desc())
    if status:
        query = query.where(DocumentLink.status == status)
    return [link_out(db, link) for link in db.scalars(query).all()]


@router.get("/links/{link_id}")
def get_link(link_id: str, db: DB) -> dict:
    return link_out(db, require_link(db, link_id))


@router.put("/links/{link_id}")
def update_link(link_id: str, payload: LinkWrite, db: DB, actor: Actor = None) -> dict:
    return write_link(db, require_link(db, link_id), payload, actor)


@router.post("/links/{link_id}/{decision}")
def decide_link(link_id: str, decision: Literal["approve", "reject"],
                payload: EdgeDecision, db: DB) -> dict:
    link = require_link(db, link_id)
    if decision == "approve":
        validate_selection(db, link.source_selection)
        validate_selection(db, link.target_selection)
    link.status = "approved" if decision == "approve" else "rejected"
    link.approved_by = payload.actor if decision == "approve" else None
    link.approved_at = datetime.now(UTC) if decision == "approve" else None
    db.add(AuditEvent(actor=payload.actor, action=f"link.{link.status}",
                      entity_type="document_link", entity_id=link.id))
    db.commit()
    return link_out(db, link)
