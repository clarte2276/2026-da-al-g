from __future__ import annotations

import json
import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .auth import CurrentUser
from .config import get_settings
from .db import SessionLocal, get_db
from .models import DeviceToken, User

router = APIRouter(prefix="/api/push")
logger = logging.getLogger(__name__)
_credentials = None
_missing_config_logged = False


class TokenBody(BaseModel):
    token: Annotated[str, Field(min_length=1)]


@router.post("/token")
def register_token(payload: TokenBody, user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> dict:
    row = db.scalar(select(DeviceToken).where(DeviceToken.token == payload.token))
    if row:
        row.user_id = user.id
    else:
        db.add(DeviceToken(user_id=user.id, token=payload.token))
    db.commit()
    return {"status": "ok"}


@router.delete("/token")
def delete_token(payload: TokenBody, user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> dict:
    db.execute(delete(DeviceToken).where(
        DeviceToken.token == payload.token, DeviceToken.user_id == user.id
    ))
    db.commit()
    return {"status": "ok"}


def send_to_names(names: list[str], title: str, body: str, data: dict[str, str]) -> None:
    global _credentials, _missing_config_logged
    raw = get_settings().firebase_service_account_json
    if not raw:
        if not _missing_config_logged:
            logger.info("Firebase push is disabled: FIREBASE_SERVICE_ACCOUNT_JSON is unset")
            _missing_config_logged = True
        return
    try:
        if _credentials is None:
            info = json.loads(raw)
            _credentials = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/firebase.messaging"]
            )
        if not _credentials.valid:
            _credentials.refresh(Request())
        project_id = _credentials.project_id
        headers = {"Authorization": f"Bearer {_credentials.token}"}
    except Exception:
        logger.exception("Could not authenticate with Firebase")
        return

    with SessionLocal() as db:
        # ponytail: same-name users all receive it; upgrade by keying exchange by user id.
        users = db.scalars(select(User).where(User.is_active.is_(True), User.display_name.in_(names))).all()
        tokens = db.scalars(select(DeviceToken).where(DeviceToken.user_id.in_([u.id for u in users]))).all() if users else []
        for token_row in tokens:
            url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
            message = {"message": {"token": token_row.token, "notification": {"title": title, "body": body},
                       "data": data, "android": {"priority": "high", "notification": {"channel_id": "exchange"}}}}
            try:
                response = httpx.post(url, headers=headers, json=message, timeout=15)
                if response.status_code == 404 or "UNREGISTERED" in response.text or (
                    response.status_code == 400 and "INVALID_ARGUMENT" in response.text
                ):
                    db.delete(token_row)
                    db.commit()
                elif response.is_error:
                    logger.warning("FCM send failed (%s): %s", response.status_code, response.text)
            except Exception:
                logger.exception("FCM send failed")

