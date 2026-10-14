from __future__ import annotations

import hashlib
import json as _json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from datetime import date as date_cls
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import AdminUser, CurrentUser
from .config import get_settings
from .db import get_db
from .duty import dia_data, load_duty, table_key_for_turn
from .models import (
    DutyOverride,
    EduVideo,
    EmergencyContact,
    ExchangePost,
    ExchangeVolunteer,
    GameScore,
    HazardComment,
    HazardReport,
    LifeMenu,
    SafetyAlert,
    SafetyTip,
    StandbyCoverage,
    VoiceReply,
    VoiceThread,
)

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]

# ──────────────── helpers ────────────────

def _audit(db: Session, actor: str, action: str, entity_type: str, entity_id: str,
           payload: dict | None = None) -> None:
    from .models import AuditEvent
    db.add(AuditEvent(actor=actor, action=action, entity_type=entity_type,
                      entity_id=entity_id, payload_json=payload or {}))


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
Short = Annotated[str, Field(max_length=200)]
Long = Annotated[str, Field(max_length=4000)]


def _check_date(value: str) -> str:
    try:
        if DATE_RE.fullmatch(value) and date_cls.fromisoformat(value):
            return value
    except ValueError:
        pass
    raise HTTPException(422, "날짜는 YYYY-MM-DD 형식이어야 합니다")


