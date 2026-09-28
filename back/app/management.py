from __future__ import annotations

import hashlib
import io
import re
from calendar import monthrange
from datetime import UTC, date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from openpyxl import load_workbook
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import AdminUser, CurrentUser, normalize_username, password_hash
from .config import get_settings
from .db import get_db
from .models import AuditEvent, AuthSession, BookmarkRecord, ConversationRecord, DutySchedule, User
from .schemas import UserOut

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,64}$")


class ConversationWrite(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(max_length=200)
    createdAt: datetime
    messages: list[dict[str, Any]] = Field(max_length=500)


class BookmarkWrite(BaseModel):
    regulation: str = Field(min_length=1, max_length=200)
    chapter: str = Field(min_length=1, max_length=200)
    version: str = Field(max_length=100)
    excerpt: str | None = Field(default=None, max_length=10000)
    content: str | None = Field(default=None, max_length=20000)
    sourcePath: str | None = Field(default=None, max_length=2000)
    chunkId: str | None = Field(default=None, max_length=100)
    retriever: str | None = Field(default=None, max_length=100)
    documentId: str | None = Field(default=None, max_length=100)
    versionId: str | None = Field(default=None, max_length=100)
    page: int | None = Field(default=None, ge=1)


class ImportWrite(BaseModel):
    conversations: list[ConversationWrite] = Field(default_factory=list, max_length=1000)
    bookmarks: list[BookmarkWrite] = Field(default_factory=list, max_length=1000)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None


def _audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str,
           payload: dict | None = None) -> None:
    db.add(AuditEvent(actor=actor, action=action, entity_type=entity_type,
                      entity_id=entity_id, payload_json=payload or {}))


def _bookmark_id(data: BookmarkWrite) -> str:
    return hashlib.sha256(f"{data.regulation}|{data.chapter}".encode()).hexdigest()


def _validate_conversation(data: ConversationWrite) -> None:
    for message in data.messages:
        if not isinstance(message.get("isUser"), bool) or not isinstance(message.get("text"), str):
            raise HTTPException(422, "Invalid conversation message")
        if len(message["text"]) > 20000:
            raise HTTPException(422, "Conversation message too long")


@router.get("/me/conversations")
def my_conversations(db: DB, user: CurrentUser) -> list[dict]:
    rows = db.scalars(select(ConversationRecord).where(ConversationRecord.user_id == user.id,
                            ConversationRecord.deleted.is_(False)).order_by(ConversationRecord.updated_at.desc())).all()
    return [row.data for row in rows]


@router.put("/me/conversations/{conversation_id}")
def save_conversation(conversation_id: str, payload: ConversationWrite, db: DB, user: CurrentUser) -> dict:
    if conversation_id != payload.id:
        raise HTTPException(422, "Conversation ID mismatch")
    _validate_conversation(payload)
    row = db.get(ConversationRecord, (conversation_id, user.id))
    if row and row.deleted:
        raise HTTPException(410, "Conversation was deleted")
    if not row:
        row = ConversationRecord(id=conversation_id, user_id=user.id, data={})
        db.add(row)
    row.data = payload.model_dump(mode="json")
    db.commit()
    return row.data


