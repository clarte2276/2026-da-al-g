from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import re
import shutil
import statistics
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import numpy as np
from dotenv import dotenv_values
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Document, DocumentLink, DocumentVersion, Fragment
from app.services.rag import GraphRAGService, _Corpus, _embedding_values, _search_tokens

HERE = Path(__file__).resolve().parent
PAPER_ROOT = HERE.parent
DATA_DIR, CACHE_DIR = HERE / "data", HERE / "cache"
COST_CACHE_DIR, CACHE_SETTING = CACHE_DIR, "baseline"
OPENAI_TOKEN_ESTIMATE_PER_CHAR, OPENAI_PAIR_BATCH_SIZE = 2.0, 80
SUMMARY_DIR, RUNS_DIR = HERE / "summary", HERE / "runs"
DB_DIR = PAPER_ROOT / "runtime"
SEED, K, K_RECALL, BATCH_SIZE, JEV_BATCH_SIZE = 20261017, 10, 100, 8, 1
JEV_PAIR_CANDIDATES_PER_REQUEST = 10
REPEATS = ("r1", "r2", "r3")
UNCERTAINTY_BAND = (0.2, 0.8)
OPENAI_CAP_USD, JEV_CAP_USD = 15.0, 5.0
OPENAI_PRICE = {"input": 0.20, "cached_input": 0.02, "output": 1.20}
JEV_INPUT_PRICE = 0.042
OPENAI_PRICE_URL = "https://developers.openai.com/api/docs/models/gpt-5.6-luna"
OPENAI_EMBEDDING_PRICE = 0.02
OPENAI_EMBEDDING_PRICE_URL = "https://developers.openai.com/api/docs/models/text-embedding-3-small"
JEV_PRICE_URL = "https://docs.typesafe.ai/llms.txt"

RELATION_QUESTION = "Does this guide slide require or reference this regulation article?"
RELATION_RULE = (
    "Answer yes only when the article is directly needed to apply, explain, or support the slide's procedure. "
    "Shared topic, nearby text, or a merely plausible legal basis is not enough."
)
PAIR_INSTRUCTION = f"{RELATION_QUESTION} {RELATION_RULE}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def database_url(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def source_id(version_id: str, page: int) -> str:
    return f"slide_{version_id[:8]}_{int(page):03d}"


def article_id(version_id: str, article_no: str) -> str:
    return f"article_{version_id[:8]}_{article_no}"


def article_number(value: str) -> str | None:
    match = re.search(r"\uC81C\s*(\d+)\s*\uC870", value or "")
    return str(int(match.group(1))) if match else None


def stored_embedding(fragment: Fragment) -> np.ndarray:
    value = fragment.embedding_vector or fragment.embedding_json
    return np.asarray(value, dtype=np.float32) if isinstance(value, list) else _embedding_values(value)


def load_data() -> dict[str, Any]:
    return read_json(DATA_DIR / "experiment_data.json")


def make_prompts() -> None:
    prompts = {
        "common.md": f"# Shared link criterion\n\n{PAIR_INSTRUCTION}\n",
        "jev_pair.md": (
            "# Jev pair prompt\n\nState is JSON with a pairs array. For each question id, use the corresponding "
            "slide/article pair in state and answer the shared link criterion as a probability.\n\n"
            f"{PAIR_INSTRUCTION}\n"
        ),
        "jev_choice.md": (
            "# Jev choice prompt\n\nEach question names one source slide; its criteria contain candidate article ids and none. "
            "Choose the one candidate with the strongest direct link, or none.\n\n" + PAIR_INSTRUCTION + "\n"
        ),
        "llm_pair.json": json.dumps({
            "system": f"{PAIR_INSTRUCTION} For each pair, return yes/no and confidence from 0 to 1 in that decision. "
                      "Return JSON with a pairs array containing pair_id, decision, and confidence for every pair.",
            "user_shape": {"relation_question": RELATION_QUESTION, "decision_rule": RELATION_RULE,
                           "pairs": "source text and candidate article text"},
        }, ensure_ascii=False, indent=2),
        "llm_list.json": json.dumps({
            "system": f"{PAIR_INSTRUCTION} For each slide_key, select zero or more candidate_keys and return p_yes in [0,1] for every candidate_key. "
                      "Return JSON items with slide_key, selected_candidate_keys, and p_yes mapping candidate_key to probability.",
            "user_shape": {"relation_question": RELATION_QUESTION, "decision_rule": RELATION_RULE,
                           "slides": "source text and candidate article lists"},
        }, ensure_ascii=False, indent=2),
        "cascade.md": (
            "# Jev-to-LLM cascade\n\nUse Jev pair probability first. Send only pairs with Jev probability in "
            "[0.20, 0.80] to the same LLM pair prompt; retain Jev outside the band.\n\n" + PAIR_INSTRUCTION + "\n"
        ),
    }
    folder = HERE / "prompts"
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in prompts.items():
        (folder / name).write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8")


