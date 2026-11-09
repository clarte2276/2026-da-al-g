from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .auth import AdminUser, require_admin
from .db import get_db
from .links import content_indexer
from .models import (
    Document,
    DocumentContent,
    DocumentLink,
    DocumentVersion,
    Fragment,
    GlossaryEntry,
    IngestionJob,
    KnowledgeEdge,
)
from .services.document_content import utf16_length
from .services.ingestion import IngestionService
from .services.pdf_conversion import _font_path

router = APIRouter(prefix="/api", dependencies=[Depends(require_admin)])
DB = Annotated[Session, Depends(get_db)]
ARTICLE_RE = re.compile(r"(?m)^[ \t]*제(\d+)조\(")


class EntryWrite(BaseModel):
    category: Literal["부품", "장비", "용어", "기타"] = "부품"
    title: str = Field(max_length=200)
    code: str | None = Field(default=None, max_length=100)
    aliases: str = ""
    scope: str = ""
    location: str = ""
    photo_caption: str = ""
    definition: str = ""
    symptoms: str = ""
    actions: str = ""
    regulations: str = ""


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    category: str
    title: str
    code: str | None
    aliases: str
    scope: str
    location: str
    photo_caption: str
    definition: str
    symptoms: str
    actions: str
    regulations: str
    status: str
    has_photo: bool = False
    document_id: str | None
    updated_at: datetime


def output(entry: GlossaryEntry) -> EntryOut:
    return EntryOut.model_validate(
        {
            **{c.name: getattr(entry, c.name) for c in entry.__table__.columns},
            "has_photo": bool(entry.photo_path),
        }
    )


def required_entry(db: Session, entry_id: str) -> GlossaryEntry:
    entry = db.get(GlossaryEntry, entry_id)
    if not entry:
        raise HTTPException(404, "도해 사전을 찾을 수 없습니다.")
    return entry


@router.get("/glossary/regulation-refs")
def regulation_refs_endpoint(text: str, db: DB) -> list[dict]:
    return _resolve_refs(text, db)


def article_ranges(text: str) -> dict[int, dict[str, int | str]]:
    matches = list(ARTICLE_RE.finditer(text))
    result = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw = text[match.start() : end]
        article = raw.strip()
        if not article or re.fullmatch(rf"제{match.group(1)}조\(\s*삭제\s*\)", article):
            continue
        start = match.start() + len(raw) - len(raw.lstrip())
        result[int(match.group(1))] = {
            "start": utf16_length(text[:start]),
            "end": utf16_length(text[:start]) + utf16_length(article),
            "exact": article,
        }
    return result


@router.get("/glossary", response_model=list[EntryOut])
def list_entries(db: DB, q: str = "") -> list[EntryOut]:
    query = select(GlossaryEntry).order_by(GlossaryEntry.updated_at.desc())
    if q:
        pattern = f"%{q}%"
        query = query.where(
            GlossaryEntry.title.ilike(pattern)
            | GlossaryEntry.code.ilike(pattern)
            | GlossaryEntry.aliases.ilike(pattern)
        )
    return [output(row) for row in db.scalars(query)]


@router.get("/glossary/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: str, db: DB) -> EntryOut:
    return output(required_entry(db, entry_id))


@router.post("/glossary", response_model=EntryOut, status_code=201)
def create_entry(payload: EntryWrite, db: DB) -> EntryOut:
    entry = GlossaryEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return output(entry)


@router.put("/glossary/{entry_id}", response_model=EntryOut)
def update_entry(entry_id: str, payload: EntryWrite, db: DB) -> EntryOut:
    entry = required_entry(db, entry_id)
    for key, value in payload.model_dump().items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return output(entry)


def remove_document(db: Session, document_id: str) -> None:
    versions = select(DocumentVersion.id).where(DocumentVersion.document_id == document_id)
    fragments = select(Fragment.id).where(Fragment.version_id.in_(versions))
    db.execute(
        delete(KnowledgeEdge).where(
            KnowledgeEdge.source_fragment_id.in_(fragments)
            | KnowledgeEdge.target_fragment_id.in_(fragments)
        )
    )
    db.execute(
        delete(DocumentLink).where(
            DocumentLink.source_version_id.in_(versions)
            | DocumentLink.target_version_id.in_(versions)
        )
    )
    db.execute(delete(Fragment).where(Fragment.version_id.in_(versions)))
    db.execute(delete(DocumentContent).where(DocumentContent.version_id.in_(versions)))
    db.execute(delete(IngestionJob).where(IngestionJob.document_version_id.in_(versions)))
    db.execute(delete(DocumentVersion).where(DocumentVersion.document_id == document_id))
    db.execute(delete(Document).where(Document.id == document_id))


@router.delete("/glossary/{entry_id}", status_code=204)
def delete_entry(entry_id: str, db: DB) -> Response:
    entry = required_entry(db, entry_id)
    if entry.photo_path:
        Path(entry.photo_path).unlink(missing_ok=True)
    if entry.document_id:
        remove_document(db, entry.document_id)
    db.delete(entry)
    db.commit()
    return Response(status_code=204)


@router.put("/glossary/{entry_id}/photo", response_model=EntryOut)
async def upload_photo(
    entry_id: str,
    db: DB,
    file: Annotated[UploadFile, File(...)],
    indexer: Annotated[IngestionService, Depends(content_indexer)],
) -> EntryOut:
    entry = required_entry(db, entry_id)
    media = file.content_type or ""
    if media not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(415, "PNG, JPEG 또는 WebP 이미지만 업로드할 수 있습니다.")
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "사진은 10MB 이하여야 합니다.")
    folder = indexer.settings.storage_root / "glossary"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{entry.id}{Path(file.filename or '').suffix.lower()}"
    path.write_bytes(data)
    if entry.photo_path and Path(entry.photo_path) != path:
        Path(entry.photo_path).unlink(missing_ok=True)
    entry.photo_path, entry.photo_media_type = str(path), media
    db.commit()
    db.refresh(entry)
    return output(entry)


