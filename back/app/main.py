from __future__ import annotations

import mimetypes
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, init_db
from .links import get_version
from .links import router as links_router
from .models import AuditEvent, Document, DocumentVersion, Fragment, KnowledgeEdge
from .schemas import (
    DocumentOut,
    EdgeBatchCreate,
    EdgeBatchOut,
    EdgeCreate,
    EdgeDecision,
    EdgeOut,
    EvidenceOut,
    FragmentOut,
    LocalFileOut,
    LocalOpenOut,
    LocalOpenRequest,
    LocalRootOut,
    NeighborOut,
    RAGQuery,
    RAGResponse,
    SelectionAnchor,
    VersionOut,
)
from .services.document_content import verified_source
from .services.embedding import get_embedding_provider
from .services.ingestion import IngestionService
from .services.local_files import LocalFile, LocalFileService
from .services.pdf_conversion import PdfConversionError, PdfConversionService
from .services.rag import GraphRAGService

settings = get_settings()
embedding_provider = get_embedding_provider(settings)
ingestion_service = IngestionService(settings, embedding_provider)
local_file_service = LocalFileService(settings)
rag_service = GraphRAGService(settings, embedding_provider)
pdf_conversion_service = PdfConversionService(settings)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(links_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


def _fragment_out(fragment: Fragment) -> FragmentOut:
    return FragmentOut(
        id=fragment.id,
        version_id=fragment.version_id,
        parent_id=fragment.parent_id,
        stable_key=fragment.stable_key,
        kind=fragment.kind,
        ordinal=fragment.ordinal,
        title=fragment.title,
        text=fragment.text,
        html=fragment.html,
        table_json=fragment.table_json,
        locator_json=fragment.locator_json,
        bbox_json=fragment.bbox_json,
        asset_url=f"/api/fragments/{fragment.id}/asset" if fragment.asset_path else None,
        content_hash=fragment.content_hash,
        metadata_json=fragment.metadata_json,
    )


def _edge_out(edge: KnowledgeEdge) -> EdgeOut:
    return EdgeOut(
        id=edge.id,
        source_fragment_id=edge.source_fragment_id,
        target_fragment_id=edge.target_fragment_id,
        relation_type=edge.relation_type,
        status=edge.status,
        source=edge.source,
        note=edge.note,
        confidence=edge.confidence,
        source_anchor=(
            SelectionAnchor.model_validate(edge.source_anchor_json)
            if edge.source_anchor_json
            else None
        ),
        target_anchor=(
            SelectionAnchor.model_validate(edge.target_anchor_json)
            if edge.target_anchor_json
            else None
        ),
        created_by=edge.created_by,
        approved_by=edge.approved_by,
        created_at=edge.created_at,
        approved_at=edge.approved_at,
    )


def _version_out(db: Session, version: DocumentVersion) -> VersionOut:
    return VersionOut(
        id=version.id,
        document_id=version.document_id,
        version_number=version.version_number,
        status=version.status,
        parser_name=version.parser_name,
        fragment_count=db.scalar(
            select(func.count(Fragment.id)).where(Fragment.version_id == version.id)
        )
        or 0,
        error_message=version.error_message,
    )


def _local_file_out(local_file: LocalFile) -> LocalFileOut:
    stat = local_file.path.stat()
    relative_path = local_file.relative_path
    return LocalFileOut(
        id=f"{local_file.root.id}:{relative_path}",
        root_id=local_file.root.id,
        relative_path=relative_path,
        filename=local_file.path.name,
        suffix=local_file.suffix,
        size_bytes=stat.st_size,
        modified_at=local_file.modified_at,
    )


def _audit(
    db: Session,
    *,
    actor: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    payload: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=payload or {},
        )
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "embedding_provider": embedding_provider.name}


@app.get("/api/local/roots", response_model=list[LocalRootOut])
def list_local_roots() -> list[LocalRootOut]:
    return [
        LocalRootOut(id=root.id, label=root.path.name or str(root.path))
        for root in local_file_service.roots()
        if root.path.is_dir()
    ]