def _owner_hash(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()


# ──────────────── § 1  Exchange ────────────────

class ExchangeCreate(BaseModel):
    type: Literal["direct", "open"]
    target_name: Short | None = None
    dates: list[str] = Field(min_length=1, max_length=7)
    requester_dias: list[Short] = Field(default_factory=list, max_length=7)
    target_dias: list[Short] | None = Field(default=None, max_length=7)
    memo: Long | None = None


class ExchangeRespond(BaseModel):
    action: Literal["accept", "decline"]
    reason: Long | None = None


def _volunteer_out(v: ExchangeVolunteer) -> dict:
    return {"id": v.id, "person_name": v.person_name, "status": v.status,
            "created_at": v.created_at.isoformat()}


def _post_out(post: ExchangePost, volunteers: list[ExchangeVolunteer], me: str, db: Session) -> dict:
    is_mine = (post.requester_name == me or post.target_name == me or
               any(v.person_name == me for v in volunteers))
    return {
        "id": post.id, "type": post.type, "status": post.status,
        "requester_name": post.requester_name,
        "target_name": post.target_name, "dates": post.dates,
        "requester_dias": post.requester_dias,
        "target_dias": post.target_dias, "memo": post.memo,
        "decline_reason": post.decline_reason,
        "accepted_volunteer_id": post.accepted_volunteer_id,
        "revert_of": post.revert_of,
        "applied": db.scalar(select(DutyOverride.id).where(DutyOverride.post_id == post.id).limit(1)) is not None,
        "volunteers": [_volunteer_out(v) for v in volunteers],
        "created_at": post.created_at.isoformat(), "mine": is_mine,
    }


def _post_partner(db: Session, post: ExchangePost) -> str | None:
    if post.target_name:
        return post.target_name
    volunteer = db.get(ExchangeVolunteer, post.accepted_volunteer_id) if post.accepted_volunteer_id else None
    return volunteer.person_name if volunteer else None


def _effective_code(db: Session, name: str, day: str, cache: dict[str, dict | None]) -> str | None:
    month = day[:7]
    if month not in cache:
        cache[month] = load_duty(db, month)
    schedule = cache[month]
    driver = next((item for item in schedule["drivers"] if item["name"] == name), None) if schedule else None
    cell = driver and driver["days"].get(day)
    return cell.get("code") if cell else None


def _apply_swap(db: Session, post: ExchangePost, partner: str) -> None:
    cache: dict[str, dict | None] = {}
    if post.revert_of:
        original = db.get(ExchangePost, post.revert_of)
        original_partner = _post_partner(db, original) if original else None
        participants = {original.requester_name, original_partner} if original and original_partner else set()
        if not original or original.status != "accepted" or participants != {post.requester_name, partner} or not db.scalar(
            select(DutyOverride.id).where(DutyOverride.post_id == post.revert_of).limit(1)
        ):
            raise HTTPException(409, "원본 교체를 되돌릴 수 없습니다")
        active = list(db.scalars(select(DutyOverride).where(
            DutyOverride.post_id == original.id, DutyOverride.active.is_(True))).all())
        expected = {(name, day) for day in post.dates for name in (original.requester_name, original_partner)}
        if len(active) != len(expected) or {(row.driver_name, row.date) for row in active} != expected:
            raise HTTPException(409, "원본 교체가 이미 변경되어 되돌릴 수 없습니다")

    snapshots = []
    for index, day in enumerate(post.dates):
        requester_code = _effective_code(db, post.requester_name, day, cache)
        target_code = _effective_code(db, partner, day, cache)
        if not requester_code or not target_code:
            if not post.revert_of and not any(cache.values()) and not post.requester_dias and not post.target_dias:
                return  # shortcut: accepts remain unapplied with no roster, require a duty upload to exchange codes.
            raise HTTPException(409, "근무가 이미 바뀌어 교체할 수 없습니다")
        if index < len(post.requester_dias) and post.requester_dias[index] and requester_code != post.requester_dias[index]:
            raise HTTPException(409, "근무가 이미 바뀌어 교체할 수 없습니다")
        if index < len(post.target_dias) and post.target_dias[index] and target_code != post.target_dias[index]:
            raise HTTPException(409, "근무가 이미 바뀌어 교체할 수 없습니다")
        snapshots.append((day, requester_code, target_code))

    for day, requester_code, target_code in snapshots:
        active = db.scalars(select(DutyOverride).where(
            DutyOverride.date == day, DutyOverride.active.is_(True),
            DutyOverride.driver_name.in_((post.requester_name, partner)))).all()
        for row in active:
            row.active = False
        db.add(DutyOverride(driver_name=post.requester_name, date=day, code=target_code,
                            original_code=requester_code, post_id=post.id, active=True))
        db.add(DutyOverride(driver_name=partner, date=day, code=requester_code,
                            original_code=target_code, post_id=post.id, active=True))


@router.get("/exchange/posts")
def list_exchange_posts(db: DB, user: CurrentUser,
                        status: str | None = None, mine: bool = False) -> list[dict]:
    q = select(ExchangePost).order_by(ExchangePost.created_at.desc())
    if status:
        q = q.where(ExchangePost.status == status)
    posts = list(db.scalars(q).all())
    out = []
    for p in posts:
        vols = list(db.scalars(select(ExchangeVolunteer).where(
            ExchangeVolunteer.post_id == p.id)).all())
        d = _post_out(p, vols, user.display_name, db)
        if mine and not d["mine"]:
            continue
        out.append(d)
    return out


@router.post("/exchange/posts", status_code=201)
def create_exchange_post(payload: ExchangeCreate, db: DB, user: CurrentUser) -> dict:
    for d in payload.dates:
        _check_date(d)
    if len(set(payload.dates)) != len(payload.dates):
        raise HTTPException(422, "dates must be unique")
    if payload.type == "direct":
        if not payload.target_name:
            raise HTTPException(422, "direct type requires target_name")
        if payload.target_name == user.display_name:
            raise HTTPException(422, "자기 자신과 교체할 수 없습니다")
    if not (1 <= len(payload.dates) <= 7):
        raise HTTPException(422, "dates must be 1~7")
    post = ExchangePost(
        type=payload.type, requester_name=user.display_name,
        target_name=payload.target_name if payload.type == "direct" else None,
        dates=payload.dates, requester_dias=payload.requester_dias,
        target_dias=payload.target_dias or [], memo=payload.memo,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_out(post, [], user.display_name, db)


@router.post("/exchange/posts/{post_id}/respond")
def respond_exchange(post_id: str, payload: ExchangeRespond, db: DB, user: CurrentUser) -> dict:
    post = db.get(ExchangePost, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.status != "open":
        raise HTTPException(409, "Post is not open")
    if post.type != "direct":
        raise HTTPException(422, "공개 교체글은 지원자를 수락하세요")
    if post.target_name != user.display_name:
        raise HTTPException(403, "대상자만 응답할 수 있습니다")
    if payload.action == "accept":
        _apply_swap(db, post, post.target_name)
        post.status = "accepted"
    else:
        post.status = "declined"
        post.decline_reason = payload.reason
    db.commit()
    db.refresh(post)
    vols = list(db.scalars(select(ExchangeVolunteer).where(
        ExchangeVolunteer.post_id == post.id)).all())
    return _post_out(post, vols, user.display_name, db)


@router.post("/exchange/posts/{post_id}/volunteers", status_code=201)
def volunteer_exchange(post_id: str, db: DB, user: CurrentUser) -> dict:
    post = db.get(ExchangePost, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.type != "open":
        raise HTTPException(422, "open 타입만 지원 가능합니다")
    if post.status != "open":
        raise HTTPException(409, "Post is not open")
    if post.requester_name == user.display_name:
        raise HTTPException(403, "요청자는 지원할 수 없습니다")
    existing = db.scalar(select(ExchangeVolunteer).where(
        ExchangeVolunteer.post_id == post_id,
        ExchangeVolunteer.person_name == user.display_name))
    if existing:
        raise HTTPException(409, "이미 지원했습니다")
    vol = ExchangeVolunteer(post_id=post_id, person_name=user.display_name)
    db.add(vol)
    db.commit()
    db.refresh(vol)
    return _volunteer_out(vol)


@router.post("/exchange/posts/{post_id}/volunteers/{vid}/accept")
def accept_volunteer(post_id: str, vid: str, db: DB, user: CurrentUser) -> dict:
    post = db.get(ExchangePost, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.requester_name != user.display_name:
        raise HTTPException(403, "요청자만 수락할 수 있습니다")
    if post.status != "open":
        raise HTTPException(409, "Post is not open")
    vol = db.get(ExchangeVolunteer, vid)
    if not vol or vol.post_id != post_id:
        raise HTTPException(404, "Volunteer not found")
    _apply_swap(db, post, vol.person_name)
    post.status = "accepted"
    post.accepted_volunteer_id = vid
    vol.status = "accepted"
    for other in db.scalars(select(ExchangeVolunteer).where(
            ExchangeVolunteer.post_id == post_id, ExchangeVolunteer.id != vid)).all():
        other.status = "rejected"
    db.commit()
    db.refresh(post)
    vols = list(db.scalars(select(ExchangeVolunteer).where(
        ExchangeVolunteer.post_id == post.id)).all())
    return _post_out(post, vols, user.display_name, db)


@router.post("/exchange/posts/{post_id}/revert", status_code=201)
def revert_exchange(post_id: str, db: DB, user: CurrentUser) -> dict:
    post = db.get(ExchangePost, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    partner = _post_partner(db, post)
    if post.status != "accepted" or not db.scalar(
        select(DutyOverride.id).where(DutyOverride.post_id == post.id).limit(1)
    ):
        raise HTTPException(409, "적용된 교체만 되돌릴 수 있습니다")
    if user.display_name not in {post.requester_name, partner}:
        raise HTTPException(403, "교체 당사자만 되돌릴 수 있습니다")
    other = partner if user.display_name == post.requester_name else post.requester_name
    cache: dict[str, dict | None] = {}
    requester_dias, target_dias = [], []
    for day in post.dates:
        requester_dias.append(_effective_code(db, user.display_name, day, cache) or "")
        target_dias.append(_effective_code(db, other, day, cache) or "")
    revert = ExchangePost(type="direct", status="open", requester_name=user.display_name,
                          target_name=other, dates=post.dates, requester_dias=requester_dias,
                          target_dias=target_dias, revert_of=post.id)
    db.add(revert)
    db.commit()
    db.refresh(revert)
    return _post_out(revert, [], user.display_name, db)


@router.delete("/exchange/posts/{post_id}")
def cancel_exchange(post_id: str, db: DB, user: CurrentUser) -> dict:
    post = db.get(ExchangePost, post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.requester_name != user.display_name and user.role != "admin":
        raise HTTPException(403, "요청자 또는 관리자만 취소할 수 있습니다")
    if post.status != "open" and user.role != "admin":
        raise HTTPException(409, "이미 성사·거절된 교체는 취소할 수 없습니다")
    post.status = "cancelled"
    db.commit()
    return {"status": "ok"}


@router.get("/exchange/match")
def exchange_match(date: str, db: DB, user: CurrentUser,
                   kind: str | None = None) -> list[dict]:
    date = _check_date(date)
    sched = load_duty(db, date[:7])
    if not sched:
        return []
    swapped = set(db.scalars(select(DutyOverride.driver_name).where(
        DutyOverride.date == date, DutyOverride.active.is_(True))).all())
    results = []
    for driver in sched.get("drivers", []):
        if driver["name"] == user.display_name:
            continue
        day_data = driver.get("days", {}).get(date)
        if not day_data:
            continue
        if kind and day_data.get("type") != kind:
            continue
        results.append({"name": driver["name"], "code": day_data.get("code", ""),
                        "type": day_data.get("type", ""), "turnKey": day_data.get("turnKey"),
                        "swapped": driver["name"] in swapped})
    return results


# ──────────────── § 2  Standby Coverage ────────────────

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


@router.get("/standby-coverage")
def list_standby(db: DB, user: CurrentUser, date: str | None = None) -> list[dict]:
    q = select(StandbyCoverage).where(StandbyCoverage.deleted_at.is_(None))
    if date:
        q = q.where(StandbyCoverage.date == _check_date(date))
    q = q.order_by(StandbyCoverage.created_at.desc()).limit(50)
    return [{"id": r.id, "date": r.date, "uploader_name": r.uploader_name,
             "created_at": r.created_at.isoformat(), "mine": r.uploader_id == user.id,
             "image_url": f"/api/standby-coverage/{r.id}/image"} for r in db.scalars(q).all()]


@router.post("/standby-coverage", status_code=201)
def upload_standby(date: Annotated[str, Form()],
                   file: Annotated[UploadFile, File(...)],
                   db: DB, user: CurrentUser) -> dict:
    _check_date(date)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(415, "jpg/png/webp만 허용됩니다")
    data = file.file.read(MAX_IMAGE_SIZE + 1)
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "10MB 이하만 가능합니다")
    settings = get_settings()
    dest = Path(settings.storage_root) / "standby" / date
    dest.mkdir(parents=True, exist_ok=True)
    from .models import new_id
    fid = new_id()
    fpath = dest / f"{fid}{ext}"
    fpath.write_bytes(data)
    row = StandbyCoverage(date=date, uploader_name=user.display_name,
                          uploader_id=user.id, file_path=str(fpath))
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "date": row.date, "uploader_name": row.uploader_name,
            "created_at": row.created_at.isoformat(), "mine": True,
            "image_url": f"/api/standby-coverage/{row.id}/image"}


@router.get("/standby-coverage/{item_id}/image")
def get_standby_image(item_id: str, db: DB, _user: CurrentUser) -> FileResponse:
    row = db.get(StandbyCoverage, item_id)
    if not row or row.deleted_at:
        raise HTTPException(404, "Not found")
    return FileResponse(row.file_path)


@router.delete("/standby-coverage/{item_id}")
def delete_standby(item_id: str, db: DB, user: CurrentUser) -> dict:
    row = db.get(StandbyCoverage, item_id)
    if not row or row.deleted_at:
        raise HTTPException(404, "Not found")
    if row.uploader_id != user.id and user.role != "admin":
        raise HTTPException(403, "올린 사람 또는 관리자만 삭제 가능합니다")
    row.deleted_at = datetime.now(UTC)
    db.commit()
    return {"status": "ok"}


# ──────────────── § 3  Safety ────────────────

class AlertCreate(BaseModel):
    station_from: Short = ""
    station_to: Short = ""
    direction: Literal["up", "down"] | None = None
    message: Annotated[str, Field(min_length=1, max_length=1000)]
    severity: Literal["info", "warning", "danger"] = "info"
    expires_at: datetime | None = None


@router.get("/alerts")
def list_alerts(db: DB, _user: CurrentUser) -> list[dict]:
    now = datetime.now(UTC)
    rows = db.scalars(select(SafetyAlert).where(
        SafetyAlert.is_active.is_(True))).all()
    out = []
    for r in rows:
        if r.expires_at and r.expires_at.replace(tzinfo=UTC if r.expires_at.tzinfo is None else r.expires_at.tzinfo) < now:
            continue
        out.append({"id": r.id, "station_from": r.station_from, "station_to": r.station_to,
                    "direction": r.direction, "message": r.message, "severity": r.severity,
                    "created_by": r.created_by, "created_at": r.created_at.isoformat(),
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None})
    return out


@router.post("/alerts", status_code=201)
def create_alert(payload: AlertCreate, db: DB, admin: AdminUser) -> dict:
    exp = payload.expires_at
    row = SafetyAlert(station_from=payload.station_from, station_to=payload.station_to,
                      direction=payload.direction, message=payload.message,
                      severity=payload.severity, created_by=admin.display_name, expires_at=exp)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "station_from": row.station_from, "station_to": row.station_to,
            "direction": row.direction, "message": row.message, "severity": row.severity,
            "created_by": row.created_by, "created_at": row.created_at.isoformat(),
            "expires_at": row.expires_at.isoformat() if row.expires_at else None}


@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: str, db: DB, _admin: AdminUser) -> dict:
    row = db.get(SafetyAlert, alert_id)
    if not row:
        raise HTTPException(404, "Alert not found")
    row.is_active = False
    db.commit()
    return {"status": "ok"}


# ── hazard ──

class HazardCreate(BaseModel):
    category: Literal["hazard", "action", "inspect"]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(min_length=1, max_length=4000)]
    location: Short | None = None


class HazardStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


@router.get("/safety/hazards")
def list_hazards(db: DB, _user: CurrentUser, category: str | None = None) -> list[dict]:
    q = select(HazardReport).order_by(HazardReport.created_at.desc())
    if category:
        q = q.where(HazardReport.category == category)
    rows = db.scalars(q).all()
    out = []
    for r in rows:
        cnt = db.scalar(select(func.count(HazardComment.id)).where(
            HazardComment.hazard_id == r.id)) or 0
        out.append({"id": r.id, "category": r.category, "title": r.title,
                    "description": r.description, "location": r.location,
                    "status": r.status, "author_name": r.author_name,
                    "created_at": r.created_at.isoformat(), "comment_count": cnt})
    return out


@router.get("/safety/hazards/{hazard_id}")
def get_hazard(hazard_id: str, db: DB, _user: CurrentUser) -> dict:
    r = db.get(HazardReport, hazard_id)
    if not r:
        raise HTTPException(404, "Hazard not found")
    comments = db.scalars(select(HazardComment).where(
        HazardComment.hazard_id == hazard_id).order_by(HazardComment.created_at)).all()
    cnt = len(comments)
    return {"id": r.id, "category": r.category, "title": r.title,
            "description": r.description, "location": r.location,
            "status": r.status, "author_name": r.author_name,
            "created_at": r.created_at.isoformat(), "comment_count": cnt,
            "comments": [{"id": c.id, "author_name": c.author_name,
                          "content": c.content, "created_at": c.created_at.isoformat()}
                         for c in comments]}


@router.post("/safety/hazards", status_code=201)
def create_hazard(payload: HazardCreate, db: DB, user: CurrentUser) -> dict:
    row = HazardReport(category=payload.category, title=payload.title,
                       description=payload.description, location=payload.location,
                       author_name=user.display_name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "category": row.category, "title": row.title,
            "description": row.description, "location": row.location,
            "status": row.status, "author_name": row.author_name,
            "created_at": row.created_at.isoformat(), "comment_count": 0}


@router.post("/safety/hazards/{hazard_id}/comments", status_code=201)
def create_hazard_comment(hazard_id: str, payload: CommentCreate, db: DB,
                          user: CurrentUser) -> dict:
    if not db.get(HazardReport, hazard_id):
        raise HTTPException(404, "Hazard not found")
    c = HazardComment(hazard_id=hazard_id, author_name=user.display_name,
                      content=payload.content)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "author_name": c.author_name, "content": c.content,
            "created_at": c.created_at.isoformat()}


@router.patch("/safety/hazards/{hazard_id}")
def update_hazard_status(hazard_id: str, payload: HazardStatusUpdate, db: DB,
                         _admin: AdminUser) -> dict:
    r = db.get(HazardReport, hazard_id)
    if not r:
        raise HTTPException(404, "Hazard not found")
    r.status = payload.status
    db.commit()
    db.refresh(r)
    return {"id": r.id, "status": r.status}


# ── safety tips ──

class TipCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Long = ""
    media_url: Annotated[str, Field(max_length=1000)] | None = None


@router.get("/safety/tips")
def list_tips(db: DB, _user: CurrentUser) -> list[dict]:
    rows = db.scalars(select(SafetyTip).order_by(SafetyTip.created_at.desc())).all()
    return [{"id": r.id, "title": r.title, "description": r.description,
             "media_url": r.media_url, "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/safety/tips", status_code=201)
def create_tip(payload: TipCreate, db: DB, _admin: AdminUser) -> dict:
    row = SafetyTip(title=payload.title, description=payload.description,
                    media_url=payload.media_url)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "title": row.title, "description": row.description,
            "media_url": row.media_url, "created_at": row.created_at.isoformat()}


@router.delete("/safety/tips/{tip_id}")
def delete_tip(tip_id: str, db: DB, _admin: AdminUser) -> dict:
    row = db.get(SafetyTip, tip_id)
    if not row:
        raise HTTPException(404, "Tip not found")
    db.delete(row)
    db.commit()
    return {"status": "ok"}


# ──────────────── § 4  Voice (anonymous) ────────────────

class VoiceCreate(BaseModel):
    content: str = Field(min_length=5, max_length=1000)


class ReplyCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


@router.get("/voice")
def list_voice(db: DB, user: CurrentUser) -> list[dict]:
    oh = _owner_hash(user.id)
    threads = db.scalars(select(VoiceThread).where(
        VoiceThread.owner_hash == oh).order_by(VoiceThread.created_at.desc())).all()
    out = []
    for t in threads:
        replies = db.scalars(select(VoiceReply).where(
            VoiceReply.thread_id == t.id).order_by(VoiceReply.created_at)).all()
        out.append({"id": t.id, "content": t.content,
                    "created_at": t.created_at.isoformat(),
                    "replies": [{"id": r.id, "content": r.content,
                                 "from_admin": r.from_admin,
                                 "created_at": r.created_at.isoformat()} for r in replies]})
    return out


@router.post("/voice", status_code=201)
def create_voice(payload: VoiceCreate, db: DB, user: CurrentUser) -> dict:
    oh = _owner_hash(user.id)
    cutoff = datetime.now(UTC) - timedelta(minutes=10)
    recent = db.scalar(select(func.count(VoiceThread.id)).where(
        VoiceThread.owner_hash == oh, VoiceThread.created_at >= cutoff))
    if (recent or 0) >= 5:
        raise HTTPException(429, "10분에 5건까지만 작성할 수 있습니다")
    t = VoiceThread(owner_hash=oh, content=payload.content)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "content": t.content, "created_at": t.created_at.isoformat(),
            "replies": []}