@router.delete("/me/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: DB, user: CurrentUser) -> dict:
    row = db.get(ConversationRecord, (conversation_id, user.id))
    if not row:
        row = ConversationRecord(id=conversation_id, user_id=user.id, data={}, deleted=True)
        db.add(row)
    row.deleted = True
    row.data = {}
    db.commit()
    return {"status": "ok"}


@router.get("/me/bookmarks")
def my_bookmarks(db: DB, user: CurrentUser) -> list[dict]:
    rows = db.scalars(select(BookmarkRecord).where(BookmarkRecord.user_id == user.id,
                            BookmarkRecord.deleted.is_(False)).order_by(BookmarkRecord.updated_at.desc())).all()
    return [row.data for row in rows]


@router.post("/me/bookmarks")
def save_bookmark(payload: BookmarkWrite, db: DB, user: CurrentUser) -> dict:
    key = _bookmark_id(payload)
    row = db.get(BookmarkRecord, (key, user.id))
    if row and row.deleted:
        raise HTTPException(410, "Bookmark was deleted")
    if not row:
        row = BookmarkRecord(id=key, user_id=user.id, data={})
        db.add(row)
    row.data = payload.model_dump(mode="json")
    db.commit()
    return row.data


@router.delete("/me/bookmarks")
def delete_bookmark(payload: BookmarkWrite, db: DB, user: CurrentUser) -> dict:
    key = _bookmark_id(payload)
    row = db.get(BookmarkRecord, (key, user.id))
    if not row:
        row = BookmarkRecord(id=key, user_id=user.id, data={}, deleted=True)
        db.add(row)
    row.deleted = True
    row.data = {}
    db.commit()
    return {"status": "ok"}


@router.post("/me/import")
def import_local(payload: ImportWrite, db: DB, user: CurrentUser) -> dict:
    for item in payload.conversations:
        _validate_conversation(item)
        if not db.get(ConversationRecord, (item.id, user.id)):
            db.add(ConversationRecord(id=item.id, user_id=user.id, data=item.model_dump(mode="json")))
    for item in payload.bookmarks:
        key = _bookmark_id(item)
        if not db.get(BookmarkRecord, (key, user.id)):
            db.add(BookmarkRecord(id=key, user_id=user.id, data=item.model_dump(mode="json")))
    db.commit()
    return {"status": "ok"}


@router.get("/duty/{month}")
def get_duty(month: str, db: DB, _user: CurrentUser) -> dict:
    if not MONTH_RE.fullmatch(month):
        raise HTTPException(422, "Invalid month")
    row = db.get(DutySchedule, month)
    if not row:
        raise HTTPException(404, "No duty schedule for this month")
    return row.data


@router.get("/duty")
def available_duty_months(db: DB, _user: CurrentUser) -> list[str]:
    return list(db.scalars(select(DutySchedule.month).order_by(DutySchedule.month.desc())).all())


@router.get("/admin/duty")
def list_duty(db: DB, _admin: AdminUser) -> list[dict]:
    rows = db.scalars(select(DutySchedule).order_by(DutySchedule.month.desc())).all()
    return [{"month": x.month, "source_filename": x.source_filename, "updated_at": x.updated_at,
             "driver_count": len(x.data["drivers"])} for x in rows]


def parse_duty_xlsx(data: bytes, month: str, filename: str) -> dict:
    try:
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        sheet = workbook["교번기관사 근무계획"]
    except Exception as exc:
        raise ValueError("근무계획 엑셀 양식이 올바르지 않습니다") from exc
    try:
        header = next(sheet.iter_rows(min_row=2, max_row=2, values_only=True))
        dates = {i: v.date() if isinstance(v, datetime) else v for i, v in enumerate(header)
                 if isinstance(v, (date, datetime)) and v.strftime("%Y-%m") == month}
        if len(dates) != monthrange(int(month[:4]), int(month[-2:]))[1]:
            raise ValueError("선택한 월의 날짜 열을 찾을 수 없습니다")
        drivers = []
        for row in sheet.iter_rows(min_row=7, values_only=True):
            no, name = row[:2]
            if not isinstance(no, int) or not isinstance(name, str) or not name.strip():
                continue
            days = {}
            for col, day in dates.items():
                code = str(row[col]).strip() if row[col] is not None else ""
                if not code:
                    raise ValueError(f"{name}: {day} 근무 코드가 비어 있습니다")
                if code == "비": kind = "off"
                elif code.startswith(("휴", "운휴")): kind = "rest"
                elif code.startswith("대"): kind = "standby"
                elif code.startswith("지정"): kind = "designated"
                elif code.isdigit() and int(code) < 60: kind = "day"
                elif code.isdigit(): kind = "night"
                else: kind = "unknown"
                days[day.isoformat()] = {"code": code, "type": kind,
                                         "turn": code if kind in {"day", "night", "standby"} else None}
            drivers.append({"no": no, "name": name.strip(), "days": days})
        if not drivers or len({x["no"] for x in drivers}) != len(drivers):
            raise ValueError("기관사 행이 없거나 연번이 중복되었습니다")
        return {"month": month, "line": "6호선", "office": "승무사업소", "source": filename,
                "dates": [day.isoformat() for day in dates.values()], "drivers": drivers,
                "turns": {}, "turnDetailIsDummy": True}
    finally:
        workbook.close()


@router.post("/admin/duty/{month}")
def upload_duty(month: str, file: Annotated[UploadFile, File(...)], db: DB, admin: AdminUser) -> dict:
    if not MONTH_RE.fullmatch(month) or not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(422, "YYYY-MM month and .xlsx file required")
    data = file.file.read(get_settings().max_upload_bytes + 1)
    if len(data) > get_settings().max_upload_bytes:
        raise HTTPException(413, "File too large")
    try:
        parsed = parse_duty_xlsx(data, month, file.filename or "schedule.xlsx")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    row = db.get(DutySchedule, month)
    if not row:
        row = DutySchedule(month=month, data=parsed, source_filename=file.filename or "schedule.xlsx")
        db.add(row)
    else:
        row.data = parsed
        row.source_filename = file.filename or "schedule.xlsx"
        row.updated_at = datetime.now(UTC)
    _audit(db, admin.id, "duty.upload", "duty_schedule", month)
    db.commit()
    return {"month": month, "driver_count": len(parsed["drivers"])}


@router.get("/admin/users", response_model=list[UserOut])
def list_users(db: DB, _admin: AdminUser) -> list[User]:
    return list(db.scalars(select(User).where(User.role == "user").order_by(User.created_at.desc())).all())


@router.post("/admin/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: DB, admin: AdminUser) -> User:
    username = normalize_username(payload.username)
    if not USERNAME_RE.fullmatch(username) or username == "test":
        raise HTTPException(422, "Invalid username")
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(409, "Username already exists")
    if not payload.display_name.strip():
        raise HTTPException(422, "Display name is required")
    user = User(username=username, display_name=payload.display_name.strip(),
                password_hash=password_hash.hash(payload.password), role="user", is_active=True)
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Username already exists") from exc
    _audit(db, admin.id, "user.created", "user", user.id)
    db.commit()
    return user


@router.patch("/admin/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, db: DB, admin: AdminUser) -> User:
    user = db.get(User, user_id)
    if not user or user.role != "user":
        raise HTTPException(404, "User not found")
    if payload.display_name is not None:
        if not payload.display_name.strip():
            raise HTTPException(422, "Display name is required")
        user.display_name = payload.display_name.strip()
    if payload.password is not None:
        user.password_hash = password_hash.hash(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None or payload.is_active is False:
        db.execute(update(AuthSession).where(AuthSession.user_id == user.id,
                   AuthSession.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
    _audit(db, admin.id, "user.updated", "user", user.id)
    db.commit()
    return user


@router.get("/admin/users/{user_id}/conversations")
def admin_conversations(user_id: str, db: DB, _admin: AdminUser) -> list[dict]:
    rows = db.scalars(select(ConversationRecord).where(ConversationRecord.user_id == user_id,
                            ConversationRecord.deleted.is_(False)).order_by(ConversationRecord.updated_at.desc())).all()
    return [row.data for row in rows]


@router.delete("/admin/users/{user_id}/conversations/{conversation_id}")
def admin_delete_conversation(user_id: str, conversation_id: str, db: DB, admin: AdminUser) -> dict:
    row = db.get(ConversationRecord, (conversation_id, user_id))
    if not row or row.deleted:
        raise HTTPException(404, "Conversation not found")
    row.deleted, row.data = True, {}
    _audit(db, admin.id, "conversation.deleted", "conversation", conversation_id,
           {"user_id": user_id})
    db.commit()
    return {"status": "ok"}


@router.get("/admin/users/{user_id}/bookmarks")
def admin_bookmarks(user_id: str, db: DB, _admin: AdminUser) -> list[dict]:
    rows = db.scalars(select(BookmarkRecord).where(BookmarkRecord.user_id == user_id,
                            BookmarkRecord.deleted.is_(False)).order_by(BookmarkRecord.updated_at.desc())).all()
    return [{"id": row.id, **row.data} for row in rows]


@router.delete("/admin/users/{user_id}/bookmarks/{bookmark_id}")
def admin_delete_bookmark(user_id: str, bookmark_id: str, db: DB, admin: AdminUser) -> dict:
    row = db.get(BookmarkRecord, (bookmark_id, user_id))
    if not row or row.deleted:
        raise HTTPException(404, "Bookmark not found")
    row.deleted, row.data = True, {}
    _audit(db, admin.id, "bookmark.deleted", "bookmark", bookmark_id,
           {"user_id": user_id})
    db.commit()
    return {"status": "ok"}


@router.get("/admin/feedback")
def list_feedback(db: DB, _admin: AdminUser, limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    rows = db.scalars(select(AuditEvent).where(AuditEvent.action == "chat.feedback")
                      .order_by(AuditEvent.created_at.desc()).limit(limit)).all()
    return [{"id": x.id, "user_id": x.actor, "created_at": x.created_at,
             **x.payload_json} for x in rows]