@app.get("/api/local/files", response_model=list[LocalFileOut])
def list_local_files(
    root_id: str | None = Query(default=None),
    query: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=500, ge=1, le=20000),
) -> list[LocalFileOut]:
    try:
        files = local_file_service.list_files(root_id=root_id, query=query, limit=limit)
        return [_local_file_out(local_file) for local_file in files]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/local/open", response_model=LocalOpenOut)
def open_local_document(
    payload: LocalOpenRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LocalOpenOut:
    try:
        local_file = local_file_service.resolve(payload.root_id, payload.relative_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Local document not found") from exc

    if local_file.path.stat().st_size > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Local document is too large")
    try:
        document, version = ingestion_service.ingest_new_file(
            db,
            local_file.path,
            local_file.path.name,
            mimetypes.guess_type(local_file.path.name)[0],
        )
        # A moved file with the same content keeps its document and edge IDs.
        document.source_path = str(local_file.path)
        document.filename = local_file.path.name
        document.mime_type = mimetypes.guess_type(local_file.path.name)[0]
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LocalOpenOut(
        root_id=payload.root_id,
        relative_path=local_file.relative_path,
        document=DocumentOut.model_validate(document),
        version=_version_out(db, version),
    )


@app.get("/api/documents", response_model=list[DocumentOut])
def list_documents(db: Annotated[Session, Depends(get_db)]) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())).all())


@app.get("/api/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Annotated[Session, Depends(get_db)]) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.get("/api/documents/{document_id}/versions", response_model=list[VersionOut])
def list_versions(document_id: str, db: Annotated[Session, Depends(get_db)]) -> list[VersionOut]:
    versions = list(
        db.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        ).all()
    )
    return [
        VersionOut(
            id=version.id,
            document_id=version.document_id,
            version_number=version.version_number,
            status=version.status,
            parser_name=version.parser_name,
            fragment_count=db.scalar(
                select(func.count(Fragment.id)).where(Fragment.version_id == version.id)
            )
            or 0,
            error_message=version.error_message,
        )
        for version in versions
    ]


@app.post("/api/documents/{document_id}/ingest", response_model=VersionOut)
def reingest_document(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> VersionOut:
    try:
        version = ingestion_service.ingest_existing_document(db, document_id)
        db.commit()
    except FileNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"Source file not found: {exc}") from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return VersionOut(
        id=version.id,
        document_id=version.document_id,
        version_number=version.version_number,
        status=version.status,
        parser_name=version.parser_name,
        fragment_count=db.scalar(
            select(func.count(Fragment.id)).where(Fragment.version_id == version.id)
        )
        or 0,
        error_message=version.error_message,
    )


@app.post("/api/documents/upload")
def upload_document(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".docx", ".hwp", ".hwpx", ".pptx", ".pdf"}:
        raise HTTPException(status_code=415, detail="Only .docx, .hwp, .hwpx, .pptx, and .pdf are supported")
    upload_dir = settings.storage_root / "originals"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in ".-_" else "_" for ch in (file.filename or "document"))
    path = upload_dir / f"{secrets.token_hex(8)}_{safe_name}"
    size = 0
    with path.open("wb") as handle:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Uploaded file is too large")
            handle.write(chunk)
    try:
        document, version = ingestion_service.ingest_new_file(
            db,
            path,
            file.filename or safe_name,
            file.content_type or mimetypes.guess_type(file.filename or "")[0],
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "document": DocumentOut.model_validate(document).model_dump(mode="json"),
        "version": {
            "id": version.id,
            "status": version.status,
            "parser_name": version.parser_name,
            "fragment_count": db.scalar(
                select(func.count(Fragment.id)).where(Fragment.version_id == version.id)
            )
            or 0,
        },
    }