@router.post("/voice/{thread_id}/replies", status_code=201)
def create_voice_reply(thread_id: str, payload: ReplyCreate, db: DB,
                       user: CurrentUser) -> dict:
    t = db.get(VoiceThread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    oh = _owner_hash(user.id)
    if t.owner_hash != oh and user.role != "admin":
        raise HTTPException(403, "본인 스레드 또는 관리자만 답글 가능합니다")
    r = VoiceReply(thread_id=thread_id, content=payload.content,
                   from_admin=user.role == "admin")
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "content": r.content, "from_admin": r.from_admin,
            "created_at": r.created_at.isoformat()}


@router.get("/admin/voice")
def admin_list_voice(db: DB, _admin: AdminUser) -> list[dict]:
    threads = db.scalars(select(VoiceThread).order_by(
        VoiceThread.created_at.desc())).all()
    out = []
    for t in threads:
        replies = db.scalars(select(VoiceReply).where(
            VoiceReply.thread_id == t.id).order_by(VoiceReply.created_at)).all()
        out.append({"id": t.id, "content": t.content,
                    "created_at": t.created_at.isoformat(),
                    "replies": [{"id": r.id, "content": r.content,
                                 "from_admin": r.from_admin,
                                 "created_at": r.created_at.isoformat()} for r in replies]})
    return out


