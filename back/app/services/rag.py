from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import (
    Document,
    DocumentContent,
    DocumentLink,
    DocumentVersion,
    Fragment,
    KnowledgeEdge,
)
from .document_content import overlaps, selection_text, text_ranges
from .embedding import EmbeddingProvider, cosine_similarity

RELATION_WEIGHTS = {
    "REFERENCES": 1.00,
    "PROCEDURE": 0.95,
    "EXCEPTION": 0.90,
    "VISUAL_HELP": 0.82,
    "SUPERSEDES": 0.88,
    "RELATED": 0.70,
}


@dataclass(slots=True)
class Evidence:
    fragment: Fragment
    score: float
    hop: int
    path: list[str]
    via_relation: str | None = None
    link_id: str | None = None
    selection: dict | None = None
    document_id: str | None = None
    filename: str | None = None


class GraphRAGService:
    def __init__(self, settings: Settings, embedding_provider: EmbeddingProvider) -> None:
        self.settings = settings
        self.embedding_provider = embedding_provider

    def retrieve(
        self,
        db: Session,
        question: str,
        top_k: int = 5,
        max_hops: int | None = None,
        relation_types: list[str] | None = None,
    ) -> list[Evidence]:
        max_hops = self.settings.default_graph_hops if max_hops is None else max_hops
        query_vector = self.embedding_provider.embed([question])[0]
        fragments = self._vector_candidates(db, query_vector, top_k)
        if not fragments:
            fragments = list(
                db.scalars(select(Fragment).where(Fragment.embedding_json.is_not(None))).all()
            )
        question_tokens = set(re.findall(r"[가-힣A-Za-z0-9_]+", question.lower()))
        scored: list[tuple[Fragment, float]] = []
        for fragment in fragments:
            vector_score = cosine_similarity(
                query_vector,
                fragment.embedding_vector or fragment.embedding_json or [],
            )
            fragment_tokens = set(re.findall(r"[가-힣A-Za-z0-9_]+", (fragment.text or "").lower()))
            overlap = len(question_tokens & fragment_tokens) / max(len(question_tokens), 1)
            score = (vector_score * 0.8) + (overlap * 0.2)
            scored.append((fragment, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        seeds = [(fragment, score) for fragment, score in scored[:top_k]]
        if max_hops <= 0 or not seeds:
            return [Evidence(fragment=f, score=s, hop=0, path=[f.id]) for f, s in seeds]

        allowed = set(relation_types or [])
        edges = list(
            db.scalars(select(KnowledgeEdge).where(KnowledgeEdge.status == "approved")).all()
        )
        adjacency: dict[str, list[tuple[KnowledgeEdge, str]]] = {}
        for edge in edges:
            if allowed and edge.relation_type not in allowed:
                continue
            adjacency.setdefault(edge.source_fragment_id, []).append((edge, edge.target_fragment_id))
            adjacency.setdefault(edge.target_fragment_id, []).append((edge, edge.source_fragment_id))

        by_id = {fragment.id: fragment for fragment in fragments}
        if adjacency:
            connected_ids = set(by_id)
            frontier_ids = set(by_id)
            for _ in range(max_hops):
                next_ids = {
                    neighbor_id
                    for current_id in frontier_ids
                    for _, neighbor_id in adjacency.get(current_id, [])
                    if neighbor_id not in connected_ids
                }
                if not next_ids:
                    break
                connected_ids.update(next_ids)
                frontier_ids = next_ids
            if connected_ids - set(by_id):
                graph_fragments = db.scalars(
                    select(Fragment).where(Fragment.id.in_(connected_ids))
                ).all()
                by_id.update({fragment.id: fragment for fragment in graph_fragments})
        evidence: dict[str, Evidence] = {
            fragment.id: Evidence(fragment=fragment, score=score, hop=0, path=[fragment.id])
            for fragment, score in seeds
        }
        frontier = set(evidence)
        for hop in range(1, max_hops + 1):
            next_frontier: set[str] = set()
            for current_id in frontier:
                current = evidence[current_id]
                for edge, neighbor_id in adjacency.get(current_id, []):
                    neighbor = by_id.get(neighbor_id)
                    if not neighbor or neighbor_id in current.path:
                        continue
                    relation_weight = RELATION_WEIGHTS.get(edge.relation_type, 0.6)
                    candidate_score = current.score * relation_weight / hop
                    candidate_path = [*current.path, neighbor_id]
                    previous = evidence.get(neighbor_id)
                    if previous and previous.score >= candidate_score:
                        continue
                    evidence[neighbor_id] = Evidence(
                        fragment=neighbor,
                        score=candidate_score,
                        hop=hop,
                        path=candidate_path,
                        via_relation=edge.relation_type,
                    )
                    next_frontier.add(neighbor_id)
            frontier = next_frontier
            if not frontier:
                break

        self._expand_links(db, evidence, max_hops, allowed)
        return sorted(evidence.values(), key=lambda item: (item.hop != 0, -item.score))[: top_k * 3]

    def _expand_links(self, db: Session, evidence: dict[str, Evidence],
                      max_hops: int, allowed: set[str]) -> None:
        links = list(db.scalars(select(DocumentLink).where(DocumentLink.status == "approved")))
        contents = {c.version_id: c for c in db.scalars(select(DocumentContent))}
        # ponytail: scan approved links for each frontier; index version/range lookups at scale.
        for hop in range(1, max_hops + 1):
            frontier = [item for item in evidence.values() if item.hop == hop - 1]
            for current in frontier:
                for link in links:
                    if (allowed and link.relation_type not in allowed) or link.id in current.path:
                        continue
                    for source, target in ((link.source_selection, link.target_selection),
                                           (link.target_selection, link.source_selection)):
                        content = contents.get(source["version_id"])
                        target_content = contents.get(target["version_id"])
                        if not content or not target_content:
                            continue
                        if current.selection:
                            previous = current.selection
                            matches = previous["version_id"] == source["version_id"] and (
                                bool(set(previous["pages"]) & set(source["pages"]))
                                if previous["kind"] == source["kind"] == "pages"
                                else previous["kind"] == source["kind"] == "text"
                                and any(a["start"] < b["end"] and a["end"] > b["start"]
                                        for a in text_ranges(previous) for b in text_ranges(source))
                            )
                        else:
                            matches = overlaps(current.fragment, source, content)
                        if not matches:
                            continue
                        key = f"link:{link.id}:{target['version_id']}:{'target' if target is link.target_selection else 'source'}"
                        score = current.score * RELATION_WEIGHTS.get(link.relation_type, 0.7) / hop
                        if key in evidence and evidence[key].score >= score:
                            continue
                        version = db.get(DocumentVersion, target["version_id"])
                        document = db.get(Document, version.document_id)
                        text_value = selection_text(target_content, target).strip()
                        fragment = Fragment(
                            id=key, version_id=version.id, parent_id=None, stable_key=key,
                            kind=target["kind"], ordinal=0, title=document.filename,
                            text=text_value or "텍스트 없는 페이지입니다. 원본을 확인하세요.",
                            html=None, table_json=None, bbox_json=None, asset_path=None,
                            locator_json={"pages": target["pages"]} if target["kind"] == "pages"
                            else {"ranges": [{"start": part["start"], "end": part["end"]}
                                             for part in text_ranges(target)]},
                            content_hash="", metadata_json={},
                        )
                        evidence[key] = Evidence(
                            fragment=fragment, score=score, hop=hop,
                            path=[*current.path, link.id], via_relation=link.relation_type,
                            link_id=link.id, selection=target,
                            document_id=document.id, filename=document.filename,
                        )

    def _vector_candidates(
        self,
        db: Session,
        query_vector: list[float],
        top_k: int,
    ) -> list[Fragment]:
        """Use the pgvector HNSW index when the PostgreSQL profile is active.

        SQLite intentionally uses the deterministic Python fallback below. The
        try/except keeps the API usable while a database is being migrated.
        """
        bind = db.get_bind()
        if not bind or bind.dialect.name != "postgresql":
            return []
        vector_literal = "[" + ",".join(str(float(value)) for value in query_vector) + "]"
        try:
            rows = db.execute(
                text(
                    "SELECT id FROM fragments "
                    "WHERE embedding_vector IS NOT NULL "
                    "ORDER BY embedding_vector <=> CAST(:query_vector AS vector) "
                    "LIMIT :candidate_limit"
                ),
                {
                    "query_vector": vector_literal,
                    "candidate_limit": max(top_k * 8, 50),
                },
            ).all()
        except Exception:  # noqa: BLE001 - allow a partially migrated DB to use fallback search
            return []
        ids = [row[0] for row in rows]
        if not ids:
            return []
        return list(db.scalars(select(Fragment).where(Fragment.id.in_(ids))).all())

    def answer(self, question: str, evidence: list[Evidence], model: str | None = None) -> str:
        if not evidence:
            return "관련된 문서 근거를 찾지 못했습니다."
        context_parts = []
        for index, item in enumerate(evidence, start=1):
            locator = ", ".join(f"{key}={value}" for key, value in item.fragment.locator_json.items())
            context_parts.append(
                f"[근거 {index} | hop={item.hop} | {locator}]\n{item.fragment.text or '(텍스트 없음)'}"
            )
        context = "\n\n".join(context_parts)
        if self.settings.openai_api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=self.settings.openai_api_key)
                response = client.chat.completions.create(
                    model=model or self.settings.llm_model,
                    temperature=0,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "문서 근거만 사용해 한국어로 답변하세요. 근거가 부족하면 모른다고 말하고, "
                                "답변 끝에 [근거 n] 형식으로 참조하세요. 그래프 hop이 0보다 큰 근거는 "
                                "연결된 관련 자료임을 명시하세요."
                            ),
                        },
                        {"role": "user", "content": f"질문: {question}\n\n문서 근거:\n{context}"},
                    ],
                )
                return response.choices[0].message.content or context_parts[0]
            except Exception as exc:
                import logging

                logging.getLogger(__name__).debug("LLM answer generation failed", exc_info=exc)
        snippets = [item.fragment.text for item in evidence[:3] if item.fragment.text]
        return "검색된 근거를 바탕으로 확인할 수 있는 내용입니다.\n\n" + "\n\n".join(snippets)