@app.get("/api/documents/{document_id}/fragments", response_model=list[FragmentOut])
def list_fragments(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    kind: str | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=20000),
) -> list[FragmentOut]:
    latest_version_id = (
        select(DocumentVersion.id)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
        .scalar_subquery()
    )
    query = select(Fragment).where(Fragment.version_id == latest_version_id)
    if kind:
        query = query.where(Fragment.kind == kind)
    fragments = list(db.scalars(query.order_by(Fragment.ordinal).limit(limit)).all())
    return [_fragment_out(fragment) for fragment in fragments]


@app.get("/api/documents/{document_id}/source")
def get_document_source(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    version_id: str | None = None,
) -> FileResponse:
    """Stream the original bytes to the browser-native document renderers."""

    document = db.get(Document, document_id)
    if not document or not document.source_path:
        raise HTTPException(status_code=404, detail="Document source not found")
    source_path = verified_source(get_version(db, document_id, version_id))
    return FileResponse(
        source_path,
        media_type=document.mime_type or mimetypes.guess_type(document.filename)[0] or "application/octet-stream",
        filename=document.filename,
    )


@app.get("/api/documents/{document_id}/pdf")
def get_document_pdf(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    version_id: str | None = None,
) -> FileResponse:
    """Return a PDF representation rendered by an Office-compatible converter."""

    document = db.get(Document, document_id)
    if not document or not document.source_path:
        raise HTTPException(status_code=404, detail="Document source not found")
    version = get_version(db, document_id, version_id)
    source_path = verified_source(version)
    try:
        pdf_path, converter = pdf_conversion_service.convert(source_path, version.sha256)
    except PdfConversionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{Path(document.filename).stem}.pdf",
        headers={"X-Daalgi-Pdf-Converter": converter},
    )


@app.get("/api/fragments/{fragment_id}", response_model=FragmentOut)
def get_fragment(fragment_id: str, db: Annotated[Session, Depends(get_db)]) -> FragmentOut:
    fragment = db.get(Fragment, fragment_id)
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return _fragment_out(fragment)


