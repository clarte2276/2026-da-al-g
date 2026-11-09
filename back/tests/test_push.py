from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import auth, crew, management, push
from app.config import Settings
from app.db import Base, get_db
from app.models import DeviceToken


def setup_client(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    settings = Settings(_env_file=None, storage_root=tmp_path, bootstrap_admin_username="admin",
                        bootstrap_admin_password="safe-password")
    monkeypatch.setattr(auth, "get_settings", lambda: settings)
    db = Session(engine, expire_on_commit=False)
    auth.ensure_bootstrap_accounts(db)
    db.add_all([
        auth.User(username="u1", display_name="One", password_hash=auth.password_hash.hash("pw"), role="user", is_active=True),
        auth.User(username="u2", display_name="Two", password_hash=auth.password_hash.hash("pw"), role="user", is_active=True),
    ])
    db.commit()
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(push.router)
    app.include_router(crew.router)
    app.include_router(management.router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app), db, settings


def headers(client, username, password="pw"):
    token = client.post("/api/auth/login", json={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_token_upsert_and_owned_delete(tmp_path, monkeypatch):
    client, db, _ = setup_client(tmp_path, monkeypatch)
    one, two = headers(client, "u1"), headers(client, "u2")
    assert client.post("/api/push/token", headers=one, json={"token": "fcm"}).json() == {"status": "ok"}
    client.post("/api/push/token", headers=two, json={"token": "fcm"})
    row = db.query(DeviceToken).one()
    assert row.user_id == db.query(auth.User).filter_by(username="u2").one().id
    assert client.request("DELETE", "/api/push/token", headers=one, json={"token": "fcm"}).status_code == 200
    assert db.query(DeviceToken).count() == 1
    assert client.request("DELETE", "/api/push/token", headers=two, json={"token": "fcm"}).status_code == 200
    assert db.query(DeviceToken).count() == 0


def test_admin_user_delete_removes_device_tokens(tmp_path, monkeypatch):
    client, db, _ = setup_client(tmp_path, monkeypatch)
    user = db.query(auth.User).filter_by(username="u1").one()
    db.add(DeviceToken(user_id=user.id, token="registered"))
    db.commit()
    admin = headers(client, "admin", "safe-password")
    response = client.delete(f"/api/admin/users/{user.id}", headers=admin)
    assert response.status_code == 200
    assert db.query(DeviceToken).filter_by(user_id=user.id).count() == 0


def test_direct_exchange_schedules_send(tmp_path, monkeypatch):
    client, _, _ = setup_client(tmp_path, monkeypatch)
    sent = []
    monkeypatch.setattr(crew, "send_to_names", lambda *args: sent.append(args))
    response = client.post("/api/exchange/posts", headers=headers(client, "u1"), json={
        "type": "direct", "target_name": "Two", "dates": ["2026-06-01"]
    })
    assert response.status_code == 201
    assert sent[0][0] == ["Two"] and sent[0][3] == {"type": "exchange", "post_id": response.json()["id"]}


def test_no_config_is_noop_and_invalid_token_is_removed(tmp_path, monkeypatch):
    _, db, settings = setup_client(tmp_path, monkeypatch)
    monkeypatch.setattr(push, "get_settings", lambda: settings)
    monkeypatch.setattr(push, "SessionLocal", lambda: db)
    push.send_to_names(["Nobody"], "title", "body", {})
    settings.firebase_service_account_json = '{"project_id":"test"}'
    db.add(DeviceToken(user_id=db.query(auth.User).filter_by(username="u1").one().id, token="bad"))
    db.commit()

    class Credentials:
        valid = True
        token = "access"
        project_id = "test"

    class Response:
        status_code = 404
        text = "UNREGISTERED"
        is_error = True

    monkeypatch.setattr(push.service_account.Credentials, "from_service_account_info", lambda *_a, **_k: Credentials())
    monkeypatch.setattr(push.httpx, "post", lambda *_a, **_k: Response())
    push._credentials = None
    push.send_to_names(["One"], "title", "body", {})
    assert db.query(DeviceToken).count() == 0