def prepare(args: argparse.Namespace) -> None:
    db_path, eval_path = args.db.resolve(), args.eval_set.resolve()
    if not db_path.is_file() or not eval_path.is_file():
        raise FileNotFoundError("Both the source DB and eval set must exist.")
    engine = create_engine(database_url(db_path))
    with Session(engine) as db:
        approved = sorted(
            db.scalars(select(DocumentLink).where(DocumentLink.status == "approved")).all(),
            key=lambda item: item.id,
        )
        if len(approved) != 36:
            raise ValueError(f"Expected 36 approved link records, found {len(approved)}")
        target_versions = {link.target_version_id for link in approved}
        if len(target_versions) != 1:
            raise ValueError(f"Expected one regulation version, found {len(target_versions)}")
        target_version = next(iter(target_versions))
        filenames = {item.id: item.filename for item in db.scalars(select(Document)).all()}
        regulation_version = db.get(DocumentVersion, target_version)
        regulation_filename = filenames.get(regulation_version.document_id, "") if regulation_version else ""
        guide_versions = list(db.scalars(
            select(DocumentVersion)
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(Document.mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        ).all())
        guide_version_ids = {version.id for version in guide_versions}
        slides = db.scalars(select(Fragment).where(
            Fragment.version_id.in_(guide_version_ids), Fragment.kind == "slide"
        )).all()
        slide_by_key: dict[tuple[str, int], list[Fragment]] = defaultdict(list)
        for slide in slides:
            locator = slide.locator_json or {}
            page = locator.get("page", locator.get("slide", (slide.ordinal or 0) + 1))
            slide_by_key[(slide.version_id, int(page))].append(slide)

        gold_by_slide: dict[tuple[str, int], set[str]] = defaultdict(set)
        gold_links = []
        positive_keys: set[tuple[str, int]] = set()
        for link in approved:
            selection = link.source_selection or {}
            if selection.get("kind") != "pages" or selection.get("version_id") not in guide_version_ids:
                raise ValueError(f"Approved link {link.id} does not point to a guide slide selection")
            pages = sorted({int(page) for page in selection.get("pages", [])})
            articles = []
            for span in (link.target_selection or {}).get("ranges", []):
                number = article_number(span.get("exact", ""))
                if number is None:
                    raise ValueError(f"Could not parse article number from approved link {link.id}")
                articles.append(number)
            articles = sorted(set(articles), key=int)
            for page in pages:
                key = (selection["version_id"], page)
                if key not in slide_by_key:
                    raise ValueError(f"Source slide {key} is missing from DB")
                positive_keys.add(key)
                gold_by_slide[key].update(articles)
            gold_links.append({
                "link_id": link.id, "source_version_id": selection["version_id"], "source_pages": pages,
                "target_version_id": link.target_version_id, "target_articles": articles,
                "source_filename": filenames.get(selection["version_id"], ""),
            })

        target_fragments = db.scalars(select(Fragment).where(Fragment.version_id == target_version)).all()
        service = GraphRAGService(None, None)
        embedding_sources: dict[str, str] = {}
        target_units = service._article_units(
            service._search_units(db, target_fragments, defer_embeddings=True), db,
            include_embeddings=False, embedding_source_ids=embedding_sources,
        )
        articles: dict[str, dict[str, Any]] = {}
        article_units = []
        for unit in target_units:
            # The parser's broad heading matcher also sees numbered references in prose.
            if not re.match(r"^\uC81C\s*\d+\s*\uC870\s*\(", unit.text or ""):
                continue
            number = article_number((unit.locator_json or {}).get("article", ""))
            if number is None:
                continue
            if number in articles:
                raise ValueError(f"Duplicate regulation article {number}")
            metadata = unit.metadata_json or {}
            if metadata.get("text_start") is None or metadata.get("text_end") is None:
                raise ValueError(f"Article {number} has no source offsets")
            articles[number] = {
                "id": article_id(target_version, number), "number": number, "version_id": target_version,
                "text": unit.text or "", "start": int(metadata["text_start"]),
                "end": int(metadata["text_end"]), "title": (unit.title or "").strip(),
            }
            article_units.append(unit)
        missing = sorted(
            {number for link in gold_links for number in link["target_articles"]} - articles.keys(),
            key=int,
        )
        if missing:
            raise ValueError(f"Approved article ranges absent from corpus: {missing}")
        embedding_ids = list(dict.fromkeys(embedding_sources.get(unit.id, unit.id) for unit in article_units))
        corpus = _Corpus.build(
            article_units,
            embedding_rows=lambda ids=embedding_ids: service._stream_embeddings(db, ids),
            embedding_source_ids=embedding_sources,
        )

        positives = sorted(positive_keys)
        negative_pool = sorted(set(slide_by_key) - positive_keys)
        if not negative_pool:
            raise ValueError("No unlinked guide slides are available for negatives")
        # shortcut: a pool smaller by three needs three repeated draws; add three unlinked slides to avoid replacement.
        rng = random.Random(SEED)
        negatives = (rng.sample(negative_pool, len(positives)) if len(negative_pool) >= len(positives)
                     else negative_pool + rng.choices(negative_pool, k=len(positives) - len(negative_pool)))
        rng.shuffle(negatives)
        negative_draws: dict[tuple[str, int], int] = defaultdict(int)
        sources = []
        chosen = [(key, "positive") for key in positives] + [(key, "negative") for key in negatives]
        for key, role in chosen:
            version, page = key
            page_fragments = slide_by_key[key]
            text_parts = list(dict.fromkeys((fragment.text or "").strip() for fragment in page_fragments if (fragment.text or "").strip()))
            slide_text = "\n\n".join(text_parts)
            vectors = [stored_embedding(fragment) for fragment in page_fragments]
            vectors = [vector for vector in vectors if len(vector)]
            if not vectors:
                raise ValueError(f"Slide {key} has no stored embedding")
            vector = vectors[0].copy()
            for extra in vectors[1:]:
                if len(extra) != len(vector):
                    raise ValueError(f"Slide fragments have mixed embedding dimensions: {key}")
                vector += extra
            title = next((fragment.title for fragment in page_fragments if fragment.title), "")
            query = f"{title}\n{slide_text}"
            scores = corpus.scores(vector.tolist(), _search_tokens(query))
            ranked = sorted(
                zip(article_units, scores, strict=True),
                key=lambda item: (-item[1], int(article_number((item[0].locator_json or {}).get("article", "")) or 0)),
            )[:K_RECALL]
            candidates = []
            for unit, score in ranked:
                number = article_number((unit.locator_json or {}).get("article", ""))
                candidates.append({"article_id": articles[number]["id"], "article": number, "score": round(float(score), 8)})
            sid = source_id(version, page)
            if role == "negative":
                negative_draws[key] += 1
                sid = f"{sid}_sample{negative_draws[key]:02d}"
            sources.append({
                "source_id": sid, "role": role, "source_version_id": version,
                "source_filename": filenames.get(version, ""), "page": page,
                "selection": {"kind": "pages", "version_id": version, "pages": [page]},
                "title": title or "", "text": slide_text,
                "gold_articles": sorted(gold_by_slide.get(key, set()), key=int),
                "candidates_20": candidates[:20], "candidates_100": candidates,
            })
        if len(positives) != 80 or len(negatives) != 80:
            raise ValueError(f"Unexpected sample size: {len(positives)} positive slides, {len(negatives)} negatives")
        source_map = {source["source_id"]: source for source in sources}
        metric_groups = []
        gold_edges = []
        for link in gold_links:
            member_ids = [source_id(link["source_version_id"], page) for page in link["source_pages"]]
            group_id = "link_" + link["link_id"]
            candidate_map = {}
            for sid in member_ids:
                for candidate in source_map[sid]["candidates_20"][:K]:
                    previous = candidate_map.get(candidate["article_id"])
                    if previous is None or candidate["score"] > previous["score"]:
                        candidate_map[candidate["article_id"]] = candidate
            group = {
                "source_id": group_id, "role": "positive", "link_id": link["link_id"],
                "source_ids": member_ids, "source_version_id": link["source_version_id"],
                "source_pages": link["source_pages"], "source_filename": link["source_filename"],
                "selection": {"kind": "pages", "version_id": link["source_version_id"], "pages": link["source_pages"]},
                "title": " / ".join(source_map[sid]["title"] for sid in member_ids if source_map[sid]["title"]),
                "text": "\n\n".join(source_map[sid]["text"] for sid in member_ids if source_map[sid]["text"]),
                "gold_articles": link["target_articles"],
                "candidates": sorted(candidate_map.values(), key=lambda item: (-item["score"], int(item["article"]))),
            }
            metric_groups.append(group)
            gold_edges.extend({
                "source_id": group_id, "article_id": articles[number]["id"], "article": number,
                "link_id": link["link_id"],
            } for number in link["target_articles"])
        for source in sources:
            if source["role"] == "negative":
                metric_groups.append({
                    "source_id": source["source_id"], "role": "negative", "link_id": None,
                    "source_ids": [source["source_id"]], "source_version_id": source["source_version_id"],
                    "source_pages": [source["page"]], "source_filename": source["source_filename"],
                    "selection": source["selection"], "title": source["title"], "text": source["text"],
                    "gold_articles": [],
                    "candidates": source["candidates_20"][:K],
                })
        edge_count = len(gold_edges)
        if len(metric_groups) != len(gold_links) + len(negatives):
            raise ValueError("Metric groups must contain each approved selection and negative draw exactly once")
        eval_obj = read_json(eval_path)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(eval_path, DATA_DIR / "eval_set_v3.json")
        data = {
            "seed": SEED, "k": K, "candidate_k_recall": K_RECALL,
            "hybrid_weights": {"dense": 0.6, "bm25": 0.4},
            "embedding_model": "stored DB embeddings (text-embedding-3-small)",
            "regulation_filename": regulation_filename,
            "guide_slide_count": len(slide_by_key), "positive_slide_count": len(positives),
            "negative_slide_count": len(negatives), "gold_link_record_count": len(gold_links),
            "negative_unique_slide_count": len(set(negatives)),
            "gold_article_range_count": sum(len(link["target_articles"]) for link in gold_links),
            "gold_edge_count": edge_count, "target_version_id": target_version,
            "sources": sources, "metric_groups": metric_groups, "articles": articles,
            "gold_links": gold_links, "gold_edges": gold_edges,
            "eval_set": {
                "version": eval_obj.get("version"), "case_count": len(eval_obj.get("cases", [])),
                "graph_case_count": sum(case.get("category") == "graph" for case in eval_obj.get("cases", [])),
                "via_link_gold_count": sum(item.get("via_link", False) for case in eval_obj.get("cases", []) for item in case.get("gold_evidence", [])),
            },
        }
    engine.dispose()
    write_json(DATA_DIR / "experiment_data.json", data)
    make_prompts()
    print(json.dumps({key: data[key] for key in (
        "seed", "guide_slide_count", "positive_slide_count", "negative_slide_count",
        "gold_link_record_count", "gold_article_range_count", "gold_edge_count", "eval_set",
    )}, ensure_ascii=False, indent=2))


def load_env(args: argparse.Namespace) -> tuple[str, str, str]:
    openai_env = dotenv_values(args.openai_env) if getattr(args, "openai_env", None) else {}
    jev_env = dotenv_values(args.jev_env) if getattr(args, "jev_env", None) else {}
    openai_key = os.environ.get("OPENAI_API_KEY") or openai_env.get("OPENAI_API_KEY") or ""
    jev_key = os.environ.get("JEV_API_KEY") or jev_env.get("JEV_API_KEY") or ""
    model = os.environ.get("LLM_MODEL") or openai_env.get("LLM_MODEL") or "gpt-5.6-luna"
    return str(openai_key), str(jev_key), str(model)


def token_count(usage: dict[str, Any], aliases: tuple[str, ...]) -> int:
    for key in aliases:
        if isinstance(usage.get(key), (int, float)):
            return int(usage[key])
    nested = usage.get("tokens") or usage.get("token_usage") or {}
    if isinstance(nested, dict):
        for key in aliases:
            if isinstance(nested.get(key), (int, float)):
                return int(nested[key])
    return 0


def cached_call_records() -> list[dict[str, Any]]:
    rows = []
    if COST_CACHE_DIR.exists():
        for path in COST_CACHE_DIR.rglob("*.json"):
            try:
                item = read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(item, dict) and item.get("_api_call"):
                rows.append(item)
    return rows


def total_spend(provider: str) -> float:
    if provider == "openai":
        from tracking_openai import spend_so_far

        return spend_so_far()
    return sum(float(item.get("cost_usd", 0)) for item in cached_call_records() if item.get("provider") == provider)


def api_cost(provider: str, usage: dict[str, Any]) -> tuple[dict[str, int], float]:
    input_tokens = token_count(usage, ("input_tokens", "prompt_tokens", "input"))
    output_tokens = token_count(usage, ("output_tokens", "completion_tokens", "output"))
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    cached = min(input_tokens, int(details.get("cached_tokens", details.get("cached_input_tokens", 0)) or 0)) if isinstance(details, dict) else 0
    if provider == "openai":
        cost = ((input_tokens - cached) * OPENAI_PRICE["input"] + cached * OPENAI_PRICE["cached_input"] + output_tokens * OPENAI_PRICE["output"]) / 1_000_000
    else:
        cost = input_tokens * JEV_INPUT_PRICE / 1_000_000
    return {"input_tokens": input_tokens, "cached_input_tokens": cached, "output_tokens": output_tokens}, cost


def estimate_cost(provider: str, chars: int, max_output: int = 4096) -> float:
    tokens = chars * (OPENAI_TOKEN_ESTIMATE_PER_CHAR if provider == "openai" else 2)
    return ((tokens * OPENAI_PRICE["input"] + max_output * OPENAI_PRICE["output"]) / 1_000_000
            if provider == "openai" else tokens * JEV_INPUT_PRICE / 1_000_000)


def api_request(provider: str, judge: str, repeat: str, cache_path: Path, payload: dict[str, Any], key: str, model: str) -> dict[str, Any]:
    if cache_path.is_file():
        return read_json(cache_path)
    serialized = json.dumps(payload, ensure_ascii=False)
    cap = OPENAI_CAP_USD if provider == "openai" else JEV_CAP_USD
    if total_spend(provider) + estimate_cost(provider, len(serialized)) > cap:
        raise RuntimeError(f"{provider} budget guard stopped before a call: conservative estimate crosses USD {cap:.2f}")
    started = time.perf_counter()
    if provider == "jev":
        response = requests.post(
            "https://api.typesafe.ai/v1/systemone",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload, timeout=120,
        )
    else:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload, timeout=120,
        )
    latency = time.perf_counter() - started
    if response.status_code >= 400:
        raise RuntimeError(f"{provider} API returned HTTP {response.status_code}: {response.text[:500]}")
    raw = response.json()
    token_usage, cost = api_cost(provider, raw.get("usage") or {})
    record = {
        "_api_call": True, "provider": provider, "judge": judge, "repeat": repeat,
        "candidate_setting": CACHE_SETTING,
        "model": "jev-latest" if provider == "jev" else model,
        "latency_seconds": latency, "usage": token_usage, "cost_usd": cost,
        "response": raw, "created_at_utc": datetime.now(UTC).isoformat(),
    }
    write_json(cache_path, record)
    if total_spend(provider) > cap:
        raise RuntimeError(f"{provider} reached the USD {cap:.2f} cap; stopped after recording the call")
    return record