# ──────────────── § 5  Life & Info ────────────────

# ── news cache ──
_news_cache: dict[str, Any] = {"items": [], "ts": 0.0}
_NEWS_TTL = 600  # 10 min


@router.get("/news")
def get_news(_user: CurrentUser) -> list[dict]:
    now = time.time()
    if now - _news_cache["ts"] < _NEWS_TTL and _news_cache["items"]:
        return _news_cache["items"]
    try:
        url = "https://news.google.com/rss/search?q=%EC%84%9C%EC%9A%B8%EA%B5%90%ED%86%B5%EA%B3%B5%EC%82%AC+6%ED%98%B8%EC%84%A0&hl=ko&gl=KR&ceid=KR:ko"
        with urllib.request.urlopen(url, timeout=10) as resp:
            root = ET.fromstring(resp.read())
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            source = item.findtext("source", "")
            try:
                published = parsedate_to_datetime(item.findtext("pubDate", "")).isoformat()
            except (TypeError, ValueError):
                published = ""
            items.append({"title": title, "link": link, "source": source,
                          "published": published})
        _news_cache["items"] = items
        _news_cache["ts"] = now
        return items
    except (OSError, ValueError, ET.ParseError):
        return _news_cache["items"] or []


# ── life menu ──

@router.get("/life/menu")
def list_menus(db: DB, _user: CurrentUser) -> list[dict]:
    rows = db.scalars(select(LifeMenu).order_by(LifeMenu.created_at.desc())).all()
    return [{"id": r.id, "week": r.week, "filename": r.filename,
             "created_at": r.created_at.isoformat(),
             "url": f"/api/life/menu/{r.id}/file"} for r in rows]