@app.get("/api/fragments/{fragment_id}/asset")
def get_fragment_asset(
    fragment_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    fragment = db.get(Fragment, fragment_id)
    if not fragment or not fragment.asset_path:
        raise HTTPException(status_code=404, detail="Fragment asset not found")
    asset_path = Path(fragment.asset_path).resolve()
    storage_root = settings.storage_root.resolve()
    try:
        asset_path.relative_to(storage_root)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Fragment asset not found") from exc
    if not asset_path.is_file():
        raise HTTPException(status_code=404, detail="Fragment asset not found")
    return FileResponse(
        asset_path,
        media_type=mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream",
        filename=asset_path.name,
    )


@app.post("/api/edges", response_model=EdgeOut, status_code=201)
def create_edge(
    payload: EdgeCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str | None, Header(alias="X-Admin-Actor")] = None,
) -> EdgeOut:
    source = db.get(Fragment, payload.source_fragment_id)
    target = db.get(Fragment, payload.target_fragment_id)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Both source and target fragments are required")
    if source.id == target.id:
        raise HTTPException(status_code=400, detail="A fragment cannot link to itself")
    if bool(payload.source_anchor) != bool(payload.target_anchor):
        raise HTTPException(
            status_code=400,
            detail="Source and target selection anchors must be provided together",
        )
    if payload.source_anchor and payload.source_anchor.fragment_id != source.id:
        raise HTTPException(status_code=400, detail="Source anchor does not match source fragment")
    if payload.target_anchor and payload.target_anchor.fragment_id != target.id:
        raise HTTPException(status_code=400, detail="Target anchor does not match target fragment")
    edge = KnowledgeEdge(
        source_fragment_id=source.id,
        target_fragment_id=target.id,
        relation_type=payload.relation_type,
        source=payload.source,
        note=payload.note,
        confidence=payload.confidence,
        source_anchor_json=(
            payload.source_anchor.model_dump(mode="json") if payload.source_anchor else None
        ),
        target_anchor_json=(
            payload.target_anchor.model_dump(mode="json") if payload.target_anchor else None
        ),
        created_by=payload.created_by or actor,
        status="draft",
    )
    db.add(edge)
    try:
        db.flush()
        _audit(
            db,
            actor=payload.created_by or actor,
            action="edge.created",
            entity_type="knowledge_edge",
            entity_id=edge.id,
            payload={"relation_type": payload.relation_type, "source": payload.source},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This edge already exists") from exc
    db.refresh(edge)
    return _edge_out(edge)


@app.post("/api/edges/batch", response_model=EdgeBatchOut, status_code=201)
def create_edge_batch(
    payload: EdgeBatchCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str | None, Header(alias="X-Admin-Actor")] = None,
) -> EdgeBatchOut:
    """Turn one selection on each side into a many-to-many set of edges."""

    source_anchors = list({anchor.fragment_id: anchor for anchor in payload.source_anchors}.values())
    target_anchors = list({anchor.fragment_id: anchor for anchor in payload.target_anchors}.values())
    source_ids = [anchor.fragment_id for anchor in source_anchors]
    target_ids = [anchor.fragment_id for anchor in target_anchors]
    fragment_ids = set(source_ids + target_ids)
    fragments = {
        fragment.id
        for fragment in db.scalars(select(Fragment).where(Fragment.id.in_(fragment_ids))).all()
    }
    missing = fragment_ids - fragments
    if missing:
        raise HTTPException(status_code=404, detail="One or more selected fragments no longer exist")

    candidate_pairs = [
        (source_anchor.fragment_id, target_anchor.fragment_id)
        for source_anchor in source_anchors
        for target_anchor in target_anchors
        if source_anchor.fragment_id != target_anchor.fragment_id
    ]
    if not candidate_pairs:
        raise HTTPException(status_code=400, detail="At least one pair of different fragments is required")

    relation_type = payload.relation_type or "RELATED"
    existing_rows = db.execute(
        select(KnowledgeEdge.source_fragment_id, KnowledgeEdge.target_fragment_id).where(
            KnowledgeEdge.source_fragment_id.in_(source_ids),
            KnowledgeEdge.target_fragment_id.in_(target_ids),
            KnowledgeEdge.relation_type == relation_type,
        )
    ).all()
    existing_pairs = {(row[0], row[1]) for row in existing_rows}

    edges: list[KnowledgeEdge] = []
    for source_anchor in source_anchors:
        for target_anchor in target_anchors:
            pair = (source_anchor.fragment_id, target_anchor.fragment_id)
            if pair in existing_pairs or pair[0] == pair[1]:
                continue
            edge = KnowledgeEdge(
                source_fragment_id=source_anchor.fragment_id,
                target_fragment_id=target_anchor.fragment_id,
                relation_type=relation_type,
                source=payload.source,
                note=payload.note,
                confidence=payload.confidence,
                source_anchor_json=source_anchor.model_dump(mode="json"),
                target_anchor_json=target_anchor.model_dump(mode="json"),
                created_by=payload.created_by or actor,
                status="draft",
            )
            db.add(edge)
            edges.append(edge)

    try:
        db.flush()
        for edge in edges:
            _audit(
                db,
                actor=payload.created_by or actor,
                action="edge.created",
                entity_type="knowledge_edge",
                entity_id=edge.id,
                payload={
                    "relation_type": relation_type,
                    "source": payload.source,
                    "batch": True,
                },
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="One or more edges already exist") from exc

    for edge in edges:
        db.refresh(edge)
    return EdgeBatchOut(
        edges=[_edge_out(edge) for edge in edges],
        created_count=len(edges),
        skipped_count=len(candidate_pairs) - len(edges),
    )


