from datetime import date
from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import auth, management
from app.config import Settings
from app.db import Base, get_db


def test_admin_account_and_personal_data_lifecycle(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    settings = Settings(_env_file=None, storage_root=tmp_path, bootstrap_admin_username="admin",
                        bootstrap_admin_password="safe-password", enable_test_account=False)
    monkeypatch.setattr(auth, "get_settings", lambda: settings)
    with Session(engine, expire_on_commit=False) as db:
        auth.ensure_bootstrap_accounts(db)
        app = FastAPI()
        app.include_router(auth.router)
        app.include_router(management.router)
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            login = lambda username, password: client.post("/api/auth/login", json={"username": username, "password": password}).json()["access_token"]
            admin = {"Authorization": f"Bearer {login('admin', 'safe-password')}"}
            assert client.get("/api/admin/users", headers=admin).status_code == 200
            created = client.post("/api/admin/users", headers=admin, json={"username": "driver1", "display_name": "Driver", "password": "password-123"})
            assert created.status_code == 201
            user_id = created.json()["id"]
            user = {"Authorization": f"Bearer {login('driver1', 'password-123')}"}
            assert client.get("/api/admin/users", headers=user).status_code == 403
            conversation = {"id": "old-1", "title": "Question", "createdAt": "2026-06-01T00:00:00Z", "messages": [{"isUser": True, "text": "Hello"}]}
            bookmark = {"regulation": "Rule", "chapter": "1", "version": ""}
            payload = {"conversations": [conversation], "bookmarks": [bookmark]}
            assert client.post("/api/me/import", headers=user, json=payload).status_code == 200
            assert client.post("/api/me/import", headers=user, json=payload).status_code == 200
            assert len(client.get("/api/me/conversations", headers=user).json()) == 1
            marks = client.get(f"/api/admin/users/{user_id}/bookmarks", headers=admin).json()
            assert len(marks) == 1
            assert client.delete(f"/api/admin/users/{user_id}/bookmarks/{marks[0]['id']}", headers=admin).status_code == 200
            assert client.delete(f"/api/admin/users/{user_id}/conversations/old-1", headers=admin).status_code == 200
            assert client.post("/api/me/import", headers=user, json=payload).status_code == 200
            assert client.get("/api/me/bookmarks", headers=user).json() == []
            assert client.get("/api/me/conversations", headers=user).json() == []
            assert client.put("/api/me/conversations/old-1", headers=user, json=conversation).status_code == 410
            assert client.patch(f"/api/admin/users/{user_id}", headers=admin, json={"is_active": False}).status_code == 200
            assert client.get("/api/me/bookmarks", headers=user).status_code == 401


def test_duty_parser_reads_selected_month_only():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "교번기관사 근무계획"
    for day in range(1, 29):
        sheet.cell(2, day + 27, date(2026, 2, day))
        sheet.cell(7, day + 27, "61" if day == 1 else "비")
    sheet.cell(7, 1, 1)
    sheet.cell(7, 2, "기관사")
    content = BytesIO()
    workbook.save(content)
    parsed = management.parse_duty_xlsx(content.getvalue(), "2026-02", "duty.xlsx")
    assert len(parsed["dates"]) == 28
    assert parsed["drivers"][0]["days"]["2026-02-01"] == {"code": "61", "type": "night", "turn": "61"}
    assert parsed["turns"] == {}