@router.post("/life/menu", status_code=201)
def upload_menu(week: Annotated[str, Form()],
                file: Annotated[UploadFile, File(...)],
                db: DB, _admin: AdminUser) -> dict:
    settings = get_settings()
    if Path(file.filename or "").suffix.lower() not in ALLOWED_IMAGE_EXT | {".pdf"}:
        raise HTTPException(415, "이미지(jpg/png/webp) 또는 PDF만 허용됩니다")
    if not re.fullmatch(r"\d{4}-W\d{2}", week):
        raise HTTPException(422, "주차는 2026-W41 형식이어야 합니다")
    data = file.file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "File too large")
    dest = Path(settings.storage_root) / "menu"
    dest.mkdir(parents=True, exist_ok=True)
    from .models import new_id
    fname = file.filename or "menu"
    ext = Path(fname).suffix
    fpath = dest / f"{new_id()}{ext}"
    fpath.write_bytes(data)
    # replace same week
    existing = db.scalar(select(LifeMenu).where(LifeMenu.week == week))
    if existing:
        Path(existing.file_path).unlink(missing_ok=True)
        db.delete(existing)
    row = LifeMenu(week=week, filename=fname, file_path=str(fpath))
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "week": row.week, "filename": row.filename,
            "created_at": row.created_at.isoformat(),
            "url": f"/api/life/menu/{row.id}/file"}


