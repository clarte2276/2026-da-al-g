from __future__ import annotations

import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import AuditEvent, AuthSession, User
from .schemas import AuthLoginRequest, AuthRegisterRequest, AuthResponse, UserOut

USERNAME_RE = re.compile(r"^[a-z0-9._-]+$")
TEST_USERNAME = "test"
TEST_PASSWORD = "test"
password_hash = PasswordHash.recommended()
dummy_password_hash = password_hash.hash("invalid-login-password")

router = APIRouter(prefix="/api/auth", tags=["auth"])
DB = Annotated[Session, Depends(get_db)]


def normalize_username(username: str) -> str:
    return username.strip().casefold()


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
    )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _issue_session(db: Session, user: User) -> AuthResponse:
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=settings.auth_session_hours)
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=_token_hash(token),
            expires_at=expires_at,
        )
    )
    db.add(
        AuditEvent(
            actor=user.id,
            action="auth.login",
            entity_type="user",
            entity_id=user.id,
        )
    )
    db.commit()
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at,
        user=_user_out(user),
    )


def get_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization:
        raise _unauthorized()
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token.strip():
        raise _unauthorized()
    return token.strip()


def get_current_user(token: Annotated[str, Depends(get_bearer_token)], db: DB) -> User:
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _token_hash(token),
            AuthSession.revoked_at.is_(None),
        )
    )
    if not session or _aware(session.expires_at) <= datetime.now(UTC):
        raise _unauthorized()
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def authenticate_user(db: Session, username: str, candidate_password: str) -> User | None:
    """Authenticate a local account; this boundary can later call employee/PIN auth."""
    normalized_username = normalize_username(username)
    user = db.scalar(select(User).where(User.username == normalized_username))
    candidate_hash = user.password_hash if user else dummy_password_hash
    try:
        valid = password_hash.verify(candidate_password, candidate_hash)
    except PwdlibError:
        valid = False
    return user if user and user.is_active and valid else None


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: AuthRegisterRequest, db: DB) -> AuthResponse:
    settings = get_settings()
    if not settings.enable_registration:
        raise HTTPException(status_code=403, detail="회원가입이 비활성화되어 있습니다.")
    username = normalize_username(payload.username)
    if not USERNAME_RE.fullmatch(username):
        raise HTTPException(status_code=422, detail="아이디는 영문, 숫자, 마침표, 밑줄, 하이픈만 사용할 수 있습니다.")
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")
    if username == TEST_USERNAME:
        raise HTTPException(status_code=409, detail="예약된 아이디입니다.")
    display_name = (payload.display_name or username).strip() or username
    user = User(
        username=username,
        password_hash=password_hash.hash(payload.password),
        display_name=display_name,
        role="user",
        is_active=True,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.") from exc
    db.add(
        AuditEvent(
            actor=user.id,
            action="auth.register",
            entity_type="user",
            entity_id=user.id,
        )
    )
    return _issue_session(db, user)


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLoginRequest, db: DB) -> AuthResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise _unauthorized()
    return _issue_session(db, user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return _user_out(user)


@router.post("/logout")
def logout(
    token: Annotated[str, Depends(get_bearer_token)],
    user: CurrentUser,
    db: DB,
) -> dict[str, str]:
    db.execute(
        update(AuthSession)
        .where(AuthSession.token_hash == _token_hash(token), AuthSession.user_id == user.id)
        .values(revoked_at=datetime.now(UTC))
    )
    db.add(
        AuditEvent(
            actor=user.id,
            action="auth.logout",
            entity_type="user",
            entity_id=user.id,
        )
    )
    db.commit()
    return {"status": "ok"}


def ensure_bootstrap_accounts(db: Session) -> None:
    settings = get_settings()
    test_user = db.scalar(select(User).where(User.username == TEST_USERNAME))
    if settings.enable_test_account:
        if not test_user:
            user = User(
                username=TEST_USERNAME,
                password_hash=password_hash.hash(TEST_PASSWORD),
                display_name="테스트 사용자",
                role="user",
                is_active=True,
            )
            db.add(user)
        else:
            test_user.is_active = True
    elif test_user:
        test_user.is_active = False
        db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == test_user.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )

    username = normalize_username(settings.bootstrap_admin_username or "")
    password = settings.bootstrap_admin_password or ""
    if username and password and not db.scalar(select(User).where(User.username == username)):
        db.add(
            User(
                username=username,
                password_hash=password_hash.hash(password),
                display_name=settings.bootstrap_admin_display_name.strip() or "관리자",
                role="admin",
                is_active=True,
            )
        )
    db.commit()
