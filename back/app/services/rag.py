from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
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
from .document_content import overlaps, selection_text, text_ranges, utf16_length
from .embedding import EmbeddingProvider, cosine_similarity

RELATION_WEIGHTS = {
    "REFERENCES": 1.00,
    "PROCEDURE": 0.95,
    "EXCEPTION": 0.90,
    "VISUAL_HELP": 0.82,
    "SUPERSEDES": 0.88,
    "RELATED": 0.70,
}
TOKEN_SUFFIXES = ("하다고", "으로서", "으로", "에서", "에게", "에는", "하면", "해야", "하고",
                  "할", "했", "한", "인", "은", "는", "이", "가", "을", "를", "에", "의", "도",
                  "과", "와")
ARTICLE_HEADING_RE = re.compile(r"(?m)^[ \t]*(제\d+조)(?=\(|[ \t]|$)")


def _search_tokens(value: str) -> set[str]:
    tokens = set(re.findall(r"[가-힣A-Za-z0-9_]+", value.lower()))
    stems = set(tokens)
    for token in tokens:
        current = token
        while True:
            shortened = next(
                (
                    current[:-len(suffix)]
                    for suffix in TOKEN_SUFFIXES
                    if current.endswith(suffix) and len(current) > len(suffix) + 1
                ),
                None,
            )
            if not shortened:
                break
            stems.add(shortened)
            current = shortened
    return stems


def _utf16_index(value: str, offset: int) -> int:
    return len(value.encode("utf-16-le")[: offset * 2].decode("utf-16-le"))


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
    location: str | None = None
    version_id: str | None = None
    page: int | None = None


def _location_page(fragment: Fragment, selection: dict | None = None) -> int | None:
    """The page of the original document a chunk sits on, when the format has pages."""
    if selection and selection.get("kind") == "pages" and selection["pages"]:
        return int(selection["pages"][0])
    locator = fragment.locator_json or {}
    for key in ("page", "slide"):
        if locator.get(key) is not None:
            return int(locator[key])
    return None


