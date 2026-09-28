from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import auth
from app.auth import AdminUser, CurrentUser
from app.config import Settings
from app.db import Base, get_db
from app.models import AuthSession, User


def test_register_login_me_logout_and_role_guard(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    settings = Settings(
        _env_file=None,
        storage_root=tmp_path,
        enable_registration=True,
        enable_test_account=True,
        bootstrap_admin_username="admin",
        bootstrap_admin_password="admin-password",
    )
    monkeypatch.setattr(auth, "get_settings", lambda: settings)

    with Session(engine, expire_on_commit=False) as db:
        auth.ensure_bootstrap_accounts(db)
        app = FastAPI()
        app.include_router(auth.router)
        app.dependency_overrides[get_db] = lambda: db

        @app.get("/protected")
        def protected(user: CurrentUser) -> dict[str, str]:
            return {"username": user.username}

        @app.get("/admin")
        def admin(user: AdminUser) -> dict[str, str]:
            return {"username": user.username}

        with TestClient(app) as client:
            assert client.get("/protected").status_code == 401

            test_login = client.post(
                "/api/auth/login",
                json={"username": "test", "password": "test"},
            )
            assert test_login.status_code == 200
            test_token = test_login.json()["access_token"]
            assert client.get(
                "/protected", headers={"Authorization": f"Bearer {test_token}"}
            ).json() == {"username": "test"}
            assert client.get(
                "/admin", headers={"Authorization": f"Bearer {test_token}"}
            ).status_code == 403

            registered = client.post(
                "/api/auth/register",
                json={
                    "username": "New.User",
                    "password": "password-123",
                    "display_name": "새 사용자",
                },
            )
            assert registered.status_code == 201
            assert registered.json()["user"]["username"] == "new.user"
            assert client.post(
                "/api/auth/register",
                json={"username": "new.user", "password": "password-456"},
            ).status_code == 409

            admin_login = client.post(
                "/api/auth/login",
                json={"username": "ADMIN", "password": "admin-password"},
            )
            assert admin_login.status_code == 200
            admin_token = admin_login.json()["access_token"]
            assert client.get(
                "/admin", headers={"Authorization": f"Bearer {admin_token}"}
            ).json() == {"username": "admin"}

            assert client.post(
                "/api/auth/logout", headers={"Authorization": f"Bearer {test_token}"}
            ).status_code == 200
            assert client.get(
                "/protected", headers={"Authorization": f"Bearer {test_token}"}
            ).status_code == 401

        registered_user = db.scalar(select(User).where(User.username == "new.user"))
        assert registered_user.password_hash != "password-123"
        assert db.scalar(select(AuthSession).where(AuthSession.user_id.is_not(None)))

    engine.dispose()


def test_chat_feedback_is_stored_in_audit_log():
    from app.main import chat_feedback
    from app.models import AuditEvent
    from app.schemas import ChatFeedbackRequest

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="u", password_hash="x", display_name="u", role="user", is_active=True)
        db.add(user)
        db.commit()
        payload = ChatFeedbackRequest(rating="down", reason="조항 번호 틀림", question="q", answer="a",
                                      evidence=[{"filename": "f.pdf"}])
        out = chat_feedback(payload, db, user)
        event = db.scalar(select(AuditEvent).where(AuditEvent.action == "chat.feedback"))
        assert event.entity_id == out["id"]
        assert event.actor == user.id
        assert event.payload_json["reason"] == "조항 번호 틀림"


def test_change_password_keeps_current_session_and_revokes_others(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    settings = Settings(_env_file=None, storage_root=tmp_path, enable_test_account=True,
                        bootstrap_admin_username=None, bootstrap_admin_password=None)
    monkeypatch.setattr(auth, "get_settings", lambda: settings)

    with Session(engine, expire_on_commit=False) as db:
        auth.ensure_bootstrap_accounts(db)
        app = FastAPI()
        app.include_router(auth.router)
        app.dependency_overrides[get_db] = lambda: db

        with TestClient(app) as client:
            def login(password):
                return client.post("/api/auth/login", json={"username": "test", "password": password})

            phone = {"Authorization": f"Bearer {login('test').json()['access_token']}"}
            tablet = {"Authorization": f"Bearer {login('test').json()['access_token']}"}

            wrong = client.post("/api/auth/password", headers=phone,
                                json={"current_password": "nope", "new_password": "new-password-1"})
            assert wrong.status_code == 400

            ok = client.post("/api/auth/password", headers=phone,
                             json={"current_password": "test", "new_password": "new-password-1"})
            assert ok.status_code == 200

            assert client.get("/api/auth/me", headers=phone).status_code == 200
            assert client.get("/api/auth/me", headers=tablet).status_code == 401
            assert login("test").status_code == 401
            assert login("new-password-1").status_code == 200


def test_every_answer_is_logged():
    from types import SimpleNamespace

    from app.main import _log_answer
    from app.models import AuditEvent
    from app.services.chat import ChatResult

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    evidence = SimpleNamespace(fragment=SimpleNamespace(id="f1"), link_id=None, filename="규정.hwp",
                               location="제1조", version_id="v1", page=3, score=0.91234, hop=0)
    with Session(engine) as db:
        _log_answer(db, "u1", "질문", ChatResult("답변", "rag", [evidence]))
        event = db.scalar(select(AuditEvent).where(AuditEvent.action == "chat.answer"))
        assert event.actor == "u1"
        assert event.payload_json["question"] == "질문"
        assert event.payload_json["evidence"][0]["fragment_id"] == "f1"
        assert event.payload_json["evidence"][0]["score"] == 0.9123
