import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import auth, crew, management
from app.config import Settings
from app.db import Base, get_db
from app.models import DutySchedule


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    settings = Settings(_env_file=None, storage_root=tmp_path, bootstrap_admin_username="admin",
                        bootstrap_admin_password="safe-password", enable_test_account=False)
    monkeypatch.setattr(auth, "get_settings", lambda: settings)
    monkeypatch.setattr(crew, "get_settings", lambda: settings)
    
    with Session(engine, expire_on_commit=False) as db:
        auth.ensure_bootstrap_accounts(db)
        # Create a few users
        db.add(auth.User(username="user1", display_name="User One", password_hash=auth.password_hash.hash("pw"), role="user", is_active=True))
        db.add(auth.User(username="user2", display_name="User Two", password_hash=auth.password_hash.hash("pw"), role="user", is_active=True))
        db.add(auth.User(username="user3", display_name="User Three", password_hash=auth.password_hash.hash("pw"), role="user", is_active=True))
        db.commit()

        app = FastAPI()
        app.include_router(auth.router)
        app.include_router(crew.router)
        app.include_router(management.router)
        app.dependency_overrides[get_db] = lambda: db

        test_client = TestClient(app)
        test_client.db = db
        yield test_client

def login(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_exchange_direct(client):
    u1 = login(client, "user1", "pw")
    u2 = login(client, "user2", "pw")
    u3 = login(client, "user3", "pw")
    
    # direct exchange create->target accepts
    res = client.post("/api/exchange/posts", headers=u1, json={
        "type": "direct", "target_name": "User Two", "dates": ["2026-06-01"]
    })
    assert res.status_code == 201
    post_id = res.json()["id"]
    
    # non-target cannot respond (403)
    assert client.post(f"/api/exchange/posts/{post_id}/respond", headers=u3, json={"action": "accept"}).status_code == 403
    
    # target accepts
    res = client.post(f"/api/exchange/posts/{post_id}/respond", headers=u2, json={"action": "accept"})
    assert res.status_code == 200
    assert res.json()["status"] == "accepted"

def test_exchange_open(client):
    u1 = login(client, "user1", "pw")
    u2 = login(client, "user2", "pw")
    u3 = login(client, "user3", "pw")
    
    res = client.post("/api/exchange/posts", headers=u1, json={
        "type": "open", "dates": ["2026-06-01"]
    })
    assert res.status_code == 201
    post_id = res.json()["id"]
    
    # requester cannot volunteer
    assert client.post(f"/api/exchange/posts/{post_id}/volunteers", headers=u1).status_code == 403
    
    # volunteers apply
    res2 = client.post(f"/api/exchange/posts/{post_id}/volunteers", headers=u2)
    assert res2.status_code == 201
    v2_id = res2.json()["id"]
    client.post(f"/api/exchange/posts/{post_id}/volunteers", headers=u3)
    
    # open post volunteer->requester accepts (others rejected)
    res = client.post(f"/api/exchange/posts/{post_id}/volunteers/{v2_id}/accept", headers=u1)
    assert res.status_code == 200
    assert res.json()["status"] == "accepted"
    vols = res.json()["volunteers"]
    assert any(v["id"] == v2_id and v["status"] == "accepted" for v in vols)
    assert any(v["id"] != v2_id and v["status"] == "rejected" for v in vols)

def test_standby_coverage(client):
    u1 = login(client, "user1", "pw")
    admin = login(client, "admin", "safe-password")
    
    # upload
    res = client.post("/api/standby-coverage", headers=u1, data={"date": "2026-10-01"}, files={"file": ("test.png", b"fake image content")})
    assert res.status_code == 201
    item_id = res.json()["id"]
    
    # list
    res = client.get("/api/standby-coverage", headers=admin)
    assert res.status_code == 200
    assert len(res.json()) == 1
    
    # delete-permissions (u2 cannot delete)
    u2 = login(client, "user2", "pw")
    assert client.delete(f"/api/standby-coverage/{item_id}", headers=u2).status_code == 403
    
    # u1 can delete
    assert client.delete(f"/api/standby-coverage/{item_id}", headers=u1).status_code == 200

def test_alerts(client):
    u1 = login(client, "user1", "pw")
    admin = login(client, "admin", "safe-password")
    
    # admin-only create
    assert client.post("/api/alerts", headers=u1, json={"station_from": "A", "station_to": "B", "message": "msg"}).status_code == 403
    
    res = client.post("/api/alerts", headers=admin, json={"station_from": "A", "station_to": "B", "message": "msg"})
    assert res.status_code == 201
    
    # expiry filter
    client.post("/api/alerts", headers=admin, json={"station_from": "C", "station_to": "D", "message": "msg2", "expires_at": "2000-01-01T00:00:00Z"})
    res = client.get("/api/alerts", headers=u1)
    assert res.status_code == 200
    assert len(res.json()) == 1

def test_voice(client):
    u1 = login(client, "user1", "pw")
    u2 = login(client, "user2", "pw")
    
    # create
    res = client.post("/api/voice", headers=u1, json={"content": "hello world"})
    assert res.status_code == 201
    thread_id = res.json()["id"]
    
    # owner isolation
    res = client.get("/api/voice", headers=u1)
    assert len(res.json()) == 1
    res = client.get("/api/voice", headers=u2)
    assert len(res.json()) == 0
    assert client.post(f"/api/voice/{thread_id}/replies", headers=u2, json={"content": "hi"}).status_code == 403
    
    # rate limit (6th attempt should fail)
    for _ in range(4):
        client.post("/api/voice", headers=u1, json={"content": "hello world"})
    assert client.post("/api/voice", headers=u1, json={"content": "hello world"}).status_code == 429

def test_game_score(client):
    u1 = login(client, "user1", "pw")
    u2 = login(client, "user2", "pw")
    
    client.post("/api/games/scores", headers=u1, json={"game": "reaction", "score": 200})
    client.post("/api/games/scores", headers=u1, json={"game": "reaction", "score": 150})
    client.post("/api/games/scores", headers=u2, json={"game": "reaction", "score": 180})
    
    # best-per-user ordering (reaction ascending)
    res = client.get("/api/games/scores?game=reaction", headers=u1)
    assert res.status_code == 200
    scores = res.json()
    assert len(scores) == 2
    assert scores[0]["name"] == "User One"
    assert scores[0]["score"] == 150
    assert scores[1]["name"] == "User Two"
    assert scores[1]["score"] == 180

def test_realtime_503_without_key(client):
    u1 = login(client, "user1", "pw")
    res = client.get("/api/realtime/trains", headers=u1)
    assert res.status_code == 503
    assert "키가 설정되지 않았습니다" in res.json()["detail"]


def test_realtime_seoul_errors_and_no_trains(client, monkeypatch, tmp_path):
    settings = Settings(_env_file=None, storage_root=tmp_path, seoul_subway_api_key="test-key")
    monkeypatch.setattr(crew, "get_settings", lambda: settings)
    headers = login(client, "user1", "pw")

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps(self.payload).encode()

    crew._train_cache.update(items=[], ts=0.0)
    payload = {"RESULT": {"CODE": "INFO-100", "MESSAGE": "INFO-100 인증키가 유효하지 않습니다"}}
    def fake_urlopen(url, **_kwargs):
        assert url.isascii(), url  # 실제 urlopen은 한글 URL을 보내지 못한다
        return FakeResponse(payload)

    monkeypatch.setattr(crew.urllib.request, "urlopen", fake_urlopen)
    error = client.get("/api/realtime/trains", headers=headers)
    assert error.status_code == 502 and "INFO-100" in error.json()["detail"]

    payload = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다"}}
    no_trains = client.get("/api/realtime/trains", headers=headers)
    assert no_trains.status_code == 200 and no_trains.json() == []


def _seed_duty(client, dates, codes):
    drivers = []
    for number, (name, day_codes) in enumerate(codes.items(), 1):
        days = {}
        for day in dates:
            code = day_codes[day]
            kind = "night" if code.isdigit() and int(code) >= 60 else "day"
            days[day] = {"code": code, "type": kind, "turn": code}
        drivers.append({"no": number, "name": name, "days": days})
    data = {"month": "2026-06", "line": "6호선", "office": "수색승무사업소",
            "dates": dates, "dayTypes": {"2026-05-31": "휴", "2026-06-01": "평",
                                           "2026-06-02": "평"},
            "drivers": drivers, "turns": {}, "turnDetailIsDummy": True}
    client.db.add(DutySchedule(month="2026-06", data=data, source_filename="test.xlsx"))
    client.db.commit()


def test_exchange_applies_both_sides_stale_codes_and_revert(client):
    u1, u2, u3 = (login(client, f"user{i}", "pw") for i in (1, 2, 3))
    _seed_duty(client, ["2026-06-01"], {
        "User One": {"2026-06-01": "1"},
        "User Two": {"2026-06-01": "61"},
        "User Three": {"2026-06-01": "2"},
    })
    months = client.get("/api/duty", headers=u1).json()
    assert months[:3] == ["2026-12", "2026-11", "2026-10"]
    projected = client.get("/api/duty/2026-07", headers=u1).json()
    assert projected["projected"] is True and projected["projectedFrom"] == "2026-06"
    post = client.post("/api/exchange/posts", headers=u1, json={
        "type": "direct", "target_name": "User Two", "dates": ["2026-06-01"],
        "requester_dias": ["1"], "target_dias": ["61"],
    }).json()
    accepted = client.post(f"/api/exchange/posts/{post['id']}/respond", headers=u2,
                           json={"action": "accept"})
    assert accepted.status_code == 200 and accepted.json()["applied"] is True
    duty = client.get("/api/duty/2026-06", headers=u1).json()
    assert duty["drivers"][0]["days"]["2026-06-01"]["code"] == "61"
    assert duty["drivers"][0]["days"]["2026-06-01"]["original"]["code"] == "1"
    assert duty["drivers"][1]["days"]["2026-06-01"]["code"] == "1"
    matches = client.get("/api/exchange/match?date=2026-06-01", headers=u1).json()
    partner_match = next(item for item in matches if item["name"] == "User Two")
    assert partner_match["turnKey"] == "평평:1" and partner_match["swapped"] is True

    stale = client.post("/api/exchange/posts", headers=u1, json={
        "type": "direct", "target_name": "User Three", "dates": ["2026-06-01"],
        "requester_dias": ["1"], "target_dias": ["2"],
    }).json()
    assert client.post(f"/api/exchange/posts/{stale['id']}/respond", headers=u3,
                       json={"action": "accept"}).status_code == 409
    assert len(client.db.query(crew.DutyOverride).filter_by(active=True).all()) == 2

    revert = client.post(f"/api/exchange/posts/{post['id']}/revert", headers=u1)
    assert revert.status_code == 201 and revert.json()["revert_of"] == post["id"]
    assert client.post(f"/api/exchange/posts/{revert.json()['id']}/respond", headers=u2,
                       json={"action": "accept"}).status_code == 200
    duty = client.get("/api/duty/2026-06", headers=u1).json()
    assert duty["drivers"][0]["days"]["2026-06-01"]["code"] == "1"
    assert duty["drivers"][1]["days"]["2026-06-01"]["code"] == "61"


def test_open_exchange_accept_applies_swap(client):
    u1, u3 = login(client, "user1", "pw"), login(client, "user3", "pw")
    _seed_duty(client, ["2026-06-02"], {
        "User One": {"2026-06-02": "1"},
        "User Two": {"2026-06-02": "61"},
        "User Three": {"2026-06-02": "2"},
    })
    post = client.post("/api/exchange/posts", headers=u1, json={
        "type": "open", "dates": ["2026-06-02"], "requester_dias": ["1"],
    }).json()
    volunteer = client.post(f"/api/exchange/posts/{post['id']}/volunteers", headers=u3).json()
    accepted = client.post(f"/api/exchange/posts/{post['id']}/volunteers/{volunteer['id']}/accept", headers=u1)
    assert accepted.status_code == 200 and accepted.json()["applied"] is True
    data = client.get("/api/duty/2026-06", headers=u1).json()
    assert data["drivers"][0]["days"]["2026-06-02"]["code"] == "2"
    assert data["drivers"][2]["days"]["2026-06-02"]["code"] == "1"


def test_dia_image_auth_and_name_validation(client):
    user = login(client, "user1", "pw")
    image = next((Path(crew.__file__).parent / "static" / "dia").glob("*.png"))
    url = f"/api/duty/dia-images/{image.stem}.png"
    assert client.get(url).status_code == 401
    response = client.get(url, headers=user)
    assert response.status_code == 200 and response.headers["content-type"] == "image/png"
    assert client.get("/api/duty/dia-images/nope-1.png", headers=user).status_code == 404


def test_crew_matching_uses_fixed_time_and_mock_trains(client):
    from zoneinfo import ZoneInfo

    fixed = datetime(2026, 6, 1, 7, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    _seed_duty(client, ["2026-06-01"], {
        "User One": {"2026-06-01": "2"},
        "User Two": {"2026-06-01": "61"},
        "User Three": {"2026-06-01": "3"},
    })
    data = client.db.query(DutySchedule).filter_by(month="2026-06").one().data
    data["dayTypes"]["2026-06-01"] = "휴"
    client.db.query(DutySchedule).filter_by(month="2026-06").one().data = data
    client.db.commit()
    trains = crew._mock_trains(fixed)
    matched = crew._with_train_crews(trains, client.db, fixed)
    assert matched[0]["crew_name"] == "User One"
    assert matched[0]["crew_turn"] == "휴휴:2"
    assert matched[-1]["crew_name"] == "신내사업소"


def test_realtime_trains_mock_setting(client, monkeypatch, tmp_path):
    settings = Settings(_env_file=None, storage_root=tmp_path, realtime_trains_mock=True)
    monkeypatch.setattr(crew, "get_settings", lambda: settings)
    response = client.get("/api/realtime/trains", headers=login(client, "user1", "pw"))
    assert response.status_code == 200 and len(response.json()) == 8
    assert all("crew_name" in item and "crew_turn" in item for item in response.json())


def test_input_guards(client, tmp_path):
    u1 = login(client, "user1", "pw")
    u2 = login(client, "user2", "pw")
    # 날짜가 저장 경로에 들어가므로 형식이 아니면 거부한다.
    res = client.post("/api/standby-coverage", headers=u1, data={"date": "../../evil"},
                      files={"file": ("a.jpg", b"x", "image/jpeg")})
    assert res.status_code == 422
    assert not (tmp_path.parent / "evil").exists()
    # 공개 교체글은 respond로 처리할 수 없고, 성사된 글은 다시 수락할 수 없다.
    post = client.post("/api/exchange/posts", headers=u1, json={"type": "open", "dates": ["2026-06-02"]}).json()
    assert client.post(f"/api/exchange/posts/{post['id']}/respond", headers=u2,
                       json={"action": "accept"}).status_code == 422
    vid = client.post(f"/api/exchange/posts/{post['id']}/volunteers", headers=u2).json()["id"]
    assert client.post(f"/api/exchange/posts/{post['id']}/volunteers/{vid}/accept", headers=u1).status_code == 200
    assert client.post(f"/api/exchange/posts/{post['id']}/volunteers/{vid}/accept", headers=u1).status_code == 409
    assert client.delete(f"/api/exchange/posts/{post['id']}", headers=u1).status_code == 409
    assert client.post("/api/exchange/posts", headers=u1,
                       json={"type": "open", "dates": ["2026-13-40"]}).status_code == 422