@router.get("/life/menu/{menu_id}/file")
def get_menu_file(menu_id: str, db: DB, _user: CurrentUser) -> FileResponse:
    row = db.get(LifeMenu, menu_id)
    if not row:
        raise HTTPException(404, "Menu not found")
    return FileResponse(row.file_path, filename=row.filename)


# ── contacts ──

@router.get("/contacts")
def get_contacts(db: DB, _user: CurrentUser) -> list[dict]:
    row = db.scalars(select(EmergencyContact).limit(1)).first()
    return row.data if row else []


class Contact(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    phone: Annotated[str, Field(min_length=1, max_length=40)]
    group: Annotated[str, Field(max_length=100)] = ""


@router.put("/contacts")
def set_contacts(contacts: Annotated[list[Contact], Field(max_length=200)], db: DB,
                 _admin: AdminUser) -> list[dict]:
    payload = [c.model_dump() for c in contacts]
    row = db.scalars(select(EmergencyContact).limit(1)).first()
    if not row:
        row = EmergencyContact(data=payload)
        db.add(row)
    else:
        row.data = payload
    db.commit()
    return payload


# ── edu videos ──

class VideoCreate(BaseModel):
    category: Annotated[str, Field(min_length=1, max_length=100)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    url: Annotated[str, Field(pattern=r"^https?://", max_length=1000)]


@router.get("/edu/videos")
def list_videos(db: DB, _user: CurrentUser) -> list[dict]:
    rows = db.scalars(select(EduVideo).order_by(EduVideo.created_at.desc())).all()
    return [{"id": r.id, "category": r.category, "title": r.title,
             "url": r.url, "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/edu/videos", status_code=201)
def create_video(payload: VideoCreate, db: DB, _admin: AdminUser) -> dict:
    row = EduVideo(category=payload.category, title=payload.title, url=payload.url)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "category": row.category, "title": row.title,
            "url": row.url, "created_at": row.created_at.isoformat()}


@router.delete("/edu/videos/{video_id}")
def delete_video(video_id: str, db: DB, _admin: AdminUser) -> dict:
    row = db.get(EduVideo, video_id)
    if not row:
        raise HTTPException(404, "Video not found")
    db.delete(row)
    db.commit()
    return {"status": "ok"}


# ── realtime trains ──
_train_cache: dict[str, Any] = {"items": [], "ts": 0.0}
_TRAIN_TTL = 20
_SEOUL = ZoneInfo("Asia/Seoul")
_LINE6_STATIONS = [
    "응암", "역촌", "불광", "독바위", "연신내", "구산", "새절", "증산", "디지털미디어시티",
    "월드컵경기장", "마포구청", "망원", "합정", "상수", "광흥창", "대흥", "공덕",
    "효창공원앞", "삼각지", "녹사평", "이태원", "한강진", "버티고개", "약수", "청구",
    "신당", "동묘앞", "창신", "보문", "안암", "고려대", "월곡", "상월곡", "돌곶이",
    "석계", "태릉입구", "화랑대", "봉화산", "신내",
]
_UNMATCHED_CREW = "신내사업소"


@lru_cache(maxsize=1)
def _train_segments() -> dict:
    return _json.loads((Path(__file__).parent / "data" / "dia-train-segments.json").read_text(encoding="utf-8"))["segments"]


def _mock_trains(now: datetime) -> list[dict]:
    received = (now - timedelta(seconds=18)).strftime("%Y-%m-%d %H:%M:%S")
    mock = [("6101", "망원", "down", "출발", "신내"), ("6102", "합정", "up", "출발", "응암"),
            ("6103", "버티고개", "down", "출발", "신내"), ("6104", "약수", "up", "출발", "응암"),
            ("6105", "돌곶이", "down", "출발", "신내"), ("6106", "석계", "up", "출발", "응암"),
            ("6107", "공덕", "down", "도착", "신내"), ("6108", "봉화산", "up", "도착", "응암")]
    return [{"train_no": train, "station": station, "direction": direction, "status": status,
             "terminal": terminal, "updated_at": received}
            for train, station, direction, status, terminal in mock]


def _station_index(name: str) -> int:
    normalized = re.sub(r"\s*\(.*\)\s*$", "", name).strip()
    try:
        return _LINE6_STATIONS.index(normalized)
    except ValueError:
        return 1_000_000


def _crew_for_train(train: dict, active: list[dict]) -> tuple[str, str | None]:
    direction = {"up": "eungam", "down": "sinnae"}.get(train["direction"], train["direction"])
    station = _station_index(train["station"])
    matches = []
    for segment in active:
        start, end = _station_index(segment["startStation"]), _station_index(segment["endStation"])
        if segment["trainNumber"] == str(train["train_no"]) and segment["direction"] == direction \
                and max(station, start, end) < 1_000_000 and min(start, end) <= station <= max(start, end):
            matches.append(segment)
    if not matches:
        return _UNMATCHED_CREW, None
    at_boundary = train["status"] in {"도착", "출발"}
    boundary = next((segment for segment in matches
                     if _station_index(segment["startStation"] if at_boundary else segment["endStation"]) == station), None)
    selected = boundary or matches[0]
    return selected["profileName"], selected["turnKey"]


def _active_train_segments(db: Session, now: datetime) -> list[dict]:
    now = now.replace(tzinfo=_SEOUL) if now.tzinfo is None else now.astimezone(_SEOUL)
    pack, segment_pack, active = dia_data(), _train_segments(), []
    for duty_date in (now.date() - timedelta(days=1), now.date()):
        day = duty_date.isoformat()
        schedule = load_duty(db, day[:7])
        if not schedule:
            continue
        for driver in schedule["drivers"]:
            cell = driver["days"].get(day)
            turn_key = cell and cell.get("turnKey")
            table_key = table_key_for_turn(turn_key)
            if not cell or not table_key:
                continue
            code = cell["code"]
            detail = pack["schedules"].get(table_key, {}).get(code, {})
            start_text, end_text = detail.get("startTime"), detail.get("endTime")
            start_match = re.fullmatch(r"(\d{1,2}):(\d{2})", start_text or "")
            end_match = re.fullmatch(r"(\d{1,2}):(\d{2})", end_text or "")
            if not start_match or not end_match:
                continue
            start = datetime.combine(duty_date, datetime.min.time(), _SEOUL).replace(
                hour=int(start_match[1]), minute=int(start_match[2]))
            end = datetime.combine(duty_date, datetime.min.time(), _SEOUL).replace(
                hour=int(end_match[1]), minute=int(end_match[2]))
            if end <= start:
                end += timedelta(days=1)
            if not start <= now <= end:
                continue
            for segment in segment_pack.get(table_key, {}).get(code, []):
                active.append({**segment, "profileName": driver["name"], "turnKey": turn_key})
    return active


def _with_train_crews(items: list[dict], db: Session, now: datetime) -> list[dict]:
    active = _active_train_segments(db, now)
    return [{**item, "crew_name": (match := _crew_for_train(item, active))[0], "crew_turn": match[1]}
            for item in items]


def _empty_train_result(data: dict) -> tuple[bool, str]:
    result = data.get("errorMessage") or data.get("RESULT")
    if not result:
        return False, ""
    if isinstance(result, dict):
        code = str(result.get("code") or result.get("CODE") or result.get("status") or "")
        message = str(result.get("message") or result.get("MESSAGE") or result.get("msg") or result.get("MSG") or code)
    else:
        message = str(result)
        code = re.search(r"INFO-\d+", message)
        code = code.group(0) if code else ""
    if code == "INFO-200" or "INFO-200" in message or "해당하는 데이터가 없습니다" in message:
        return True, message
    return False, message


@router.get("/realtime/trains")
def realtime_trains(_user: CurrentUser, db: DB) -> list[dict]:
    settings = get_settings()
    now = datetime.now(_SEOUL)
    if settings.realtime_trains_mock:
        return _with_train_crews(_mock_trains(now), db, now)
    key = settings.seoul_subway_api_key
    if not key:
        raise HTTPException(503, "실시간 열차 API 키가 설정되지 않았습니다")
    timestamp = time.time()
    if timestamp - _train_cache["ts"] < _TRAIN_TTL and _train_cache["items"]:
        return _with_train_crews(_train_cache["items"], db, now)
    try:
        url = f"http://swopenapi.seoul.go.kr/api/subway/{key}/json/realtimePosition/0/100/6호선"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read())
        if not isinstance(data, dict):
            raise TypeError("Invalid Seoul realtime train response")
        if "realtimePositionList" not in data:
            empty, message = _empty_train_result(data)
            if not empty and message:
                if not _train_cache["items"]:
                    raise HTTPException(502, message)
                return _with_train_crews(_train_cache["items"], db, now)
            if empty:
                _train_cache["items"] = []
                _train_cache["ts"] = timestamp
                return []
        status_map = {"0": "진입", "1": "도착", "2": "출발", "3": "전역출발", "4": "전역진입", "5": "전역도착", "99": "운행중"}
        items = []
        for t in data.get("realtimePositionList", []):
            direction = "up" if str(t.get("updnLine")) == "0" else "down"
            st = status_map.get(str(t.get("trainSttus", "")), "운행중")
            items.append({"train_no": t.get("trainNo", ""), "station": t.get("statnNm", ""),
                          "direction": direction, "status": st,
                          "terminal": t.get("statnTnm", ""),
                          "updated_at": t.get("recptnDt", "")})
        _train_cache["items"] = items
        _train_cache["ts"] = timestamp
        return _with_train_crews(items, db, now)
    except HTTPException:
        raise
    except (OSError, TypeError, ValueError):
        return _with_train_crews(_train_cache["items"] or [], db, now)


# ── games ──

class ScoreCreate(BaseModel):
    game: str
    score: int


VALID_GAMES = {"reaction", "math", "color"}


@router.post("/games/scores", status_code=201)
def post_score(payload: ScoreCreate, db: DB, user: CurrentUser) -> dict:
    if payload.game not in VALID_GAMES:
        raise HTTPException(422, "game must be reaction, math, or color")
    row = GameScore(game=payload.game, player_name=user.display_name,
                    score=payload.score)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "game": row.game, "name": row.player_name,
            "score": row.score, "created_at": row.created_at.isoformat()}


