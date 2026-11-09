from docx import Document as WordDocument
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user
from app.config import Settings
from app.db import Base, get_db
from app.glossary import content_indexer, router
from app.models import Document, DocumentLink, Fragment, User
from app.services.embedding import HashEmbeddingProvider
from app.services.ingestion import IngestionService


def setup(tmp_path, admin=True):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    settings = Settings(_env_file=None, storage_root=tmp_path / "store", embedding_dimensions=64)
    service = IngestionService(settings, HashEmbeddingProvider(64))
    db = Session(engine, expire_on_commit=False)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[content_indexer] = lambda: service
    user = User(
        id="admin" if admin else "user",
        username="test",
        password_hash="x",
        display_name="Tester",
        role="admin" if admin else "user",
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: user
    return engine, db, TestClient(app), service


def test_glossary_publish_and_refs(tmp_path):
    engine, db, client, service = setup(tmp_path)
    docx = tmp_path / "안전규정.docx"
    word = WordDocument()
    word.add_paragraph("제28조(보호구 착용) 작업자는 보호구를 착용한다.")
    word.add_paragraph("제29조(출입 통제) 허가를 받아야 한다.")
    word.save(docx)
    _regulation, _ = service.ingest_new_file(db, docx, docx.name)
    db.commit()
    response = client.post(
        "/api/glossary",
        json={
            "category": "부품",
            "title": "제동 밸브",
            "code": "BR-1",
            "definition": "공기 압력을 조절해 열차를 제동하는 장치.",
            "regulations": "안전규정 제28조, 없는규정 제9조",
        },
    )
    assert response.status_code == 201, response.text
    entry = response.json()
    photo = client.put(
        f"/api/glossary/{entry['id']}/photo",
        files={"file": ("p.png", b"not-real-image", "image/png")},
    )
    assert photo.status_code == 200
    # A valid tiny PNG keeps the ingestion/PDF path independent of external files.
    import base64

    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/pWQAAAAASUVORK5CYII="
    )
    photo = client.put(
        f"/api/glossary/{entry['id']}/photo", files={"file": ("p.png", png, "image/png")}
    )
    assert photo.status_code == 200
    refs = client.get("/api/glossary/regulation-refs", params={"text": entry["regulations"]}).json()
    assert [r["found"] for r in refs] == [True, False]
    first = client.post(f"/api/glossary/{entry['id']}/publish")
    assert first.status_code == 200, first.text
    body = first.json()
    assert [x["status"] for x in body["links"]] == ["draft", "not_found"]
    version = next(
        v for v in db.scalars(select(Fragment).where(Fragment.version_id == body["version_id"]))
    )
    assert "제동 밸브" in version.text and "공기 압력을 조절" in version.text
    pdf_path = db.get(Document, body["document_id"]).source_path
    extracted = "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)
    assert "제동 밸브" in extracted and "공기 압력을 조절" in extracted
    links_before = list(db.scalars(select(DocumentLink)))
    assert len(links_before) == 1 and links_before[0].relation_type == "VISUAL_HELP"
    client.put(
        f"/api/glossary/{entry['id']}",
        json={
            "category": "부품",
            "title": "제동 밸브",
            "code": "BR-1",
            "definition": "새 정의입니다.",
            "regulations": entry["regulations"],
        },
    )
    second = client.post(f"/api/glossary/{entry['id']}/publish")
    assert second.status_code == 200, second.text
    assert len(list(db.scalars(select(DocumentLink)))) == 1
    assert db.scalar(select(Fragment.id).where(Fragment.version_id == body["version_id"])) is None
    latest = list(
        db.scalars(select(Fragment).where(Fragment.version_id == second.json()["version_id"]))
    )
    assert len(latest) == 1 and "새 정의입니다" in latest[0].text
    empty = client.post("/api/glossary", json={"title": "정의 누락", "definition": ""}).json()
    assert client.post(f"/api/glossary/{empty['id']}/publish").status_code == 422
    db.close()
    engine.dispose()


def test_glossary_requires_admin(tmp_path):
    engine, db, client, _ = setup(tmp_path, admin=False)
    assert client.get("/api/glossary").status_code in {401, 403}
    db.close()
    engine.dispose()