def batches(rows: list[dict[str, Any]], size: int = BATCH_SIZE) -> list[list[dict[str, Any]]]:
    return [rows[index:index + size] for index in range(0, len(rows), size)]


def hash_key(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(text).hexdigest()[:16]


def output_sources(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**source, "candidates": source.get("candidates", source["candidates_20"][:K])}
            for source in data["sources"]]


def pair_batch_content(batch: list[dict[str, Any]], data: dict[str, Any]) -> list[dict[str, Any]]:
    return [{
        "source_id": source["source_id"], "source_filename": source["source_filename"],
        "page": source["page"], "slide_title": source["title"], "slide_text": source["text"],
        "candidates": [{
            "candidate_id": candidate["article_id"], "article": candidate["article"],
            "hybrid_score": candidate["score"], "article_text": data["articles"][candidate["article"]]["text"],
        } for candidate in source["candidates"]],
    } for source in batch]


def openai_request(model: str, system: str, user: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model, "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": json.dumps(user, ensure_ascii=False)}],
        "response_format": {"type": "json_object"}, "reasoning_effort": "none",
        "temperature": 0, "max_completion_tokens": 4096,
    }


def response_json(record: dict[str, Any]) -> dict[str, Any]:
    if record["provider"] == "jev":
        return record["response"]
    content = record["response"]["choices"][0]["message"].get("content") or "{}"
    return json.loads(content)


def parse_jev_pair(record: dict[str, Any], q_to_pair: dict[str, tuple[str, str]]) -> list[dict[str, Any]]:
    answers = response_json(record).get("answers", {})
    rows = []
    for qid, pair in q_to_pair.items():
        answer = answers.get(qid)
        if not isinstance(answer, dict) or not isinstance(answer.get("noul"), (int, float)):
            raise ValueError(f"Jev pair response is missing probability for {qid}")
        probability = float(answer["noul"])
        if not 0 <= probability <= 1:
            raise ValueError(f"Jev returned invalid probability for {qid}")
        rows.append({"source_id": pair[0], "candidate_id": pair[1], "probability": probability})
    return rows


def normalize_probability(value: Any) -> float:
    if isinstance(value, dict):
        value = value.get("probability", value.get("p", value.get("confidence")))
    if not isinstance(value, (int, float)):
        raise ValueError(f"Expected probability, got {value!r}")
    probability = float(value)
    if 1 < probability <= 100:
        probability /= 100
    if not 0 <= probability <= 1:
        raise ValueError(f"Probability outside [0,1]: {probability}")
    return probability


def choice_probabilities(answer: dict[str, Any], candidate_ids: list[str]) -> tuple[str, dict[str, float]]:
    choice = str(answer.get("choice", "none"))
    probabilities = answer.get("probabilities") or {}
    if isinstance(probabilities, list):
        probabilities = dict(zip(candidate_ids + ["none"], probabilities))
    if not isinstance(probabilities, dict):
        raise ValueError("Jev choice probabilities are not a map")
    mapped = {candidate: normalize_probability(probabilities.get(candidate, 0.0)) for candidate in candidate_ids}
    return choice, mapped


def run_jev_pair(data: dict[str, Any], key: str, repeat: str) -> None:
    batch_no = 0
    for source in output_sources(data):
        for candidate_chunk in batches(source["candidates"], size=JEV_PAIR_CANDIDATES_PER_REQUEST):
            batch = [{**source, "candidates": candidate_chunk}]
            contents = pair_batch_content(batch, data)
            questions, q_to_pair, pairs = {}, {}, []
            for q_index, candidate in enumerate(contents[0]["candidates"]):
                qid = f"q{q_index:03d}"
                q_to_pair[qid] = (contents[0]["source_id"], candidate["candidate_id"])
                questions[qid] = {"type": "noul", "instructions": f"For pair {qid} in state, {PAIR_INSTRUCTION}"}
                pairs.append({
                    "question_id": qid, "source_id": contents[0]["source_id"],
                    "candidate_id": candidate["candidate_id"], "slide_text": contents[0]["slide_text"],
                    "article_text": candidate["article_text"],
                })
            payload = {"model": "jev-latest",
                       "state": {"relation_question": RELATION_QUESTION, "decision_rule": RELATION_RULE, "pairs": pairs},
                       "questions": questions}
            cache = CACHE_DIR / "jev_pair" / repeat / f"batch_{batch_no:03d}_{hash_key(list(q_to_pair.values()))}.json"
            record = api_request("jev", "jev_pair", repeat, cache, payload, key, "jev-latest")
            if not record.get("parsed_scores"):
                record["parsed_scores"] = parse_jev_pair(record, q_to_pair)
                write_json(cache, record)
            batch_no += 1


def run_jev_choice(data: dict[str, Any], key: str, repeat: str) -> None:
    for batch_no, batch in enumerate(batches(output_sources(data), size=JEV_BATCH_SIZE)):
        contents = pair_batch_content(batch, data)
        questions, question_sources = {}, {}
        for source in contents:
            qid = "q_" + source["source_id"]
            question_sources[qid] = source["source_id"]
            criteria = {c["candidate_id"]: f"Article {c['article']}: {c['article_text']}" for c in source["candidates"]}
            criteria["none"] = "No candidate article is required or referenced by this slide."
            questions[qid] = {
                "type": "choice",
                "instructions": f"For source {source['source_id']}, {PAIR_INSTRUCTION} Choose the most directly related candidate or none.",
                "criteria": criteria,
            }
        payload = {"model": "jev-latest",
                   "state": {"relation_question": RELATION_QUESTION, "decision_rule": RELATION_RULE,
                             "sources": [{"source_id": s["source_id"], "slide_text": s["slide_text"]} for s in contents]},
                   "questions": questions}
        cache = CACHE_DIR / "jev_choice" / repeat / f"batch_{batch_no:03d}_{hash_key(list(question_sources.values()))}.json"
        record = api_request("jev", "jev_choice", repeat, cache, payload, key, "jev-latest")
        if not record.get("parsed_scores"):
            answers = response_json(record).get("answers", {})
            parsed = []
            for qid, sid in question_sources.items():
                source = next(s for s in batch if s["source_id"] == sid)
                answer = answers.get(qid)
                if not isinstance(answer, dict):
                    raise ValueError(f"Jev choice response missing {qid}")
                choice, probabilities = choice_probabilities(answer, [c["article_id"] for c in source["candidates"]])
                for cid in [c["article_id"] for c in source["candidates"]]:
                    parsed.append({"source_id": sid, "candidate_id": cid, "probability": probabilities[cid], "choice": choice})
            record["parsed_scores"] = parsed
            write_json(cache, record)