@app.get("/api/edges", response_model=list[EdgeOut])
def list_edges(
    db: Annotated[Session, Depends(get_db)],
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[EdgeOut]:
    query = select(KnowledgeEdge).order_by(KnowledgeEdge.created_at.desc()).limit(limit)
    if status:
        query = query.where(KnowledgeEdge.status == status)
    return [_edge_out(edge) for edge in db.scalars(query).all()]


@app.get("/api/edges/{edge_id}", response_model=EdgeOut)
def get_edge(edge_id: str, db: Annotated[Session, Depends(get_db)]) -> EdgeOut:
    edge = db.get(KnowledgeEdge, edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return _edge_out(edge)


@app.post("/api/edges/{edge_id}/approve", response_model=EdgeOut)
def approve_edge(
    edge_id: str,
    payload: EdgeDecision,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str | None, Header(alias="X-Admin-Actor")] = None,
) -> EdgeOut:
    edge = db.get(KnowledgeEdge, edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    edge.status = "approved"
    edge.approved_by = payload.actor or actor or "admin"
    edge.approved_at = datetime.now(UTC)
    _audit(
        db,
        actor=edge.approved_by,
        action="edge.approved",
        entity_type="knowledge_edge",
        entity_id=edge.id,
    )
    db.commit()
    db.refresh(edge)
    return _edge_out(edge)


@app.post("/api/edges/{edge_id}/reject", response_model=EdgeOut)
def reject_edge(
    edge_id: str,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str | None, Header(alias="X-Admin-Actor")] = None,
) -> EdgeOut:
    edge = db.get(KnowledgeEdge, edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    edge.status = "rejected"
    _audit(
        db,
        actor=actor,
        action="edge.rejected",
        entity_type="knowledge_edge",
        entity_id=edge.id,
    )
    db.commit()
    db.refresh(edge)
    return _edge_out(edge)


@app.get("/api/fragments/{fragment_id}/neighbors", response_model=list[NeighborOut])
def neighbors(
    fragment_id: str,
    db: Annotated[Session, Depends(get_db)],
    include_drafts: bool = False,
) -> list[NeighborOut]:
    fragment = db.get(Fragment, fragment_id)
    if not fragment:
        raise HTTPException(status_code=404, detail="Fragment not found")
    query = select(KnowledgeEdge).where(
        (KnowledgeEdge.source_fragment_id == fragment_id)
        | (KnowledgeEdge.target_fragment_id == fragment_id)
    )
    if not include_drafts:
        query = query.where(KnowledgeEdge.status == "approved")
    result: list[NeighborOut] = []
    for edge in db.scalars(query).all():
        outgoing = edge.source_fragment_id == fragment_id
        neighbor_id = edge.target_fragment_id if outgoing else edge.source_fragment_id
        neighbor = db.get(Fragment, neighbor_id)
        if neighbor:
            result.append(
                NeighborOut(
                    fragment=_fragment_out(neighbor),
                    edge=_edge_out(edge),
                    direction="outgoing" if outgoing else "incoming",
                    hop=1,
                )
            )
    return result


@app.post("/api/rag/query", response_model=RAGResponse)
def rag_query(payload: RAGQuery, db: Annotated[Session, Depends(get_db)]) -> RAGResponse:
    evidence = rag_service.retrieve(
        db,
        payload.question,
        top_k=payload.top_k,
        max_hops=payload.max_hops,
        relation_types=payload.relation_types,
    )
    answer = rag_service.answer(payload.question, evidence, payload.model)
    return RAGResponse(
        answer=answer,
        evidence=[
            EvidenceOut(
                fragment=None if item.link_id else _fragment_out(item.fragment),
                text=item.fragment.text if item.link_id else None,
                score=item.score,
                hop=item.hop,
                path=item.path,
                via_relation=item.via_relation,
                link_id=item.link_id,
                selection=item.selection,
                document_id=item.document_id,
                filename=item.filename,
            )
            for item in evidence
        ],
        embedding_provider=embedding_provider.name,
        graph_expanded=any(item.hop > 0 for item in evidence),
    )
