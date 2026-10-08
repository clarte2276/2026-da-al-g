import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import auth, crew
from app.config import Settings
from app.db import Base, get_db


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
        app.dependency_overrides[get_db] = lambda: db
        
        yield TestClient(app)

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
