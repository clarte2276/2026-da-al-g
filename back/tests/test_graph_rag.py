import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import Base
from app.models import Document, DocumentVersion, Fragment, KnowledgeEdge
from app.services.embedding import HashEmbeddingProvider
from app.services.rag import GraphRAGService


def _fragment(version_id: str, stable_key: str, text: str, embedding: list[float]) -> Fragment:
    return Fragment(
        version_id=version_id,
        stable_key=stable_key,
        kind="paragraph",
        ordinal=0,
        text=text,
        locator_json={"stable_key": stable_key},
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        embedding_json=embedding,
        embedding_vector=embedding,
        embedding_model="hash:hash-v1",
    )


def test_rag_expands_only_approved_edges(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    provider = HashEmbeddingProvider(dimensions=64)
    settings = Settings(storage_root=tmp_path, embedding_dimensions=64, default_graph_hops=2)
    service = GraphRAGService(settings, provider)

    with Session(engine) as db:
        document = Document(filename="규정.hwp", sha256="a" * 64, status="ready")
        db.add(document)
        db.flush()
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            sha256="a" * 64,
            storage_path="/tmp/규정.hwp",
            status="completed",
        )
        db.add(version)
        db.flush()
        seed_embedding = provider.embed(["ATC 고장 조치"])[0]
        seed = _fragment(version.id, "seed", "ATC 고장 조치", seed_embedding)
        approved_target = _fragment(
            version.id,
            "approved-target",
            "관련 규정에 따른 운전 절차",
            provider.embed(["운전 절차"])[0],
        )
        draft_target = _fragment(
            version.id,
            "draft-target",
            "아직 승인되지 않은 예외 절차",
            provider.embed(["예외 절차"])[0],
        )
        db.add_all([seed, approved_target, draft_target])
        db.flush()
        db.add_all(
            [
                KnowledgeEdge(
                    source_fragment_id=seed.id,
                    target_fragment_id=approved_target.id,
                    relation_type="REFERENCES",
                    status="approved",
                ),
                KnowledgeEdge(
                    source_fragment_id=seed.id,
                    target_fragment_id=draft_target.id,
                    relation_type="RELATED",
                    status="draft",
                ),
            ]
        )
        db.commit()

        evidence = service.retrieve(db, "ATC 고장 조치", top_k=1, max_hops=1)

    evidence_ids = {item.fragment.id for item in evidence}
    assert seed.id in evidence_ids
    assert approved_target.id in evidence_ids
    assert draft_target.id not in evidence_ids
    assert any(item.fragment.id == approved_target.id and item.hop == 1 for item in evidence)