@router.get("/games/scores")
def get_scores(db: DB, _user: CurrentUser, game: str | None = None) -> list[dict]:
    if not game:
        raise HTTPException(422, "game query parameter required")
    if game not in VALID_GAMES:
        raise HTTPException(422, "game must be reaction, math, or color")
    # best score per person, top 20
    if game == "reaction":
        # lower is better
        sub = select(
            GameScore.player_name,
            func.min(GameScore.score).label("best"),
            func.max(GameScore.created_at).label("latest"),
        ).where(GameScore.game == game).group_by(GameScore.player_name).subquery()
        rows = db.execute(
            select(sub.c.player_name, sub.c.best, sub.c.latest)
            .order_by(sub.c.best.asc()).limit(20)
        ).all()
    else:
        # higher is better
        sub = select(
            GameScore.player_name,
            func.max(GameScore.score).label("best"),
            func.max(GameScore.created_at).label("latest"),
        ).where(GameScore.game == game).group_by(GameScore.player_name).subquery()
        rows = db.execute(
            select(sub.c.player_name, sub.c.best, sub.c.latest)
            .order_by(sub.c.best.desc()).limit(20)
        ).all()
    return [{"name": r[0], "score": r[1],
             "created_at": r[2].isoformat() if hasattr(r[2], 'isoformat') else str(r[2])}
            for r in rows]