def _location_label(fragment: Fragment, selection: dict | None = None) -> str | None:
    """Name the place in the source document a chunk came from."""
    if selection and selection.get("kind") == "pages" and selection["pages"]:
        pages = selection["pages"]
        return f"페이지 {pages[0]}" if len(pages) == 1 else f"페이지 {pages[0]}-{pages[-1]}"
    locator = fragment.locator_json or {}
    for key, label in (("page", "페이지"), ("slide", "슬라이드"), ("paragraph", "문단")):
        if locator.get(key) is not None:
            return f"{label} {locator[key]}"
    article = locator.get("article") or next(
        (match.group(1) for match in ARTICLE_HEADING_RE.finditer(fragment.text or "")), None
    )
    if article:
        return str(article)
    heading = next((line.strip() for line in (fragment.text or "").splitlines() if line.strip()), "")
    return f"「{heading[:30]}」 부분" if heading else None


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
        fragments = self._article_units(self._search_units(db, fragments), db)
        question_tokens = _search_tokens(question)
        fragment_token_list = [
            _search_tokens(f"{fragment.title or ''}\n{fragment.text or ''}")
            for fragment in fragments
        ]
        doc_freq: Counter[str] = Counter()
        for f_tokens in fragment_token_list:
            for t in f_tokens:
                doc_freq[t] += 1
        n_docs = max(len(fragments), 1)
        idf = {t: math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0) for t, df in doc_freq.items()}
        total_q_idf = sum(idf.get(t, 1.0) for t in question_tokens) or 1.0

        scored: list[tuple[Fragment, float]] = []
        for fragment, fragment_tokens in zip(fragments, fragment_token_list, strict=False):
            vector_score = cosine_similarity(
                query_vector,
                fragment.embedding_vector or fragment.embedding_json or [],
            )
            matched_idf = sum(idf.get(t, 1.0) for t in question_tokens & fragment_tokens)
            lexical_score = matched_idf / total_q_idf
            score = (vector_score * 0.6) + (lexical_score * 0.4)
            scored.append((fragment, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        seeds = [(fragment, score) for fragment, score in scored[:top_k]]
        if max_hops <= 0 or not seeds:
            direct = [Evidence(fragment=f, score=s, hop=0, path=[f.id]) for f, s in seeds]
            self._attach_sources(db, direct)
            return direct

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
        original_to_synthetic: dict[str, set[str]] = {}
        synthetic_to_original: dict[str, set[str]] = {}
        for fragment in fragments:
            orig_list = (fragment.metadata_json or {}).get("original_fragment_ids") or [fragment.id]
            for orig_id in orig_list:
                original_to_synthetic.setdefault(orig_id, set()).add(fragment.id)
                synthetic_to_original.setdefault(fragment.id, set()).add(orig_id)

        if adjacency:
            seed_orig_ids = {
                orig_id
                for f in fragments
                for orig_id in synthetic_to_original.get(f.id, {f.id})
            }
            connected_orig_ids = set(seed_orig_ids)
            frontier_orig_ids = set(seed_orig_ids)
            for _ in range(max_hops):
                next_orig_ids = {
                    neighbor_orig_id
                    for current_orig_id in frontier_orig_ids
                    for _, neighbor_orig_id in adjacency.get(current_orig_id, [])
                    if neighbor_orig_id not in connected_orig_ids
                }
                if not next_orig_ids:
                    break
                connected_orig_ids.update(next_orig_ids)
                frontier_orig_ids = next_orig_ids

            missing_orig_ids = connected_orig_ids - set(original_to_synthetic.keys())
            if missing_orig_ids:
                graph_fragments = db.scalars(
                    select(Fragment).where(Fragment.id.in_(missing_orig_ids))
                ).all()
                art_fragments = self._article_units(graph_fragments, db)
                for gf in art_fragments:
                    by_id[gf.id] = gf
                    orig_list = (gf.metadata_json or {}).get("original_fragment_ids") or [gf.id]
                    for o_id in orig_list:
                        original_to_synthetic.setdefault(o_id, set()).add(gf.id)
                        synthetic_to_original.setdefault(gf.id, set()).add(o_id)

        evidence: dict[str, Evidence] = {
            fragment.id: Evidence(fragment=fragment, score=score, hop=0, path=[fragment.id])
            for fragment, score in seeds
        }
        frontier = set(evidence)
        for hop in range(1, max_hops + 1):
            next_frontier: set[str] = set()
            for current_id in frontier:
                current = evidence[current_id]
                current_orig_ids = synthetic_to_original.get(current_id, {current_id})
                for c_orig_id in current_orig_ids:
                    for edge, neighbor_orig_id in adjacency.get(c_orig_id, []):
                        target_synthetic_ids = original_to_synthetic.get(neighbor_orig_id, {neighbor_orig_id})
                        for target_syn_id in target_synthetic_ids:
                            neighbor = by_id.get(target_syn_id)
                            if not neighbor or target_syn_id in current.path or neighbor_orig_id in current.path:
                                continue
                            relation_weight = RELATION_WEIGHTS.get(edge.relation_type, 0.6)
                            candidate_score = current.score * relation_weight / hop
                            candidate_path = [*current.path, target_syn_id]
                            previous = evidence.get(target_syn_id)
                            if previous and previous.score >= candidate_score:
                                continue
                            evidence[target_syn_id] = Evidence(
                                fragment=neighbor,
                                score=candidate_score,
                                hop=hop,
                                path=candidate_path,
                                via_relation=edge.relation_type,
                            )
                            next_frontier.add(target_syn_id)
            frontier = next_frontier
            if not frontier:
                break

        self._expand_links(db, evidence, max_hops, allowed, question_tokens)
        ranked = sorted(
            evidence.values(),
            key=lambda item: (item.link_id is None, item.hop, -item.score),
        )
        ranked = ranked[: top_k * 3]
        self._attach_sources(db, ranked)
        return ranked

    @staticmethod
    def _attach_sources(db: Session, evidence: list[Evidence]) -> None:
        """Every chunk shows the document it came from and where inside it."""
        version_ids = {item.fragment.version_id for item in evidence if not item.filename}
        by_version = (
            {
                version_id: (document_id, filename)
                for version_id, document_id, filename in db.execute(
                    select(DocumentVersion.id, Document.id, Document.filename).join(
                        Document, Document.id == DocumentVersion.document_id
                    ).where(DocumentVersion.id.in_(version_ids))
                ).all()
            }
            if version_ids
            else {}
        )
        for item in evidence:
            if not item.filename:
                found = by_version.get(item.fragment.version_id)
                if found:
                    item.document_id, item.filename = found
            item.location = _location_label(item.fragment, item.selection)
            item.version_id = item.fragment.version_id
            item.page = _location_page(item.fragment, item.selection)

    def _search_units(self, db: Session, fragments: list[Fragment]) -> list[Fragment]:
        """Search PPT slides as one unit instead of ranking every text box."""
        parent_ids = {fragment.parent_id for fragment in fragments if fragment.parent_id}
        parents = (
            {
                parent.id: parent
                for parent in db.scalars(select(Fragment).where(Fragment.id.in_(parent_ids))).all()
            }
            if parent_ids
            else {}
        )
        units: dict[str, Fragment] = {}
        for fragment in fragments:
            parent = parents.get(fragment.parent_id or "")
            unit = parent if parent and parent.kind == "slide" and parent.text else fragment
            if (unit.text or "").strip():
                units[unit.id] = unit
        return list(units.values())

    def _article_units(self, fragments: list[Fragment], db: Session | None = None) -> list[Fragment]:
        contents: dict[str, DocumentContent] = {}
        if db:
            version_ids = {fragment.version_id for fragment in fragments if fragment.kind == "document"}
            if version_ids:
                contents = {
                    content.version_id: content
                    for content in db.scalars(
                        select(DocumentContent).where(DocumentContent.version_id.in_(version_ids))
                    ).all()
                }

        reconstructed: dict[tuple[str, str, int], tuple[int, Fragment, set[str]]] = {}
        units: list[Fragment] = []
        for fragment in fragments:
            content = contents.get(fragment.version_id)
            metadata = fragment.metadata_json or {}
            if (
                fragment.kind == "document"
                and content
                and content.kind == "text"
                and metadata.get("text_start") is not None
                and metadata.get("text_end") is not None
            ):
                matches = list(ARTICLE_HEADING_RE.finditer(content.text))
                if matches:
                    chunk_start = metadata.get("chunk_start")
                    chunk_end = metadata.get("chunk_end")
                    if chunk_start is None or chunk_end is None:
                        chunk_start = _utf16_index(content.text, int(metadata["text_start"]))
                        chunk_end = _utf16_index(content.text, int(metadata["text_end"]))
                    for index, match in enumerate(matches):
                        article_start = match.start(1)
                        article_end = (
                            matches[index + 1].start(1)
                            if index + 1 < len(matches)
                            else len(content.text)
                        )
                        if article_start >= chunk_end or article_end <= chunk_start:
                            continue
                        raw_text = content.text[article_start:article_end]
                        text_value = raw_text.strip()
                        if not text_value:
                            continue
                        value_start = article_start + len(raw_text) - len(raw_text.lstrip())
                        text_start = utf16_length(content.text[:value_start])
                        text_end = text_start + utf16_length(text_value)
                        article = match.group(1)
                        key = (fragment.version_id, article, article_start)
                        previous = reconstructed.get(key)
                        orig_ids = set(previous[2]) if previous else set()
                        orig_ids.add(fragment.id)
                        unit = Fragment(
                            id=f"{fragment.version_id}:article:{article}:{article_start}",
                            version_id=fragment.version_id,
                            parent_id=fragment.parent_id,
                            stable_key=f"{fragment.stable_key}:article:{article}:{article_start}",
                            kind=fragment.kind,
                            ordinal=fragment.ordinal,
                            title=fragment.title,
                            text=text_value,
                            html=None,
                            table_json=None,
                            locator_json={**fragment.locator_json, "article": article},
                            bbox_json=fragment.bbox_json,
                            asset_path=None,
                            content_hash=fragment.content_hash,
                            embedding_json=fragment.embedding_json,
                            embedding_vector=fragment.embedding_vector,
                            embedding_model=fragment.embedding_model,
                            metadata_json={
                                **metadata,
                                "text_start": text_start,
                                "text_end": text_end,
                                "canonical_article": True,
                                "original_fragment_ids": sorted(orig_ids),
                            },
                        )
                        candidate_rank = 0 if chunk_start <= article_start < chunk_end else 1
                        if previous is None or candidate_rank < previous[0]:
                            reconstructed[key] = (candidate_rank, unit, orig_ids)
                    continue

            matches = list(ARTICLE_HEADING_RE.finditer(fragment.text or ""))
            if fragment.kind != "document" or not matches:
                units.append(fragment)
                continue
            for index, match in enumerate(matches):
                raw_end = matches[index + 1].start() if index + 1 < len(matches) else len(fragment.text or "")
                raw_text = (fragment.text or "")[match.start():raw_end]
                text_value = raw_text.strip()
                if not text_value:
                    continue
                start = match.start() + len(raw_text) - len(raw_text.lstrip())
                metadata = dict(fragment.metadata_json or {})
                if metadata.get("text_start") is not None:
                    metadata["text_start"] += utf16_length((fragment.text or "")[:start])
                    metadata["text_end"] = metadata["text_start"] + utf16_length(text_value)
                metadata["original_fragment_ids"] = [fragment.id]
                article = match.group(1)
                units.append(
                    Fragment(
                        id=f"{fragment.id}:article:{article}:{index}",
                        version_id=fragment.version_id,
                        parent_id=fragment.parent_id,
                        stable_key=f"{fragment.stable_key}:article:{article}:{index}",
                        kind=fragment.kind,
                        ordinal=fragment.ordinal,
                        title=fragment.title,
                        text=text_value,
                        html=None,
                        table_json=None,
                        locator_json={**fragment.locator_json, "article": article},
                        bbox_json=fragment.bbox_json,
                        asset_path=None,
                        content_hash=fragment.content_hash,
                        embedding_json=fragment.embedding_json,
                        embedding_vector=fragment.embedding_vector,
                        embedding_model=fragment.embedding_model,
                        metadata_json=metadata,
                    )
                )
        return [unit for _, unit, _ in reconstructed.values()] + units

    def _expand_links(
        self,
        db: Session,
        evidence: dict[str, Evidence],
        max_hops: int,
        allowed: set[str],
        question_tokens: set[str],
    ) -> None:
        links = list(db.scalars(select(DocumentLink).where(DocumentLink.status == "approved")))
        contents = {c.version_id: c for c in db.scalars(select(DocumentContent))}
        for hop in range(1, max_hops + 1):
            frontier = [item for item in evidence.values() if item.hop == hop - 1]
            for current in frontier:
                for link in links:
                    if (allowed and link.relation_type not in allowed) or link.id in current.path:
                        continue
                    selections = [(link.source_selection, link.target_selection)]
                    if link.relation_type != "REFERENCES":
                        selections.append((link.target_selection, link.source_selection))
                    for source, target in selections:
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
                        if hop == 1 and current.fragment.title:
                            title_tokens = _search_tokens(current.fragment.title)
                            if not title_tokens & question_tokens:
                                source_tokens = _search_tokens(selection_text(content, source))
                                specific_matches = {
                                    token
                                    for token in question_tokens & source_tokens
                                    if (
                                        token.isascii() and len(token) >= 2
                                    ) or (
                                        len(token) >= 3
                                        and token
                                        not in {"열차", "전동차", "운전", "고장", "조치", "보고"}
                                    )
                                }
                                if not specific_matches:
                                    continue
                        for target_selection in self._relevant_target_selections(target, question_tokens):
                            target_key = json.dumps(target_selection, ensure_ascii=False, sort_keys=True)
                            key = f"link:{hashlib.sha256(target_key.encode()).hexdigest()}"
                            score = current.score * RELATION_WEIGHTS.get(link.relation_type, 0.7) / hop
                            if key in evidence and evidence[key].score >= score:
                                continue
                            version = db.get(DocumentVersion, target_selection["version_id"])
                            document = db.get(Document, version.document_id)
                            text_value = selection_text(target_content, target_selection).strip()
                            fragment = Fragment(
                                id=key, version_id=version.id, parent_id=None, stable_key=key,
                                kind=target_selection["kind"], ordinal=0, title=document.filename,
                                text=text_value or "텍스트 없는 페이지입니다. 원본을 확인하세요.",
                                html=None, table_json=None, bbox_json=None, asset_path=None,
                                locator_json={"pages": target_selection["pages"]}
                                if target_selection["kind"] == "pages"
                                else {"ranges": [{"start": part["start"], "end": part["end"]}
                                                 for part in text_ranges(target_selection)]},
                                content_hash="", metadata_json={},
                            )
                            evidence[key] = Evidence(
                                fragment=fragment, score=score, hop=hop,
                                path=[*current.path, link.id], via_relation=link.relation_type,
                                link_id=link.id, selection=target_selection,
                                document_id=document.id, filename=document.filename,
                            )

    @staticmethod
    def _relevant_target_selections(
        selection: dict,
        question_tokens: set[str],
    ) -> list[dict]:
        ranges = text_ranges(selection)
        if selection["kind"] != "text" or len(ranges) <= 3:
            return [selection]
        ranked = sorted(
            (
                len(question_tokens & _search_tokens(part.get("exact", ""))),
                index,
                part,
            )
            for index, part in enumerate(ranges)
        )
        ranked.sort(key=lambda item: (-item[0], item[1]))
        best = ranked[0][0]
        cutoff = max(1, best - 1)
        selected = [item for item in ranked if item[0] >= cutoff][:3]
        if not selected:
            selected = ranked[:3]
        selected.sort(key=lambda item: item[1])
        return [{**selection, "ranges": [part for _, _, part in selected]}]

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
            locator = ", ".join(
                part
                for part in (
                    item.filename or item.fragment.title,
                    item.location or _location_label(item.fragment, item.selection),
                )
                if part
            )
            context_parts.append(
                f"[근거 {index} | hop={item.hop} | {locator}]\n"
                f"{item.fragment.text or '(텍스트 없음)'}"
            )
        context = "\n\n".join(context_parts)
        if self.settings.openai_api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=self.settings.openai_api_key)
                response = client.chat.completions.create(
                    model=model or self.settings.llm_model,
                    temperature=1,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "문서 근거만 사용해 한국어로 답변하세요. 질문의 핵심 조건을 첫 문장에 재진술하고, "
                                "질문에 직접 관련된 조치만 3~5개 항목으로 간결하게 답하세요. "
                                "검색 결과의 짧은 도형 라벨이나 코드만으로 내용을 추측하지 말고, 서로 다른 근거가 충돌하면 "
                                "원문 규정에 우선순위를 두세요. 근거가 부족하면 모른다고 말하고, 답변 끝에 [근거 n] 형식으로 "
                                "참조하세요. 그래프 hop이 0보다 큰 근거는 연결된 관련 자료임을 명시하세요."
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
