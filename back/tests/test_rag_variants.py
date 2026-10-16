import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import Base
from app.models import Fragment
from app.services.rag import Evidence, GraphRAGService


class _FixedEmbedding:
    name = "fixed"
    model = "fixed"

    def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


class _ScoredCorpus:
    def __init__(self, units):
        self.units = units
        self.sections = {}

    def score_components(self, query_vector, question_tokens):
        return [0.9, 0.1, 0.7], [0.1, 0.8, 0.6]


def _service(tmp_path, variant, units, rerank_calls, expansion_calls):
    service = GraphRAGService(
        Settings(storage_root=tmp_path, embedding_dimensions=2, rag_variant=variant),
        _FixedEmbedding(),
    )
    corpus = _ScoredCorpus(units[:3])
    service._full_corpus = lambda db: corpus
    service._vector_candidates = lambda db, query_vector, top_k: []

    def rerank(question, scored, top_k, sections, linked_ids=None):
        rerank_calls.append(linked_ids)
        return scored[:top_k]

    def expand(db, evidence, max_hops, allowed, question_tokens):
        expansion_calls.append(variant)
        evidence["linked"] = Evidence(units[3], 0.8, 1, [units[2].id, "link"], link_id="link")

    service._rerank = rerank
    service._expand_links = expand
    return service


def test_retrieval_variants_use_their_expected_paths(tmp_path):
    units = [
        Fragment(id=name, version_id="v", kind="paragraph", text=text, locator_json={})
        for name, text in (
            ("bm25", "alpha beta gamma"),
            ("dense", "unrelated words"),
            ("hybrid", "partial match"),
            ("linked", "linked evidence"),
        )
    ]
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    outputs = {}
    rerank_counts = {}
    expansion_calls = []

    with Session(engine) as db:
        for variant in ("bm25", "dense", "hybrid", "hybrid_rerank", "link_all", "proposed"):
            rerank_calls = []
            service = _service(tmp_path, variant, units, rerank_calls, expansion_calls)
            outputs[variant] = service.retrieve(db, "alpha beta gamma", top_k=1, max_hops=2)
            rerank_counts[variant] = rerank_calls

        default_service = _service(tmp_path, "proposed", units, [], expansion_calls)
        default_service.settings = Settings(storage_root=tmp_path, embedding_dimensions=2)
        default_output = default_service.retrieve(db, "alpha beta gamma", top_k=1, max_hops=2)

    assert outputs["bm25"][0].fragment.id == "bm25"
    assert outputs["dense"][0].fragment.id == "dense"
    assert outputs["hybrid"][0].fragment.id == "hybrid"
    assert rerank_counts["bm25"] == rerank_counts["dense"] == rerank_counts["hybrid"] == []
    assert len(rerank_counts["hybrid_rerank"]) == 1
    assert len(rerank_counts["link_all"]) == 1
    assert len(rerank_counts["proposed"]) == 2
    assert [item.fragment.id for item in outputs["hybrid_rerank"]] == ["hybrid"]
    assert [item.fragment.id for item in outputs["link_all"]] == ["hybrid", "linked"]
    assert [item.fragment.id for item in outputs["proposed"]] == ["hybrid", "linked"]
    assert [
        (item.fragment.id, item.score, item.hop, item.link_id) for item in default_output
    ] == [
        (item.fragment.id, item.score, item.hop, item.link_id) for item in outputs["proposed"]
    ]
    assert expansion_calls == ["link_all", "proposed", "proposed"]


def test_tiny_dataset_fixture_uses_the_paper_contract():
    path = Path(__file__).parent / "fixtures" / "ragas_eval_tiny.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    case = payload["cases"][0]

    assert payload["version"]
    assert {"name", "question", "category", "reference_answer", "gold_evidence"} <= case.keys()
    assert {"document_version_id", "article", "page", "label", "via_link"} <= case["gold_evidence"][0].keys()