@router.delete("/glossary/{entry_id}/photo", response_model=EntryOut)
def delete_photo(entry_id: str, db: DB) -> EntryOut:
    entry = required_entry(db, entry_id)
    if entry.photo_path:
        Path(entry.photo_path).unlink(missing_ok=True)
    entry.photo_path = entry.photo_media_type = None
    db.commit()
    db.refresh(entry)
    return output(entry)


@router.get("/glossary/{entry_id}/photo")
def get_photo(entry_id: str, db: DB) -> Response:
    entry = required_entry(db, entry_id)
    if not entry.photo_path or not Path(entry.photo_path).is_file():
        raise HTTPException(404, "사진이 없습니다.")
    return Response(Path(entry.photo_path).read_bytes(), media_type=entry.photo_media_type)


def render_pdf(entry: GlossaryEntry, path: Path) -> None:
    from reportlab.pdfbase.ttfonts import TTFError, TTFont

    font = "Helvetica"
    candidate = _font_path()
    if candidate:
        try:
            pdfmetrics.registerFont(TTFont("GlossaryKorean", str(candidate)))
            font = "GlossaryKorean"
        except (OSError, TTFError, ValueError):
            font = "Helvetica"
    if font == "Helvetica":
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HYGothic-Medium"))
            font = "HYGothic-Medium"
        except (KeyError, ValueError):
            font = "Helvetica"
    styles = {
        "body": ParagraphStyle("body", fontName=font, fontSize=8, leading=9, wordWrap="CJK"),
        "title": ParagraphStyle("title", fontName=font, fontSize=15, leading=17, alignment=1),
    }
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    story = [Paragraph(f"도해 사전 · {entry.title}", styles["title"]), Spacer(1, 5 * mm)]
    fields = [
        ("분류", entry.category),
        ("표제어", entry.title),
        ("코드", entry.code),
        ("별칭·검색어", entry.aliases),
        ("적용 범위", entry.scope),
        ("설치 위치", entry.location),
    ]
    if entry.photo_path and Path(entry.photo_path).is_file():
        img = Image(entry.photo_path, width=1, height=1)
        img.drawWidth, img.drawHeight = img._restrictSize(68 * mm, 40 * mm)
        fields.append(("사진", img))
    fields += [
        ("사진 설명", entry.photo_caption),
        ("정의·기능", entry.definition),
        ("이상 현상", entry.symptoms),
        ("점검·조치", entry.actions),
        ("관련 규정", entry.regulations),
    ]
    rows = [
        [
            Paragraph(label, styles["body"]),
            value
            if isinstance(value, Image)
            else Paragraph((value or "").replace("\n", "<br/>"), styles["body"]),
        ]
        for label, value in fields
        if value or label in {"분류", "표제어"}
    ]
    table = Table(rows, colWidths=[33 * mm, 147 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    doc.build(story)


@router.post("/glossary/{entry_id}/publish")
def publish(
    entry_id: str,
    db: DB,
    admin: AdminUser,
    indexer: Annotated[IngestionService, Depends(content_indexer)],
) -> dict:
    entry = required_entry(db, entry_id)
    if not entry.title.strip() or not entry.definition.strip():
        raise HTTPException(422, "표제어와 정의·기능은 필수입니다.")
    settings = indexer.settings
    folder = settings.storage_root / "glossary"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{entry.id}.pdf"
    render_pdf(entry, path)
    old_document = db.get(Document, entry.document_id) if entry.document_id else None
    if old_document:
        old_document.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        old_document.source_path = str(path)
        old_document.filename = f"도해사전_{entry.category}_{entry.code or entry.title}.pdf"
        for version in db.scalars(
            select(DocumentVersion).where(DocumentVersion.document_id == old_document.id)
        ).all():
            ids = select(Fragment.id).where(Fragment.version_id == version.id)
            db.execute(
                delete(KnowledgeEdge).where(
                    KnowledgeEdge.source_fragment_id.in_(ids)
                    | KnowledgeEdge.target_fragment_id.in_(ids)
                )
            )
            db.execute(
                delete(DocumentLink).where(
                    (DocumentLink.source_version_id == version.id)
                    | (DocumentLink.target_version_id == version.id)
                )
            )
            db.execute(delete(Fragment).where(Fragment.version_id == version.id))
            db.delete(version)
            db.execute(delete(DocumentContent).where(DocumentContent.version_id == version.id))
            db.execute(delete(IngestionJob).where(IngestionJob.document_version_id == version.id))
        db.flush()
        document, version = old_document, indexer.ingest_existing_document(db, old_document.id)
    else:
        document, version = indexer.ingest_new_file(
            db,
            path,
            f"도해사전_{entry.category}_{entry.code or entry.title}.pdf",
            "application/pdf",
        )
        entry.document_id = document.id
    links = []
    for ref in regulation_refs(entry.regulations, db):
        if not ref["found"]:
            links.append({"ref": ref["ref"], "status": "not_found", "link_id": None})
            continue
        prior = db.scalar(
            select(DocumentLink).where(
                DocumentLink.source_version_id == version.id,
                DocumentLink.target_version_id == ref["version_id"],
                DocumentLink.relation_type == "VISUAL_HELP",
            )
        )
        if prior:
            links.append({"ref": ref["ref"], "status": "exists", "link_id": prior.id})
            continue
        link = DocumentLink(
            source_version_id=version.id,
            target_version_id=ref["version_id"],
            source_selection={"kind": "pages", "version_id": version.id, "pages": [1]},
            target_selection={
                "kind": "text",
                "version_id": ref["version_id"],
                "ranges": [{k: ref["selection"][k] for k in ("start", "end", "exact")}],
            },
            relation_type="VISUAL_HELP",
            status="draft",
            created_by=admin.id,
        )
        db.add(link)
        db.flush()
        links.append({"ref": ref["ref"], "status": "draft", "link_id": link.id})
    entry.status = "published"
    db.commit()
    return {
        "entry": output(entry).model_dump(mode="json"),
        "document_id": document.id,
        "version_id": version.id,
        "links": links,
    }


def regulation_refs(text: str, db: Session) -> list[dict]:
    # Route/helper share one implementation; the endpoint remains read-only.
    return _resolve_refs(text, db)


def _resolve_refs(text: str, db: Session) -> list[dict]:
    # Keep resolution bounded to the regulation filename match and its latest completed version.
    refs = [x.strip() for x in text.split(",") if x.strip()]
    results = []
    for ref in refs:
        m = re.search(r"(.+?)\s*(?:제)?(\d+)조", ref)
        found = None
        if m:
            for doc in db.scalars(
                select(Document).where(Document.filename.ilike(f"%{m.group(1).strip()}%"))
            ).all():
                ver = db.scalar(
                    select(DocumentVersion)
                    .where(
                        DocumentVersion.document_id == doc.id, DocumentVersion.status == "completed"
                    )
                    .order_by(DocumentVersion.version_number.desc())
                    .limit(1)
                )
                content = db.get(DocumentContent, ver.id) if ver else None
                article = (
                    article_ranges(content.text).get(int(m.group(2)))
                    if content and content.kind == "text"
                    else None
                )
                if article:
                    found = {
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "article": article["exact"],
                        "title": article["exact"].splitlines()[0],
                        "version_id": ver.id,
                        "selection": {
                            "kind": "text",
                            "version_id": ver.id,
                            "start": article["start"],
                            "end": article["end"],
                            "exact": article["exact"],
                        },
                    }
                    break
        results.append(
            {
                "ref": ref,
                "found": bool(found),
                **(
                    found or {"document_id": None, "filename": None, "article": None, "title": None}
                ),
            }
        )
    return results