def parse_llm_pairs(
    obj: dict[str, Any], expected: set[tuple[str, str]], pair_ids: dict[str, tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    items = obj.get("pairs", obj.get("items", []))
    rows = []
    if isinstance(items, dict):
        for sid, candidates in items.items():
            if isinstance(candidates, dict):
                rows.extend({"source_id": sid, "candidate_id": cid, **value}
                            for cid, value in candidates.items() if isinstance(value, dict))
    elif isinstance(items, list):
        rows = items
    out, seen = [], set()
    for row in rows:
        pair = (pair_ids or {}).get(str(row.get("pair_id", "")))
        if pair is None:
            pair = (str(row.get("source_id", "")), str(row.get("candidate_id", "")))
        if pair not in expected or pair in seen:
            continue
        decision = str(row.get("decision", row.get("label", ""))).lower()
        if decision not in {"yes", "no"}:
            raise ValueError(f"LLM pair has invalid decision for {pair}")
        confidence = normalize_probability(row.get("confidence", row.get("probability", row.get("p_yes"))))
        out.append({"source_id": pair[0], "candidate_id": pair[1], "decision": decision,
                    "confidence": confidence, "probability": confidence if decision == "yes" else 1 - confidence})
        seen.add(pair)
    return out


def parse_llm_list(
    obj: dict[str, Any], source_candidates: dict[str, list[str]],
    source_keys: dict[str, str] | None = None,
    candidate_keys: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    items = obj.get("items", {})
    if isinstance(items, list):
        items = {str(item.get("slide_key", item.get("source_id"))): item for item in items}
    if not isinstance(items, dict):
        raise ValueError("LLM list response items must be a map or list")
    source_keys = source_keys or {sid: sid for sid in source_candidates}
    candidate_keys = candidate_keys or {sid: {cid: cid for cid in cids} for sid, cids in source_candidates.items()}
    out = []
    for slide_key, sid in source_keys.items():
        item = items.get(slide_key, items.get(sid))
        if not isinstance(item, dict):
            continue
        key_to_id = candidate_keys[slide_key]
        probabilities = item.get("p_yes", item.get("probabilities", {}))
        if not isinstance(probabilities, dict):
            continue
        normalized = {key_to_id.get(str(key), str(key)): value for key, value in probabilities.items()}
        selected = item.get("selected_candidate_keys", item.get("selected_candidate_ids", item.get("selected", [])))
        selected = {key_to_id.get(str(key), str(key)) for key in selected} if isinstance(selected, list) else set()
        for cid in source_candidates[sid]:
            if cid in normalized:
                p = normalize_probability(normalized[cid])
                out.append({"source_id": sid, "candidate_id": cid, "probability": p, "selected": cid in selected})
    return out


def openai_pairs(
    data: dict[str, Any], key: str, model: str, repeat: str, judge_name: str,
    pair_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for batch_no, start in enumerate(range(0, len(pair_rows), OPENAI_PAIR_BATCH_SIZE)):
        pending = pair_rows[start:start + OPENAI_PAIR_BATCH_SIZE]
        for attempt in range(4):
            expected = {(p["source_id"], p["candidate_id"]) for p in pending}
            pair_ids = {f"p{index:03d}": pair for index, pair in enumerate(sorted(expected))}
            wire_pairs = []
            by_pair = {(p["source_id"], p["candidate_id"]): p for p in pending}
            for pair_id, pair in pair_ids.items():
                row = by_pair[pair]
                wire_pairs.append({"pair_id": pair_id, "source_id": pair[0], "candidate_id": pair[1],
                                   "slide_text": row["slide_text"], "article": row["article"],
                                   "article_text": row["article_text"]})
            system = (
                f"{PAIR_INSTRUCTION} For every pair_id return a decision yes or no and confidence from 0 to 1 in that decision. "
                "Return only JSON with a pairs array containing every requested pair_id exactly once; each row must include "
                "pair_id, decision, and confidence."
            )
            payload = openai_request(model, system, {
                "relation_question": RELATION_QUESTION, "decision_rule": RELATION_RULE, "pairs": wire_pairs,
            })
            batch_key = hash_key(sorted(expected))
            suffix = f"_{batch_key}" if attempt == 0 else f"_retry{attempt}_{batch_key}"
            cache = CACHE_DIR / judge_name / repeat / f"batch_{batch_no:03d}{suffix}.json"
            record = api_request("openai", judge_name, repeat, cache, payload, key, model)
            if "parsed_scores" not in record:
                record["parsed_scores"] = parse_llm_pairs(response_json(record), expected, pair_ids)
                write_json(cache, record)
            parsed = record["parsed_scores"]
            result.extend(parsed)
            completed = {(row["source_id"], row["candidate_id"]) for row in parsed}
            missing = expected - completed
            if not missing:
                break
            if attempt == 3:
                raise ValueError(f"LLM pair left {len(missing)} of {len(expected)} pairs unanswered after three retries")
            pending = [by_pair[pair] for pair in sorted(missing)]
    return result


def run_llm_pair(data: dict[str, Any], key: str, model: str, repeat: str) -> None:
    pairs = []
    for source in output_sources(data):
        for candidate in source["candidates"]:
            pairs.append({
                "source_id": source["source_id"], "candidate_id": candidate["article_id"],
                "slide_text": source["text"], "article": candidate["article"],
                "article_text": data["articles"][candidate["article"]]["text"],
            })
    openai_pairs(data, key, model, repeat, "llm_pair", pairs)


def run_llm_list(data: dict[str, Any], key: str, model: str, repeat: str) -> None:
    for batch_no, batch in enumerate(batches(output_sources(data))):
        source_keys = {f"s{index:02d}": source["source_id"] for index, source in enumerate(batch)}
        candidate_keys = {
            slide_key: {f"c{index:02d}": candidate["article_id"]
                        for index, candidate in enumerate(source["candidates"])}
            for slide_key, source in zip(source_keys, batch, strict=True)
        }
        def make_slides(slide_keys: list[str]) -> list[dict[str, Any]]:
            slides = []
            for slide_key in slide_keys:
                sid = source_keys[slide_key]
                source = next(item for item in batch if item["source_id"] == sid)
                candidate_map = {candidate["article_id"]: candidate for candidate in source["candidates"]}
                slides.append({
                    "slide_key": slide_key, "slide_text": source["text"],
                    "candidates": [{"candidate_key": candidate_key,
                                    "article": candidate_map[cid]["article"],
                                    "article_text": data["articles"][candidate_map[cid]["article"]]["text"]}
                                   for candidate_key, cid in candidate_keys[slide_key].items()],
                })
            return slides
        system = (
            f"{PAIR_INSTRUCTION} For each slide_key, select zero or more candidate_keys and give p_yes in [0,1] for every candidate_key. "
            "Return JSON with an items array; each item must include slide_key, selected_candidate_keys, and a p_yes mapping "
            "that contains every candidate_key exactly once."
        )
        user_base = {"relation_question": RELATION_QUESTION, "decision_rule": RELATION_RULE}
        all_source_candidates = {source["source_id"]: [c["article_id"] for c in source["candidates"]] for source in batch}
        all_scores = {}
        batch_key = hash_key([source["source_id"] for source in batch])
        initial_cache = CACHE_DIR / "llm_list" / repeat / f"batch_{batch_no:03d}_{batch_key}.json"
        payload = openai_request(model, system, {**user_base, "slides": make_slides(list(source_keys))})
        record = api_request("openai", "llm_list", repeat, initial_cache, payload, key, model)
        if "parsed_scores" not in record:
            record["parsed_scores"] = parse_llm_list(response_json(record), all_source_candidates, source_keys, candidate_keys)
            write_json(initial_cache, record)
        for row in record["parsed_scores"]:
            all_scores[(row["source_id"], row["candidate_id"])] = row

        for attempt in range(1, 4):
            missing_by_source = {
                sid: [cid for cid in cids if (sid, cid) not in all_scores]
                for sid, cids in all_source_candidates.items()
            }
            pending_keys = [slide_key for slide_key, sid in source_keys.items() if missing_by_source[sid]]
            if not pending_keys:
                break
            retry_payload = openai_request(model, system, {**user_base, "slides": make_slides(pending_keys)})
            retry_key = hash_key([(source_keys[slide_key], missing_by_source[source_keys[slide_key]])
                                 for slide_key in pending_keys])
            retry_cache = CACHE_DIR / "llm_list" / repeat / f"batch_{batch_no:03d}_retry{attempt}_{retry_key}.json"
            retry_record = api_request("openai", "llm_list", repeat, retry_cache, retry_payload, key, model)
            retry_sources = {slide_key: source_keys[slide_key] for slide_key in pending_keys}
            retry_candidates = {slide_key: candidate_keys[slide_key] for slide_key in pending_keys}
            retry_map = {source_keys[slide_key]: all_source_candidates[source_keys[slide_key]] for slide_key in pending_keys}
            if "parsed_scores" not in retry_record:
                retry_record["parsed_scores"] = parse_llm_list(response_json(retry_record), retry_map, retry_sources, retry_candidates)
                write_json(retry_cache, retry_record)
            for row in retry_record["parsed_scores"]:
                all_scores[(row["source_id"], row["candidate_id"])] = row
        if len(all_scores) != sum(len(cids) for cids in all_source_candidates.values()):
            raise ValueError(f"LLM list left {sum(len(cids) for cids in all_source_candidates.values()) - len(all_scores)} candidate probabilities unanswered")


def load_judge_scores(judge_name: str, repeat: str) -> dict[tuple[str, str], dict[str, Any]]:
    final_path = CACHE_DIR / judge_name / repeat / "final_scores.json"
    if judge_name == "cascade" and final_path.is_file():
        rows = read_json(final_path)
        return {(row["source_id"], row["candidate_id"]): row for row in rows}
    latest = {}
    folder = CACHE_DIR / judge_name / repeat
    if folder.exists():
        for path in sorted(folder.glob("batch_*.json")):
            record = read_json(path)
            stamp = record.get("created_at_utc", "")
            for row in record.get("parsed_scores", []):
                pair = (row["source_id"], row["candidate_id"])
                if pair not in latest or stamp >= latest[pair][0]:
                    latest[pair] = (stamp, row)
    return {pair: row for pair, (_, row) in latest.items()}


def run_cascade(data: dict[str, Any], key: str, model: str, repeat: str) -> None:
    jev = load_judge_scores("jev_pair", repeat)
    sources = output_sources(data)
    uncertain = []
    for source in sources:
        for candidate in source["candidates"]:
            pair = (source["source_id"], candidate["article_id"])
            row = jev.get(pair)
            if row is None:
                raise ValueError(f"Cascade requires Jev pair cache for {pair}")
            if UNCERTAINTY_BAND[0] <= float(row["probability"]) <= UNCERTAINTY_BAND[1]:
                uncertain.append({
                    "source_id": pair[0], "candidate_id": pair[1], "slide_text": source["text"],
                    "article": candidate["article"], "article_text": data["articles"][candidate["article"]]["text"],
                })
    replacements = {}
    for batch_no, start in enumerate(range(0, len(uncertain), 80)):
        pairs = uncertain[start:start + 80]
        if not pairs:
            continue
        rows = openai_pairs(data, key, model, repeat, "cascade", pairs)
        replacements.update({(row["source_id"], row["candidate_id"]): row for row in rows})
    final = []
    for source in sources:
        for candidate in source["candidates"]:
            pair = (source["source_id"], candidate["article_id"])
            p_jev = float(jev[pair]["probability"])
            replacement = replacements.get(pair)
            final.append({
                "source_id": pair[0], "candidate_id": pair[1],
                "probability": float(replacement["probability"]) if replacement else p_jev,
                "jev_probability": p_jev, "used_llm": replacement is not None,
            })
    write_json(CACHE_DIR / "cascade" / repeat / "final_scores.json", final)


def judge(args: argparse.Namespace) -> None:
    data = load_data()
    openai_key, jev_key, model = load_env(args)
    requested = args.judges
    if any(name in requested for name in ("jev_pair", "jev_choice", "cascade")) and not jev_key:
        raise RuntimeError("JEV_API_KEY is required for the requested judges")
    if any(name in requested for name in ("llm_pair", "llm_list", "cascade")) and not openai_key:
        raise RuntimeError("OPENAI_API_KEY is required for the requested judges")
    functions = {
        "jev_pair": lambda repeat: run_jev_pair(data, jev_key, repeat),
        "jev_choice": lambda repeat: run_jev_choice(data, jev_key, repeat),
        "llm_pair": lambda repeat: run_llm_pair(data, openai_key, model, repeat),
        "llm_list": lambda repeat: run_llm_list(data, openai_key, model, repeat),
        "cascade": lambda repeat: run_cascade(data, openai_key, model, repeat),
    }
    started = time.perf_counter()
    per_judge = {}
    for repeat in args.repeats:
        for name in ("jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade"):
            if name in requested:
                before = time.perf_counter()
                functions[name](repeat)
                per_judge[f"{name}_{repeat}"] = time.perf_counter() - before
                print(f"completed {name} {repeat}")
    write_json(RUNS_DIR / "judge_timing.json", {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "wall_seconds": time.perf_counter() - started, "per_judge_wall_seconds": per_judge,
        "model": model, "repeats": args.repeats, "requested_judges": requested,
    })
    print(f"Recorded Jev USD {total_spend('jev'):.6f} / 5.00, OpenAI USD {total_spend('openai'):.6f} / 15.00")


def candidate_recall(data: dict[str, Any]) -> dict[str, Any]:
    by_source = {source["source_id"]: source for source in data["sources"]}
    links = {link["link_id"]: link for link in data["gold_links"]}
    result = {}
    for k in (10, 20):
        candidates = {sid: {candidate["article_id"] for candidate in source["candidates_20"][:k]}
                      for sid, source in by_source.items()}
        hits = sum(
            any(edge["article_id"] in candidates[source_id(link["source_version_id"], page)]
                for page in link["source_pages"])
            for edge in data["gold_edges"]
            for link in [links[edge["link_id"]]]
        )
        complete_records = sum(
            all(any(article_id(data["target_version_id"], article) in candidates.get(
                source_id(link["source_version_id"], page), set()) for page in link["source_pages"])
                for article in link["target_articles"])
            for link in data["gold_links"]
        )
        result[str(k)] = {
            "source_selection_article_edges_recalled": hits,
            "source_selection_article_edges_total": len(data["gold_edges"]),
            "edge_recall": hits / max(1, len(data["gold_edges"])),
            "approved_link_records_recalled_all_targets": complete_records,
            "approved_link_records_total": len(data["gold_links"]),
            "record_recall_all_targets": complete_records / max(1, len(data["gold_links"])),
        }
    return result


def pair_predictions(data: dict[str, Any], judge_name: str, repeat: str | None = None) -> dict[tuple[str, str], float]:
    if judge_name == "score_only":
        slide_scores = {(s["source_id"], c["article_id"]): float(c["score"])
                        for s in data["sources"] for c in s["candidates_20"][:K]}
    else:
        slide_scores = {(pair[0], pair[1]): float(row["probability"])
                        for pair, row in load_judge_scores(judge_name, repeat or "r1").items()}
    grouped = {}
    for group in data["metric_groups"]:
        for candidate in group["candidates"]:
            pair = (group["source_id"], candidate["article_id"])
            values = [slide_scores[(sid, candidate["article_id"])] for sid in group["source_ids"]
                      if (sid, candidate["article_id"]) in slide_scores]
            if values:
                grouped[pair] = max(values)
    return grouped


def pair_set(data: dict[str, Any]) -> tuple[list[tuple[str, str]], set[tuple[str, str]]]:
    pairs = [(group["source_id"], c["article_id"])
             for group in data["metric_groups"] for c in group["candidates"]]
    gold = {(edge["source_id"], edge["article_id"]) for edge in data["gold_edges"]}
    return pairs, gold


def metric_at(scores: dict[tuple[str, str], float], pairs: list[tuple[str, str]], gold: set[tuple[str, str]], threshold: float) -> dict[str, float]:
    selected = [pair for pair in pairs if scores.get(pair, 0.0) >= threshold]
    tp = len(set(selected) & gold)
    fp, fn = len(selected) - tp, len(gold) - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "predicted": len(selected)}


def pr_auc(scores: dict[tuple[str, str], float], pairs: list[tuple[str, str]], gold: set[tuple[str, str]]) -> float:
    grouped: dict[float, list[tuple[str, str]]] = defaultdict(list)
    for pair in pairs:
        grouped[scores.get(pair, 0.0)].append(pair)
    tp = fp = 0
    prior_recall = area = 0.0
    for value in sorted(grouped, reverse=True):
        for pair in grouped[value]:
            if pair in gold:
                tp += 1
            else:
                fp += 1
        recall = tp / max(1, len(gold))
        precision = tp / (tp + fp) if tp + fp else 0.0
        area += (recall - prior_recall) * precision
        prior_recall = recall
    return area


def calibration(scores: dict[tuple[str, str], float], pairs: list[tuple[str, str]], gold: set[tuple[str, str]]) -> tuple[float, list[dict[str, Any]]]:
    examples = [(min(1.0, max(0.0, scores.get(pair, 0.0))), int(pair in gold)) for pair in pairs]
    examples.extend((0.0, 1) for pair in gold - set(pairs))
    bins, ece = [], 0.0
    for index in range(10):
        low, high = index / 10, (index + 1) / 10
        rows = [(p, y) for p, y in examples if low <= p < high or (index == 9 and p == 1.0)]
        mean_p = statistics.mean(p for p, _ in rows) if rows else None
        accuracy = statistics.mean(y for _, y in rows) if rows else None
        if rows:
            ece += len(rows) / len(examples) * abs(mean_p - accuracy)
        bins.append({"bin": index, "lower": low, "upper": high, "count": len(rows),
                     "mean_probability": mean_p, "empirical_accuracy": accuracy})
    return ece, bins


def score_metrics(scores: dict[tuple[str, str], float], pairs: list[tuple[str, str]], gold: set[tuple[str, str]], probabilistic: bool) -> dict[str, Any]:
    at05 = metric_at(scores, pairs, gold, 0.5)
    best = {**at05, "threshold": 0.5}
    for threshold in sorted({scores.get(pair, 0.0) for pair in pairs}):
        current = metric_at(scores, pairs, gold, threshold)
        if current["f1"] > best["f1"] + 1e-12 or (
            abs(current["f1"] - best["f1"]) <= 1e-12 and threshold > best["threshold"]
        ):
            best = {**current, "threshold": threshold}
    ece, bins = calibration(scores, pairs, gold) if probabilistic else (None, [])
    return {
        "precision_05": at05["precision"], "recall_05": at05["recall"], "f1_05": at05["f1"],
        "tp_05": at05["tp"], "fp_05": at05["fp"], "fn_05": at05["fn"], "predicted_05": at05["predicted"],
        "best_f1": best["f1"], "best_threshold": best["threshold"],
        "best_precision": best["precision"], "best_recall": best["recall"],
        "pr_auc": pr_auc(scores, pairs, gold), "ece": ece, "reliability_bins": bins,
    }


def mean_sd(values: list[float | None]) -> tuple[float | None, float | None]:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None, None
    return statistics.mean(present), statistics.stdev(present) if len(present) > 1 else None


def fmt(avg: float | None, sd: float | None, digits: int = 3) -> str:
    if avg is None:
        return "n/a"
    return f"{avg:.{digits}f}" if sd is None else f"{avg:.{digits}f} +/- {sd:.{digits}f}"


def call_summary(judge_names: set[str], setting: str = "baseline") -> dict[str, Any]:
    records = [row for row in cached_call_records() if row.get("judge") in judge_names
               and row.get("candidate_setting", "baseline") == setting]
    latencies = sorted(float(row.get("latency_seconds", 0)) for row in records)
    percentile = lambda q: latencies[min(len(latencies) - 1, max(0, math.ceil(q * len(latencies)) - 1))] if latencies else None
    wall = sum(latencies)
    return {
        "calls": len(records),
        "input_tokens": sum(row.get("usage", {}).get("input_tokens", 0) for row in records),
        "cached_input_tokens": sum(row.get("usage", {}).get("cached_input_tokens", 0) for row in records),
        "output_tokens": sum(row.get("usage", {}).get("output_tokens", 0) for row in records),
        "cost_usd": sum(float(row.get("cost_usd", 0)) for row in records),
        "p50_seconds": percentile(0.5), "p95_seconds": percentile(0.95),
        "total_call_seconds": sum(latencies), "wall_seconds": wall,
    }


def collect_downstream() -> dict[str, Any] | None:
    eval_path = DATA_DIR / "eval_set_v3.json"
    eval_set = read_json(eval_path) if eval_path.exists() else {}
    graph_names = {case["name"] for case in eval_set.get("cases", []) if case.get("category") == "graph"}
    output = {}
    for variant in ("gold", "none", "jev_pair", "llm_pair", "cascade"):
        path = RUNS_DIR / "downstream" / variant / "ragas_results.json"
        if not path.is_file():
            continue
        result = read_json(path)
        rows = result.get("document_cases", [])
        groups = {"all": rows, "graph": [row for row in rows if row.get("case") in graph_names]}
        summary = {}
        for group_name, group_rows in groups.items():
            metrics = {}
            for metric in ("recall", "mrr", "ndcg_at_10", "linked_gold_recall"):
                values = [float(row[metric]) for row in group_rows if isinstance(row.get(metric), (int, float))]
                metrics[metric] = statistics.mean(values) if values else None
                metrics[metric + "_n"] = len(values)
            summary[group_name] = metrics
        output[variant] = {
            "cases": len(rows), "graph_cases": len(groups["graph"]), "metrics": summary,
            "output": str(path.relative_to(PAPER_ROOT)),
        }
    return output or None



def usage_cost_summary(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    latencies = sorted(float(row.get("latency_seconds", 0)) for row in rows)
    percentile = lambda q: latencies[min(len(latencies) - 1, max(0, math.ceil(q * len(latencies)) - 1))] if latencies else None
    input_tokens = output_tokens = cached_tokens = 0
    cost = 0.0
    for row in rows:
        usage = row.get("usage") or {}
        prompt = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        completion = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
        details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
        cached = min(prompt, int(details.get("cached_tokens", details.get("cached_input_tokens", 0)) or 0))
        embedding_price = {"text-embedding-3-small": OPENAI_EMBEDDING_PRICE,
                           "text-embedding-3-large": 0.13}.get(row.get("model")) if row.get("endpoint") == "embeddings" else None
        input_price = OPENAI_PRICE["input"] if embedding_price is None else embedding_price
        input_tokens += prompt
        output_tokens += completion
        cached_tokens += cached
        cost += ((prompt - cached) * input_price + cached * OPENAI_PRICE["cached_input"]
                 + completion * OPENAI_PRICE["output"]) / 1_000_000
    return {
        "calls": len(rows), "input_tokens": input_tokens, "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens, "cost_usd": cost,
        "p50_seconds": percentile(0.5), "p95_seconds": percentile(0.95),
        "total_call_seconds": sum(latencies),
    }


def collect_downstream_costs() -> dict[str, dict[str, Any]]:
    result = {}
    for variant in ("gold", "none", "jev_pair", "llm_pair", "cascade"):
        summary = usage_cost_summary(RUNS_DIR / "downstream" / variant / "openai_usage.jsonl")
        if summary:
            result[variant] = summary
    return result


def collect_full_ragas() -> dict[str, dict[str, Any]]:
    result = {}
    for variant in ("gold", "jev_choice", "llm_pair"):
        path = RUNS_DIR / "full_ragas" / variant / "ragas_results.json"
        if not path.is_file():
            continue
        payload = read_json(path)
        result[variant] = {
            "cases": payload.get("document_case_count", 0),
            "ragas": payload.get("averages", {}).get("document", {}),
            "retrieval": payload.get("retrieval_averages", {}).get("graph", {}),
            "output": str(path.relative_to(PAPER_ROOT)),
        }
    return result


def collect_full_ragas_costs() -> dict[str, dict[str, Any]]:
    result = {}
    for variant in ("gold", "jev_choice", "llm_pair"):
        summary = usage_cost_summary(RUNS_DIR / "full_ragas" / variant / "openai_usage.jsonl")
        if summary:
            result[variant] = summary
    return result


def error_category(data: dict[str, Any], source: dict[str, Any], candidate: dict[str, Any], score: float) -> str:
    source_tokens = _search_tokens(source.get("text", ""))
    if len(source_tokens) < 8:
        return "generic"
    candidate_tokens = _search_tokens(data["articles"][candidate["article"]]["text"])
    approved_numbers = source["gold_articles"] or sorted({str(edge["article"]) for edge in data["gold_edges"]}, key=int)
    for number in approved_numbers:
        approved_tokens = _search_tokens(data["articles"][number]["text"])
        overlap = len(candidate_tokens & approved_tokens) / max(1, len(candidate_tokens | approved_tokens))
        if overlap >= 0.08:
            return "related-but-unapproved"
    return "wrong article"


def write_false_positives(data: dict[str, Any], score_sets: dict[str, dict[tuple[str, str], float]], gold: set[tuple[str, str]]) -> None:
    source_map = {group["source_id"]: group for group in data["metric_groups"]}
    candidate_map = {
        (group["source_id"], candidate["article_id"]): candidate
        for group in data["metric_groups"] for candidate in group["candidates"]
    }
    rows = []
    for judge_name, scores in score_sets.items():
        false_positives = [
            (pair, score) for pair, score in scores.items()
            if pair in candidate_map and score >= 0.5 and pair not in gold
        ]
        for (sid, cid), score in sorted(false_positives, key=lambda row: (-row[1], row[0]))[:20]:
            source, candidate = source_map[sid], candidate_map[(sid, cid)]
            article = data["articles"][candidate["article"]]
            rows.append({
                "judge": judge_name, "source_id": sid, "source_filename": source["source_filename"],
                "slides": ",".join(str(page) for page in source["source_pages"]),
                "slide_title": re.sub(r"\s+", " ", source["title"]).strip(), "article": candidate["article"],
                "score": round(score, 6), "hybrid_score": candidate["score"],
                "category": error_category(data, source, candidate, score),
                "category_basis": "rule-based: source specificity and lexical overlap with approved target articles",
                "source_excerpt": re.sub(r"\s+", " ", source["text"][:500]).strip(),
                "article_excerpt": re.sub(r"\s+", " ", article["text"][:700]).strip(),
            })
    path = SUMMARY_DIR / "false_positives.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else [
        "judge", "source_id", "source_filename", "slides", "slide_title", "article", "score",
        "hybrid_score", "category", "category_basis", "source_excerpt", "article_excerpt",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def render_table(data: dict[str, Any], edge_rows: list[dict[str, Any]], costs: dict[str, dict[str, Any]],
                 downstream: dict[str, Any] | None, downstream_costs: dict[str, dict[str, Any]],
                 full_ragas: dict[str, dict[str, Any]], full_ragas_costs: dict[str, dict[str, Any]],
                 recall: dict[str, Any]) -> str:
    lines = [
        "# Main results", "",
        f"Gold: {data['gold_link_record_count']} approved DB records, {data['gold_article_range_count']} target article ranges, "
        f"and {data['gold_edge_count']} unique source-selection/article edges across {data['positive_slide_count']} positive slides. "
        f"The negative set has {data['negative_slide_count']} draws from {data['negative_unique_slide_count']} unique unlinked slides.",
        "", "## Candidate recall", "",
        "A target edge is covered when any slide in its approved source selection retrieves that article.",
        "", "| K | Gold edges recalled | Edge recall | Link records with every target covered | Record recall |",
        "|---:|---:|---:|---:|---:|",
    ]
    for k in ("10", "20"):
        row = recall[k]
        lines.append(
            f"| {k} | {row['source_selection_article_edges_recalled']}/{row['source_selection_article_edges_total']} | "
            f"{row['edge_recall']:.3f} | {row['approved_link_records_recalled_all_targets']}/{row['approved_link_records_total']} | "
            f"{row['record_recall_all_targets']:.3f} |"
        )
    lines += [
        "", "## Edge metrics", "",
        "Metrics are over 96 approved source-selection/article targets, with each group score equal to the maximum probability "
        "among its selected slides. Threshold 0.5 uses judge probability (raw hybrid score for score_only). Best F1 and its threshold "
        "are tuned post hoc on this same labeled set; they are optimistic descriptive upper bounds, not held-out estimates.",
        "", "| Judge | P@0.5 | R@0.5 | F1@0.5 | Best F1 (threshold) | PR-AUC | ECE | Determinism |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in edge_rows:
        lines.append(f"| {row['judge']} | {row['p05']} | {row['r05']} | {row['f05']} | {row['best']} | "
                     f"{row['pr_auc']} | {row['ece']} | {row['determinism']} |")
    lines += [
        "", "Each probabilistic metric is mean +/- sample standard deviation over three repeats; score_only is fixed. PR-AUC is stepwise "
        "average precision. ECE uses ten equal-width bins and includes any missed gold edges at probability zero; raw hybrid scores have no ECE. "
        "Per-repeat reliability counts are in reliability_bins.csv.",
        "", "## Judge cost and latency", "",
        "Costs use reported API usage and the prices in notes.md. p50/p95 are per call; total wall time sums sequential API-call latencies and excludes local cache/parsing overhead.",
        "", "| Judge | Calls | Input tokens | Output tokens | Cost USD | p50 s/call | p95 s/call | Total wall seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("score_only", "jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade", "cascade_pipeline"):
        if name not in costs:
            continue
        row = costs[name]
        p50 = "n/a" if row["p50_seconds"] is None else f"{row['p50_seconds']:.2f}"
        p95 = "n/a" if row["p95_seconds"] is None else f"{row['p95_seconds']:.2f}"
        label = "cascade pipeline (Jev + LLM)" if name == "cascade_pipeline" else name
        lines.append(f"| {label} | {row['calls']} | {row['input_tokens']} | {row['output_tokens']} | "
                     f"{row['cost_usd']:.6f} | {p50} | {p95} | {row['wall_seconds']:.2f} |")
    lines += [
        "", "## Downstream retrieval (proposed, skip RAGAS)", "",
        "Means over all 37 cases; linked-gold recall averages cases where via_link gold is defined. Graph-only means are in downstream_summary.json.",
        "", "| Link set | Cases | Recall | MRR | nDCG@10 | Linked-gold recall |", "|---|---:|---:|---:|---:|---:|",
    ]
    for variant in ("gold", "none", "jev_pair", "llm_pair", "cascade"):
        row = (downstream or {}).get(variant)
        if not row:
            lines.append(f"| {variant} | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |")
            continue
        metrics = row["metrics"]["all"]
        show = lambda name: "n/a" if metrics[name] is None else f"{metrics[name]:.3f}"
        lines.append(f"| {variant} | {row['cases']} | {show('recall')} | {show('mrr')} | "
                     f"{show('ndcg_at_10')} | {show('linked_gold_recall')} |")
    if downstream_costs:
        lines += ["", "Downstream reranker cost and latency:", "",
                  "| Link set | Calls | Input tokens | Output tokens | Cost USD | p50 s/call | p95 s/call | Call seconds |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for variant, row in downstream_costs.items():
            p50 = "n/a" if row["p50_seconds"] is None else f"{row['p50_seconds']:.2f}"
            p95 = "n/a" if row["p95_seconds"] is None else f"{row['p95_seconds']:.2f}"
            lines.append(f"| {variant} | {row['calls']} | {row['input_tokens']} | {row['output_tokens']} | "
                         f"{row['cost_usd']:.6f} | {p50} | {p95} | {row['total_call_seconds']:.2f} |")
    lines += ["", "## Full RAGAS on graph cases (one repeat)", ""]
    if full_ragas:
        lines += ["Runs use the best-F1 Jev judge (`jev_choice`) and LLM judge (`llm_pair`) selected on the same edge set.",
                  "", "| Link set | Cases | Faithfulness | Answer relevancy | Answer correctness | Context precision | Context recall | Retrieval recall | Retrieval MRR | Retrieval nDCG@10 | Linked-gold recall |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for variant in ("gold", "jev_choice", "llm_pair"):
            row = full_ragas.get(variant)
            if not row:
                lines.append(f"| {variant} | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |")
                continue
            ragas, retrieval = row["ragas"], row["retrieval"]
            show = lambda values, key: "n/a" if values.get(key) is None else f"{values[key]:.3f}"
            lines.append(f"| {variant} | {row['cases']} | {show(ragas, 'faithfulness')} | {show(ragas, 'answer_relevancy')} | "
                         f"{show(ragas, 'answer_correctness')} | {show(ragas, 'context_precision')} | {show(ragas, 'context_recall')} | "
                         f"{show(retrieval, 'recall')} | {show(retrieval, 'mrr')} | {show(retrieval, 'ndcg_at_10')} | "
                         f"{show(retrieval, 'linked_gold_recall')} |")
        if full_ragas_costs:
            lines += ["", "Full RAGAS API cost and latency:", "",
                      "| Link set | Calls | Input tokens | Output tokens | Cost USD | p50 s/call | p95 s/call | Call seconds |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|"]
            for variant, row in full_ragas_costs.items():
                p50 = "n/a" if row["p50_seconds"] is None else f"{row['p50_seconds']:.2f}"
                p95 = "n/a" if row["p95_seconds"] is None else f"{row['p95_seconds']:.2f}"
                lines.append(f"| {variant} | {row['calls']} | {row['input_tokens']} | {row['output_tokens']} | "
                             f"{row['cost_usd']:.6f} | {p50} | {p95} | {row['total_call_seconds']:.2f} |")
    else:
        lines.append("NOT RUN")
    lines += ["", "See notes.md, edge_metrics.json, threshold_curve.csv, reliability_bins.csv, false_positives.csv, "
              "and cache/ for full details.", ""]
    return "\n".join(lines)


def aggregate(args: argparse.Namespace) -> None:
    data = load_data()
    pairs, gold = pair_set(data)
    judge_names = ("score_only", "jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade")
    edge_rows, reliability_rows, score_sets = [], [], {}
    for name in judge_names:
        repeats = (None,) if name == "score_only" else REPEATS
        metrics_by_repeat, score_by_repeat = [], []
        for repeat in repeats:
            scores = pair_predictions(data, name, repeat)
            if len(scores) < len(pairs):
                raise ValueError(f"{name} {repeat or 'fixed'} cache is incomplete: {len(scores)}/{len(pairs)} pairs; run judge")
            metrics = score_metrics(scores, pairs, gold, name != "score_only")
            metrics_by_repeat.append(metrics)
            score_by_repeat.append(scores)
            for bucket in metrics["reliability_bins"]:
                reliability_rows.append({"judge": name, "repeat": repeat or "fixed", **bucket})
        averages = {
            metric: mean_sd([row[metric] for row in metrics_by_repeat])
            for metric in ("precision_05", "recall_05", "f1_05", "best_f1", "best_threshold", "pr_auc", "ece")
        }
        deterministic = []
        for pair in pairs:
            decisions = [scores.get(pair, 0.0) >= 0.5 for scores in score_by_repeat]
            deterministic.append(all(value == decisions[0] for value in decisions))
        stability = 1.0 if name == "score_only" else sum(deterministic) / len(deterministic)
        edge_rows.append({
            "judge": name,
            "p05": fmt(*averages["precision_05"]), "r05": fmt(*averages["recall_05"]),
            "f05": fmt(*averages["f1_05"]),
            "best": f"{fmt(*averages['best_f1'])} ({fmt(*averages['best_threshold'])})",
            "pr_auc": fmt(*averages["pr_auc"]), "ece": fmt(*averages["ece"]),
            "determinism": f"{stability:.3f}",
            "per_repeat": [{key: value for key, value in row.items() if key != "reliability_bins"} for row in metrics_by_repeat],
        })
        score_sets[name] = {
            pair: statistics.mean(scores.get(pair, 0.0) for scores in score_by_repeat)
            for pair in pairs
        }

    recall = candidate_recall(data)
    write_json(SUMMARY_DIR / "candidate_recall.json", recall)
    write_json(SUMMARY_DIR / "edge_metrics.json", {"gold_edges": len(gold), "candidate_pairs": len(pairs), "rows": edge_rows})
    with (SUMMARY_DIR / "reliability_bins.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["judge", "repeat", "bin", "lower", "upper", "count", "mean_probability", "empirical_accuracy"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(reliability_rows)

    # This is the full in-sample hybrid-score threshold curve, not only its maximizing point.
    thresholds = sorted({0.5, *(score_sets["score_only"].values())})
    with (SUMMARY_DIR / "threshold_curve.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["threshold", "precision", "recall", "f1", "tp", "fp", "fn", "predicted"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for threshold in thresholds:
            writer.writerow({"threshold": threshold, **metric_at(score_sets["score_only"], pairs, gold, threshold)})
    write_false_positives(data, score_sets, gold)

    costs = {name: call_summary({name}) for name in ("jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade")}
    costs["cascade_pipeline"] = call_summary({"jev_pair", "cascade"})
    costs["score_only"] = {
        "calls": 0, "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
        "cost_usd": 0.0, "p50_seconds": None, "p95_seconds": None, "total_call_seconds": 0.0, "wall_seconds": 0.0,
    }
    downstream = collect_downstream()
    downstream_costs = collect_downstream_costs()
    full_ragas = collect_full_ragas()
    full_ragas_costs = collect_full_ragas_costs()
    if downstream:
        write_json(SUMMARY_DIR / "downstream_summary.json", downstream)
    write_json(SUMMARY_DIR / "cost_latency.json", costs)
    write_json(SUMMARY_DIR / "downstream_cost_latency.json", downstream_costs)
    write_json(SUMMARY_DIR / "full_ragas_summary.json", full_ragas)
    write_json(SUMMARY_DIR / "full_ragas_cost_latency.json", full_ragas_costs)
    (SUMMARY_DIR / "main_table.md").write_text(
        render_table(data, edge_rows, costs, downstream, downstream_costs, full_ragas, full_ragas_costs, recall), encoding="utf-8")
    with (SUMMARY_DIR / "main_table.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["judge", "precision_at_0.5", "recall_at_0.5", "f1_at_0.5", "best_f1", "best_threshold", "pr_auc", "ece", "determinism"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in edge_rows:
            best_f1, threshold = row["best"].split(" (", 1)
            writer.writerow({
                "judge": row["judge"], "precision_at_0.5": row["p05"], "recall_at_0.5": row["r05"],
                "f1_at_0.5": row["f05"], "best_f1": best_f1, "best_threshold": threshold.rstrip(")"),
                "pr_auc": row["pr_auc"], "ece": row["ece"], "determinism": row["determinism"],
            })
    openai_key, jev_key, model = load_env(args)
    notes = [
        "# Experiment notes", "",
        "## Dataset and units", "",
        f"The source DB contains {data['gold_link_record_count']} approved REFERENCES selections, {data['gold_article_range_count']} target article ranges, "
        f"and {data['positive_slide_count']} positive guide slide pages. We draw {data['negative_slide_count']} unlinked-slide samples "
        f"from {data['negative_unique_slide_count']} unique unlinked slides using seed {SEED}; sampling uses replacement when the negative pool is smaller. "
        f"There are {data['gold_edge_count']} unique source-selection/article target edges. Metrics score each approved selection/article pair "
        "by the maximum probability across slides in that selection; slide-level API judgments remain the same for every judge.",
        "",
        "Gold is incomplete: only human-approved links are positive labels. An edge absent from the approved set may still be valid, "
        "so precision and false positives measure agreement with current approvals, not objective relevance.",
        "", "## Candidate generation", "",
        "Stored slide and article embeddings are reused with production weights (0.6 cosine and 0.4 BM25); no embedding API is called. "
        f"Judges receive the identical top-{K} candidate list per slide; candidate recall is also measured at K={K_RECALL} and is their upper bound. "
        f"The corpus contains {len(data['articles'])} reconstructed regulation article units.",
        "", "## Metrics and tuning", "",
        "Threshold-0.5 metrics use probabilities; score_only uses the raw hybrid score. Best-F1 thresholds are tuned post hoc on this same "
        "labeled candidate set and are optimistic in-sample values, not held-out estimates. PR-AUC is stepwise average precision. ECE uses "
        "ten equal-width bins; missed gold edges receive probability zero. ECE is not applicable to raw hybrid ranking scores. Determinism "
        "is the fraction of candidate edges with identical >=0.5 decisions across three repeats; the score baseline is fixed by construction.",
        "",
        f"Jev choice emits one article or none per slide and uses per-option probabilities. LLM list returns zero or more ids with p(yes). "
        f"Cascade sends Jev probabilities in the inclusive {UNCERTAINTY_BAND[0]:.1f}-{UNCERTAINTY_BAND[1]:.1f} band to the same LLM pair prompt.",
        "", "## Cost and runtime", "",
        f"OpenAI price: input USD {OPENAI_PRICE['input']:.2f}/M, cached input USD {OPENAI_PRICE['cached_input']:.2f}/M, "
        f"output USD {OPENAI_PRICE['output']:.2f}/M for {model}; source: {OPENAI_PRICE_URL}. Jev price: input USD "
        f"{JEV_INPUT_PRICE:.3f}/M, output free; source: {JEV_PRICE_URL}. Downstream text-embedding-3-small input is USD "
        f"{OPENAI_EMBEDDING_PRICE:.2f}/M; source: {OPENAI_EMBEDDING_PRICE_URL}. Full RAGAS uses text-embedding-3-large at USD 0.13/M input; "
        "source: https://developers.openai.com/api/docs/models/text-embedding-3-large. Costs use API usage fields and cached-input counts when returned. "
        "The runner guards cumulative OpenAI spend at USD 15 and Jev at USD 5.",
        "",
        f"Recorded judge spend: OpenAI USD {total_spend('openai'):.6f}; Jev USD {total_spend('jev'):.6f}. The optional gpt-4o-mini point was not run. "
        + ("Full RAGAS was run once on 20 graph cases for gold, best Jev (`jev_choice`), and best LLM (`llm_pair`). "
           if full_ragas else "Full RAGAS was not run.")
        + "Retrieval-only results cover all 37 evaluation cases.",
        "", "## Error analysis", "",
        "false_positives.csv lists up to 20 false-positive source-selection/article edges per judge at threshold 0.5. Categories use a "
        "reproducible heuristic: generic for low-specificity slide text; related-but-unapproved for lexical overlap with another approved "
        "target article; wrong article otherwise. These are audit labels, not human adjudications.",
        "", "## Reproduction", "",
        "See ../README.md. API responses, usage, and request latency are cached under cache/; aggregate performs no API calls.", "",
    ]
    (SUMMARY_DIR / "notes.md").write_text("\n".join(notes), encoding="utf-8")
    print(SUMMARY_DIR / "main_table.md")


def build_databases(args: argparse.Namespace) -> None:
    data, source_db = load_data(), args.db.resolve()
    if not source_db.is_file():
        raise FileNotFoundError(source_db)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    variants = {"gold": None, "none": None, "jev_pair": "jev_pair", "jev_choice": "jev_choice", "llm_pair": "llm_pair", "cascade": "cascade"}
    group_map = {group["source_id"]: group for group in data["metric_groups"]}
    candidate_pairs, _ = pair_set(data)
    now = datetime.now(UTC).isoformat()
    manifest = {}
    import sqlite3
    for variant, judge_name in variants.items():
        db_path = DB_DIR / f"links_{variant}.sqlite"
        shutil.copyfile(source_db, db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        if variant == "gold":
            conn.execute("DELETE FROM document_links WHERE status != 'approved'")
        else:
            conn.execute("DELETE FROM document_links")
            if judge_name:
                repeat_maps = [pair_predictions(data, judge_name, repeat) for repeat in REPEATS]
                predicted = [pair for pair in candidate_pairs
                             if sum(scores.get(pair, 0.0) >= 0.5 for scores in repeat_maps) >= 2]
                inserted = set()
                for sid, cid in predicted:
                    source = group_map[sid]
                    candidate = next(item for item in source["candidates"] if item["article_id"] == cid)
                    article = data["articles"][candidate["article"]]
                    key = (source["source_version_id"], tuple(source["source_pages"]), cid)
                    if key in inserted:
                        continue
                    inserted.add(key)
                    source_selection = json.dumps(source["selection"], ensure_ascii=False)
                    target_selection = json.dumps({
                        "kind": "text", "version_id": article["version_id"],
                        "ranges": [{"start": article["start"], "end": article["end"], "exact": article["text"]}],
                    }, ensure_ascii=False)
                    conn.execute(
                        "INSERT INTO document_links (id,source_version_id,target_version_id,source_selection,target_selection,"
                        "relation_type,note,status,created_by,approved_by,created_at,approved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (str(uuid.uuid4()), source["source_version_id"], article["version_id"], source_selection,
                         target_selection, "REFERENCES",
                         f"paper_jev {judge_name} majority vote across three repeats; threshold 0.5; K={K}",
                         "approved", "paper_jev-experiment", "paper_jev-experiment", now, now),
                    )
        conn.commit()
        count = conn.execute("SELECT count(*) FROM document_links").fetchone()[0]
        conn.close()
        manifest[variant] = {
            "database": str(db_path.relative_to(PAPER_ROOT)), "document_links": count,
            "link_set": "original approved records" if variant == "gold" else (
                "empty" if variant == "none" else "majority vote across three repeats at p>=0.5"
            ),
        }
    write_json(RUNS_DIR / "db_manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Jev-vs-LLM link construction experiment")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--db", type=Path, required=True)
    prep.add_argument("--eval-set", type=Path, required=True)
    run = sub.add_parser("judge")
    run.add_argument("--openai-env", type=Path)
    run.add_argument("--jev-env", type=Path)
    run.add_argument("--judges", nargs="+",
                     choices=["jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade"],
                     default=["jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade"])
    run.add_argument("--repeats", nargs="+", choices=REPEATS, default=list(REPEATS))
    agg = sub.add_parser("aggregate")
    agg.add_argument("--openai-env", type=Path)
    agg.add_argument("--jev-env", type=Path)
    dbs = sub.add_parser("build-dbs")
    dbs.add_argument("--db", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    elif args.command == "judge":
        judge(args)
    elif args.command == "aggregate":
        aggregate(args)
    else:
        build_databases(args)


if __name__ == "__main__":
    main()
