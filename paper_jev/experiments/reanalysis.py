from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
CACHE = HERE / "cache"
SUMMARY = HERE / "summary"
DATA = json.loads((HERE / "data" / "experiment_data.json").read_text(encoding="utf-8"))
N_BOOT = 2000
BOOT_SEED = 20261018
CV_SEED = 20261019
FP_SEED = 20261020
REPEATS = ("r1", "r2", "r3")
K10_JUDGES = ("jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade")
K50_JUDGES = ("jev_pair", "jev_choice", "cascade")
PAIR_JUDGES = ("jev_pair", "llm_pair", "cascade")
SELECTION_JUDGES = ("jev_choice", "llm_list")
METRICS = ("precision", "recall", "f1", "pr_auc", "ece")
PRICE = {
    "openai_input": 0.20,
    "openai_cached_input": 0.02,
    "openai_output": 1.20,
    "jev_input": 0.042,
}
OPENAI_PRICE_URL = "https://developers.openai.com/api/docs/models/gpt-5.6-luna"
JEV_PRICE_URL = "https://docs.typesafe.ai/llms.txt"
NEGATIVE_SAMPLE = re.compile(r"_sample\d+$")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def article_id(article: str) -> str:
    return DATA["articles"][str(article)]["id"]


def slide_id(version_id: str, page: int) -> str:
    return f"slide_{version_id[:8]}_{int(page):03d}"


def canonical_slide(source_id: str) -> str:
    return NEGATIVE_SAMPLE.sub("", source_id)


def candidates_for(source: dict[str, Any], k: int) -> list[dict[str, Any]]:
    return source["candidates_100"][:k]


def load_scores(k: int, judge: str, repeat: str) -> dict[tuple[str, str], dict[str, Any]]:
    root = CACHE / (f"followup/hybrid_{k}" if k == 50 else "") / judge / repeat
    final = root / "final_scores.json"
    if final.is_file():
        rows = read_json(final)
        return {(row["source_id"], row["candidate_id"]): row for row in rows}

    latest: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
    if root.exists():
        for path in sorted(root.rglob("batch_*.json")):
            record = read_json(path)
            stamp = str(record.get("created_at_utc", ""))
            for row in record.get("parsed_scores", []):
                pair = (row["source_id"], row["candidate_id"])
                if pair not in latest or stamp >= latest[pair][0]:
                    latest[pair] = (stamp, row)
    return {pair: row for pair, (_, row) in latest.items()}


def expected_pairs(k: int) -> set[tuple[str, str]]:
    return {
        (source["source_id"], candidate["article_id"])
        for source in DATA["sources"] for candidate in candidates_for(source, k)
    }


def score_maps(k: int, judge: str) -> tuple[list[dict[tuple[str, str], dict[str, Any]]], list[str]]:
    expected = expected_pairs(k)
    maps, available = [], []
    for repeat in REPEATS:
        scores = load_scores(k, judge, repeat)
        if expected <= scores.keys():
            maps.append(scores)
            available.append(repeat)
    if not maps:
        raise RuntimeError(f"No complete cached repeat for K={k} {judge}; expected {len(expected)} slide-candidate scores")
    if k == 10 and len(maps) != 3:
        raise RuntimeError(f"K=10 {judge} has {len(maps)}/3 complete repeats")
    if k == 50 and judge in K50_JUDGES and len(maps) != 3:
        raise RuntimeError(f"K=50 {judge} has {len(maps)}/3 complete repeats")
    return maps, available


def relation_maps() -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    links = {link["link_id"]: link for link in DATA["gold_links"]}
    by_slide: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for link in DATA["gold_links"]:
        for page in link["source_pages"]:
            by_slide[slide_id(link["source_version_id"], page)].append(link)
    return links, by_slide


def candidate_score_map(k: int, score_rows: dict[tuple[str, str], dict[str, Any]]) -> dict[tuple[str, str], float]:
    expected = expected_pairs(k)
    missing = expected - score_rows.keys()
    if missing:
        raise RuntimeError(f"Incomplete score cache: missing {len(missing)} of {len(expected)} pairs")
    scores = {}
    for pair in expected:
        value = float(score_rows[pair]["probability"])
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"Invalid cached probability for {pair}: {value}")
        scores[pair] = value
    return scores


def build_rows(k: int, scores: dict[tuple[str, str], float], unit: str) -> list[dict[str, Any]]:
    _, by_slide = relation_maps()
    source_map = {source["source_id"]: source for source in DATA["sources"]}
    rows: list[dict[str, Any]] = []

    def add(source_id: str, cid: str, p: float, label: int, cluster: str, role: str,
            covered: bool = True, predictable: bool = True, link_id: str | None = None) -> None:
        rows.append({"source_id": source_id, "candidate_id": cid, "p": p, "label": label,
                     "cluster": cluster, "role": role, "covered": covered,
                     "predictable": predictable, "link_id": link_id})

    if unit == "link_record":
        for link in DATA["gold_links"]:
            lid = link["link_id"]
            sids = [slide_id(link["source_version_id"], page) for page in link["source_pages"]]
            candidate_ids = set()
            for sid in sids:
                candidate_ids.update(candidate["article_id"] for candidate in candidates_for(source_map[sid], k))
            target_ids = {article_id(number) for number in link["target_articles"]}
            for cid in candidate_ids:
                values = [scores[(sid, cid)] for sid in sids if (sid, cid) in scores]
                add(f"link_{lid}", cid, max(values), int(cid in target_ids), f"L:{lid}", "positive", link_id=lid)
            for cid in target_ids - candidate_ids:
                add(f"link_{lid}", cid, 0.0, 1, f"L:{lid}", "positive", False, False, lid)

        for source in DATA["sources"]:
            if source["role"] != "negative":
                continue
            sid = source["source_id"]
            cluster = "N:" + canonical_slide(sid)
            for candidate in candidates_for(source, k):
                cid = candidate["article_id"]
                add(sid, cid, scores[(sid, cid)], 0, cluster, "negative")
        return rows

    if unit != "slide_edge":
        raise ValueError(unit)

    for sid, matched_links in by_slide.items():
        source = source_map[sid]
        for link in matched_links:
            lid = link["link_id"]
            target_ids = {article_id(number) for number in link["target_articles"]}
            candidates = candidates_for(source, k)
            candidate_ids = {candidate["article_id"] for candidate in candidates}
            for candidate in candidates:
                cid = candidate["article_id"]
                add(sid, cid, scores[(sid, cid)], int(cid in target_ids), f"L:{lid}", "positive", link_id=lid)
            for cid in target_ids - candidate_ids:
                add(sid, cid, 0.0, 1, f"L:{lid}", "positive", False, False, lid)

    for source in DATA["sources"]:
        if source["role"] != "negative":
            continue
        sid = source["source_id"]
        cluster = "N:" + canonical_slide(sid)
        for candidate in candidates_for(source, k):
            cid = candidate["article_id"]
            add(sid, cid, scores[(sid, cid)], 0, cluster, "negative")
    return rows


def cluster_weights(rows: list[dict[str, Any]], seed: int) -> tuple[list[str], np.ndarray]:
    positive = sorted({row["cluster"] for row in rows if row["role"] == "positive"})
    negative = sorted({row["cluster"] for row in rows if row["role"] == "negative"})
    if len(positive) != 36 or len(negative) != 77:
        raise AssertionError(f"Expected 36 link and 77 unique negative clusters, found {len(positive)} and {len(negative)}")
    rng = np.random.default_rng(seed)
    weights = np.zeros((N_BOOT, len(positive) + len(negative)), dtype=np.int16)
    for offset, names in ((0, positive), (len(positive), negative)):
        draws = rng.integers(0, len(names), size=(N_BOOT, len(names)))
        for row_index in range(N_BOOT):
            weights[row_index, offset:offset + len(names)] = np.bincount(draws[row_index], minlength=len(names))
    return positive + negative, weights


def make_hist(rows: list[dict[str, Any]], clusters: list[str], covered_only: bool = False) -> tuple[np.ndarray, np.ndarray, list[float]]:
    selected = [row for row in rows if not covered_only or row["covered"]]
    score_levels = sorted({float(row["p"]) for row in selected})
    score_index = {p: index for index, p in enumerate(score_levels)}
    cluster_index = {name: index for index, name in enumerate(clusters)}
    hist = np.zeros((len(clusters), 2, len(score_levels)), dtype=np.int32)
    ap_hist = np.zeros_like(hist)
    for row in selected:
        index = (cluster_index[row["cluster"]], int(row["label"]), score_index[float(row["p"])])
        hist[index] += 1
        if row["predictable"]:
            ap_hist[index] += 1
    return hist, ap_hist, score_levels


def histogram_metrics(counts: np.ndarray, score_levels: list[float], ap_counts: np.ndarray) -> dict[str, np.ndarray]:
    scores = np.asarray(score_levels, dtype=float)
    positives, negatives = counts[:, 1, :], counts[:, 0, :]
    total_positive = positives.sum(axis=1)
    selected = scores >= 0.5
    tp = positives[:, selected].sum(axis=1)
    fp = negatives[:, selected].sum(axis=1)
    precision = np.divide(tp, tp + fp, out=np.zeros_like(tp, dtype=float), where=(tp + fp) > 0)
    recall = np.divide(tp, total_positive, out=np.zeros_like(tp, dtype=float), where=total_positive > 0)
    f1 = np.divide(2 * precision * recall, precision + recall,
                   out=np.zeros_like(precision), where=(precision + recall) > 0)

    descending = np.argsort(scores)[::-1]
    ap_pos, ap_neg = ap_counts[:, 1, :], ap_counts[:, 0, :]
    pos_desc, neg_desc = ap_pos[:, descending], ap_neg[:, descending]
    cum_pos, cum_neg = np.cumsum(pos_desc, axis=1), np.cumsum(neg_desc, axis=1)
    pr = np.divide(cum_pos, cum_pos + cum_neg, out=np.zeros_like(cum_pos, dtype=float), where=(cum_pos + cum_neg) > 0)
    ap = np.divide(pos_desc, total_positive[:, None], out=np.zeros_like(pos_desc, dtype=float), where=total_positive[:, None] > 0)
    pr_auc = (ap * pr).sum(axis=1)

    total = (positives + negatives).sum(axis=1)
    ece_width = np.zeros(len(counts), dtype=float)
    for bin_index in range(10):
        in_bin = (scores >= bin_index / 10) & ((scores < (bin_index + 1) / 10) | (bin_index == 9) & (scores == 1.0))
        predicted_sum = ((positives + negatives)[:, in_bin] * scores[in_bin]).sum(axis=1)
        observed_sum = positives[:, in_bin].sum(axis=1)
        ece_width += np.divide(np.abs(predicted_sum - observed_sum), total,
                               out=np.zeros_like(ece_width), where=total > 0)

    ascending = np.argsort(scores)
    all_counts = (positives + negatives)[:, ascending].astype(float)
    pos_ascending = positives[:, ascending].astype(float)
    sorted_scores = scores[ascending]
    cdf_after = np.cumsum(all_counts, axis=1)
    cdf_before = cdf_after - all_counts
    total_float = total.astype(float)
    ece_mass = np.zeros(len(counts), dtype=float)
    pos_rate = np.divide(pos_ascending, all_counts, out=np.zeros_like(pos_ascending), where=all_counts > 0)
    for bin_index in range(10):
        low = total_float * bin_index / 10
        high = total_float * (bin_index + 1) / 10
        mass = np.maximum(0.0, np.minimum(cdf_after, high[:, None]) - np.maximum(cdf_before, low[:, None]))
        predicted_sum = mass @ sorted_scores
        observed_sum = (mass * pos_rate).sum(axis=1)
        ece_mass += np.divide(np.abs(predicted_sum - observed_sum), total_float,
                              out=np.zeros_like(ece_mass), where=total_float > 0)
    return {"precision": precision, "recall": recall, "f1": f1, "pr_auc": pr_auc,
            "ece": ece_width, "ece_equal_mass": ece_mass}


def repeat_histograms(rows_by_repeat: list[list[dict[str, Any]]], clusters: list[str],
                      weights: np.ndarray, covered_only: bool = False) -> dict[str, Any]:
    points, bootstraps = [], []
    for rows in rows_by_repeat:
        hist, ap_hist, levels = make_hist(rows, clusters, covered_only)
        aggregated = weights @ hist.reshape(len(clusters), -1)
        boot_counts = aggregated.reshape(N_BOOT, 2, len(levels))
        aggregated_ap = weights @ ap_hist.reshape(len(clusters), -1)
        boot_ap_counts = aggregated_ap.reshape(N_BOOT, 2, len(levels))
        point_counts = np.ones((1, len(clusters)), dtype=np.int16) @ hist.reshape(len(clusters), -1)
        point_ap = np.ones((1, len(clusters)), dtype=np.int16) @ ap_hist.reshape(len(clusters), -1)
        points.append(histogram_metrics(point_counts.reshape(1, 2, len(levels)), levels,
                                        point_ap.reshape(1, 2, len(levels))))
        bootstraps.append(histogram_metrics(boot_counts, levels, boot_ap_counts))
    result: dict[str, Any] = {"point": {}, "bootstrap": {}, "repeat_values": points}
    names = set.intersection(*(set(item) for item in points))
    for name in names:
        per_repeat = np.asarray([item[name][0] for item in points], dtype=float)
        repeat_mean = float(np.mean(per_repeat))
        repeat_sd = float(np.std(per_repeat, ddof=1)) if len(per_repeat) > 1 else 0.0
        samples = np.mean(np.stack([item[name] for item in bootstraps], axis=0), axis=0)
        result["point"][name] = (repeat_mean, repeat_sd)
        result["bootstrap"][name] = samples
        result.setdefault("ci", {})[name] = tuple(float(x) for x in np.percentile(samples, [2.5, 97.5]))
    return result


def direct_metric(rows: list[dict[str, Any]], threshold: float = 0.5) -> dict[str, float]:
    total_positive = sum(row["label"] for row in rows)
    predicted = [row for row in rows if row["predictable"] and row["p"] >= threshold]
    tp = sum(row["label"] for row in predicted)
    fp = len(predicted) - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / total_positive if total_positive else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def best_threshold(rows: list[dict[str, Any]]) -> tuple[float, dict[str, float]]:
    values = {0.5} | {row["p"] for row in rows if row["predictable"]}
    best_t = 0.5
    best = direct_metric(rows, best_t)
    for threshold in sorted(values):
        current = direct_metric(rows, threshold)
        if current["f1"] > best["f1"] + 1e-12 or (abs(current["f1"] - best["f1"]) <= 1e-12 and threshold > best_t):
            best_t, best = threshold, current
    return best_t, best


def fold_map(rows: list[dict[str, Any]]) -> dict[str, int]:
    rng = random.Random(CV_SEED)
    positive = sorted({row["cluster"] for row in rows if row["role"] == "positive"})
    negative = sorted({row["cluster"] for row in rows if row["role"] == "negative"})
    result = {}
    for clusters in (positive, negative):
        rng.shuffle(clusters)
        result.update({cluster: index % 5 for index, cluster in enumerate(clusters)})
    return result


def cv_summary(rows_by_repeat: list[list[dict[str, Any]]]) -> dict[str, Any]:
    all_oof, thresholds = [], []
    for rows in rows_by_repeat:
        folds = fold_map(rows)
        oof = []
        for fold in range(5):
            train = [row for row in rows if folds[row["cluster"]] != fold]
            test = [row for row in rows if folds[row["cluster"]] == fold]
            threshold, _ = best_threshold(train)
            thresholds.append(threshold)
            oof.extend({**row, "p": row["p"] if row["predictable"] and row["p"] >= threshold else 0.0,
                        "predictable": row["predictable"]} for row in test)
        all_oof.append(direct_metric(oof, 0.5))
    means = {name: statistics.mean(row[name] for row in all_oof) for name in ("precision", "recall", "f1")}
    sds = {name: statistics.stdev(row[name] for row in all_oof) if len(all_oof) > 1 else 0.0
           for name in ("precision", "recall", "f1")}
    return {"mean": means, "sd": sds, "thresholds": thresholds,
            "threshold_median": statistics.median(thresholds),
            "threshold_min": min(thresholds), "threshold_max": max(thresholds)}


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def fmt_mean_sd(pair: tuple[float, float], digits: int = 3) -> str:
    return f"{fmt(pair[0], digits)} ± {fmt(pair[1], digits)}"


def fmt_delta(value: float) -> str:
    return "+0.000000000" if abs(value) < 0.0000000005 else f"{value:+.9f}"


def fmt_metric(result: dict[str, Any], name: str) -> str:
    mean, sd = result["point"][name]
    low, high = result["ci"][name]
    return f"{mean:.3f} ± {sd:.3f}; [{low:.3f}, {high:.3f}]"


def transform_native_selection(k: int, judge: str,
                                rows: dict[tuple[str, str], dict[str, Any]]) -> dict[tuple[str, str], float]:
    if judge not in SELECTION_JUDGES:
        raise ValueError(f"Not a native selection output: {judge}")
    expected = expected_pairs(k)
    by_source: dict[str, list[tuple[tuple[str, str], dict[str, Any]]]] = defaultdict(list)
    for pair, row in rows.items():
        if pair in expected:
            by_source[pair[0]].append((pair, row))
    selected: dict[tuple[str, str], float] = {}
    for source_id, candidates in by_source.items():
        if judge == "jev_choice":
            choices = {str(row.get("choice", "none")) for _, row in candidates}
            if len(choices) != 1:
                raise AssertionError(f"Inconsistent Jev choices for {source_id}: {choices}")
            choice = next(iter(choices))
            candidate_ids = {pair[1] for pair, _ in candidates}
            if choice != "none" and choice not in candidate_ids:
                raise AssertionError(f"Jev selected a candidate outside K={k} for {source_id}: {choice}")
            selected.update({pair: float(pair[1] == choice) for pair, _ in candidates})
        else:
            selected.update({pair: float(bool(row.get("selected"))) for pair, row in candidates})
    if selected.keys() != expected:
        raise AssertionError(f"Incomplete native selection cache: {len(selected)} of {len(expected)} pairs")
    return selected


def selection_top1_accuracy(judge: str, rows: dict[tuple[str, str], dict[str, Any]]) -> float:
    _, by_slide = relation_maps()
    positive_sources = [source for source in DATA["sources"] if source["role"] == "positive"]
    correct = 0
    for source in positive_sources:
        sid = source["source_id"]
        candidates = [(pair, row) for pair, row in rows.items() if pair[0] == sid]
        if judge == "jev_choice":
            choices = {str(row.get("choice", "none")) for _, row in candidates}
            if len(choices) != 1:
                raise AssertionError(f"Inconsistent Jev choices for {sid}: {choices}")
            top = next(iter(choices))
            top = None if top == "none" else top
        else:
            selected = [(pair[1], row) for pair, row in candidates if row.get("selected")]
            top = max(selected, key=lambda item: (float(item[1]["probability"]), item[0]))[0] if selected else None
        gold = {article_id(number) for link in by_slide.get(sid, []) for number in link["target_articles"]}
        correct += int(top in gold)
    if len(positive_sources) != DATA["positive_slide_count"]:
        raise AssertionError("Positive-slide top-1 denominator changed")
    return correct / len(positive_sources)


def cache_call_records() -> list[dict[str, Any]]:
    records = []
    for path in CACHE.rglob("*.json"):
        try:
            row = read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(row, dict) and row.get("_api_call"):
            row["_path"] = path.relative_to(CACHE).as_posix()
            records.append(row)
    return records


def usage_cost(record: dict[str, Any]) -> tuple[int, int, int, float]:
    usage = record.get("usage") or {}
    input_tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
    output_tokens = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
    cached = min(input_tokens, int(usage.get("cached_input_tokens", usage.get("cached_tokens", 0)) or 0))
    if record.get("provider") == "jev":
        cost = input_tokens * PRICE["jev_input"] / 1_000_000
    else:
        cost = ((input_tokens - cached) * PRICE["openai_input"] + cached * PRICE["openai_cached_input"]
                + output_tokens * PRICE["openai_output"]) / 1_000_000
    return input_tokens, cached, output_tokens, cost


def cost_rollup(records: list[dict[str, Any]], setting: str, judge: str) -> dict[str, Any]:
    selected = [row for row in records if row.get("candidate_setting", "baseline") == setting and row.get("judge") == judge]
    totals = [usage_cost(row) for row in selected]
    return {
        "calls": len(selected),
        "input": sum(row[0] for row in totals), "cached": sum(row[1] for row in totals),
        "output": sum(row[2] for row in totals), "recomputed": sum(row[3] for row in totals),
        "recorded": sum(float(row.get("cost_usd", 0.0)) for row in selected),
        "latency": sum(float(row.get("latency_seconds", 0.0)) for row in selected),
    }


def prompt_hashes() -> list[tuple[str, str]]:
    output = []
    for name in ("common.md", "jev_pair.md", "jev_choice.md", "llm_pair.json", "llm_list.json", "cascade.md"):
        path = HERE / "prompts" / name
        output.append((f"paper_jev/experiments/prompts/{name}", hashlib.sha256(path.read_bytes()).hexdigest()))
    return output


def base_and_projection() -> dict[str, Any]:
    cost_latency = read_json(SUMMARY / "cost_latency.json")
    downstream_cost = read_json(SUMMARY / "downstream_cost_latency.json")
    full_cost = read_json(SUMMARY / "full_ragas_cost_latency.json")
    followup = read_json(SUMMARY / "followup_summary.json")
    return {"judge": cost_latency, "downstream": downstream_cost, "full": full_cost, "followup": followup}


def write_checklist(score_data: dict[tuple[int, str, str], list[tuple[tuple[str, str], dict[str, Any]]]]) -> int:
    source_map = {source["source_id"]: source for source in DATA["sources"]}
    _, by_slide = relation_maps()
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for (k, judge, repeat), raw_rows in score_data.items():
        raw = {pair: row for pair, row in raw_rows}
        for source in DATA["sources"]:
            sid = source["source_id"]
            canonical = canonical_slide(sid) if source["role"] == "negative" else sid
            labels = {article_id(n) for link in by_slide.get(sid, []) for n in link["target_articles"]}
            for candidate in candidates_for(source, k):
                cid = candidate["article_id"]
                if cid in labels:
                    continue
                pair_key = (canonical, cid)
                item = grouped.setdefault(pair_key, {"source_ids": set(), "source_role": source["role"], "scores": {}})
                item["source_ids"].add(sid)
                p = float(raw.get((sid, cid), {}).get("probability", 0.0))
                key = f"{judge}_k{k}"
                item["scores"][key] = max(item["scores"].get(key, 0.0), p)

    eligible = []
    judge_names = {"jev_pair": "Jev pair", "jev_choice": "Jev choice", "llm_pair": "LLM pair",
                   "llm_list": "LLM list", "cascade": "Cascade"}
    for (sid, cid), item in grouped.items():
        scores = item["scores"]
        best_key, best_p = max(scores.items(), key=lambda pair: pair[1]) if scores else ("", 0.0)
        if best_p < 0.8:
            continue
        best_judge = best_key.split("_k", 1)[0]
        source = next(source_map[source_id] for source_id in sorted(item["source_ids"]))
        article = next((article for article in DATA["articles"].values() if article["id"] == cid), None)
        if article is None:
            raise ValueError(f"Missing article text for {cid}")
        source_text = re.sub(r"\s+", " ", source.get("title", "") + "\n" + source.get("text", "")).strip()
        article_text = re.sub(r"\s+", " ", article.get("text", "")).strip()
        tier = "≥0.90" if best_p >= 0.90 else "0.80–0.899"
        eligible.append({
            "source_slide": sid, "draw_ids": ";".join(sorted(item["source_ids"])),
            "source_role": item["source_role"], "candidate_article": article["number"],
            "dominant_judge": judge_names[best_judge], "max_probability": best_p,
            "max_probability_variant": best_key, "confidence_stratum": tier,
            "slide_excerpt": source_text[:420], "article_excerpt": article_text[:420],
            **{name: scores.get(name, "") for name in (
                "jev_pair_k10", "jev_choice_k10", "llm_pair_k10", "llm_list_k10", "cascade_k10",
                "jev_pair_k50", "jev_choice_k50", "cascade_k50")},
        })

    rng = random.Random(FP_SEED)
    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in eligible:
        strata[(item["dominant_judge"], item["confidence_stratum"])].append(item)
    selected = []
    used = set()
    for key in sorted(strata):
        pool = sorted(strata[key], key=lambda item: (item["source_slide"], item["candidate_article"]))
        chosen = rng.sample(pool, min(4, len(pool)))
        selected.extend(chosen)
        used.update((item["source_slide"], item["candidate_article"]) for item in chosen)
    if len(selected) < 40:
        rest = [item for item in eligible if (item["source_slide"], item["candidate_article"]) not in used]
        selected.extend(rng.sample(rest, min(40 - len(selected), len(rest))))
    selected = selected[:40]
    fields = ["review_id", "source_slide", "draw_ids", "source_role", "candidate_article", "dominant_judge",
              "max_probability", "max_probability_variant", "confidence_stratum", "slide_excerpt", "article_excerpt",
              "jev_pair_k10", "jev_choice_k10", "llm_pair_k10", "llm_list_k10", "cascade_k10",
              "jev_pair_k50", "jev_choice_k50", "cascade_k50", "reviewer_1_related", "reviewer_2_related"]
    csv_path = PAPER / "data" / "fp_review_checklist.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, item in enumerate(selected, 1):
            writer.writerow({"review_id": f"FP{index:02d}", **item,
                             "reviewer_1_related": "", "reviewer_2_related": ""})

    lines = [
        "# Unapproved high-confidence prediction review checklist", "",
        "These are candidate edges not present in the current approved-link gold, not verified false links. "
        "Sample: up to 40 unique slide/article pairs with max cached probability ≥0.80, stratified by the dominant judge and confidence band; "
        "fixed sample seed 20261020. Repeated negative draws are collapsed to the underlying slide and their maximum cached probability is used for screening. "
        "The CSV contains all per-judge probabilities and excerpts; each probability is the maximum across complete cached repeats for that variant.", "",
        "Reviewers should independently mark whether the slide and article are related; do not treat approval status as a relevance label.", "",
        "| ID | Slide | Article | Dominant judge | Max p | Band | Slide excerpt | Article excerpt | Reviewer 1 related? (yes/no/unsure) | Reviewer 2 related? (yes/no/unsure) |",
        "|---|---|---:|---|---:|---|---|---|---|---|",
    ]
    for index, item in enumerate(selected, 1):
        slide_excerpt = item["slide_excerpt"].replace("|", "\\|")
        article_excerpt = item["article_excerpt"].replace("|", "\\|")
        lines.append(f"| FP{index:02d} | {item['source_slide']} | {item['candidate_article']} | {item['dominant_judge']} | "
                     f"{item['max_probability']:.3f} | {item['confidence_stratum']} | {slide_excerpt} | "
                     f"{article_excerpt} |  |  |")
    (PAPER / "data" / "fp_review_checklist.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(selected)


def make_pending_credit(costs: dict[str, Any]) -> str:
    baseline_downstream = costs["downstream"]
    full = costs["full"]
    followup = costs["followup"]
    k100_costs = followup["costs"]["hybrid_100"]
    llm_projection = followup["llm_pair_k100"]["projected_one_repeat_usd"]
    llm_partial = float(followup["llm_pair_k100"].get("partial_usage", {}).get("cost_usd", 0.0))
    llm_remaining = max(0.0, 3 * llm_projection - llm_partial)
    pair_k100 = float(k100_costs["jev_pair"]["cost_usd"])
    choice_k100 = float(k100_costs["jev_choice"]["cost_usd"])
    cascade_stage_k100 = float(k100_costs["cascade"]["cost_usd"])
    jev_repeats_remaining = 2 * (pair_k100 + choice_k100)
    cascade_repeats_remaining = 2 * cascade_stage_k100
    retrieval_repeat = sum(float(row["cost_usd"]) for row in baseline_downstream.values())
    retrieval_remaining = 2 * retrieval_repeat
    full_repeat = sum(float(row["cost_usd"]) for row in full.values())
    full_remaining = 2 * full_repeat
    # shortcut: K=50 downstream cost uses K=10 cache rates until a measured K=50 run exists.
    k50_proxy_one = float(baseline_downstream.get("jev_pair", {}).get("cost_usd", 0)) + float(
        baseline_downstream.get("cascade", {}).get("cost_usd", 0))
    k50_projection = 3 * k50_proxy_one
    total_openai = retrieval_remaining + full_remaining + k50_projection + llm_remaining + cascade_repeats_remaining
    total_jev = jev_repeats_remaining
    return f"""# Work pending new API credits

No API was called to prepare this appendix. Costs below are planning estimates from the recorded cache usage and price rates in `README.md`; actual calls vary with cache hits, response size, and provider pricing. K=100 estimates use its one completed repeat; K=50 downstream estimates use K=10 downstream calls as a proxy.

| Pending work | Projected additional OpenAI cost | Projected additional Jev cost | Basis |
|---|---:|---:|---|
| K=10 downstream retrieval repeats r2/r3 for gold, none, jev_pair, llm_pair, cascade | ${retrieval_remaining:.6f} | $0.000000 | 2 × sum of cached r1 costs |
| K=10 full RAGAS graph repeats r2/r3 for gold, jev_choice, llm_pair | ${full_remaining:.6f} | $0.000000 | 2 × cached full-RAGAS cost |
| K=50 best_jev and best_cascade downstream, three repeats each | ${k50_projection:.6f} | $0.000000 | 3 × K=10 Jev pair and cascade retrieval costs, proxy only |
| K=100 Jev pair/choice and cascade repeats r2/r3 | ${cascade_repeats_remaining:.6f} | ${jev_repeats_remaining:.6f} | 2 × observed K=100 per-repeat incremental costs by provider |
| K=100 LLM pair: finish partial r1 and run r2/r3 | ${llm_remaining:.6f} | $0.000000 | 3 × projected full-repeat cost minus USD {llm_partial:.6f} already spent on partial r1 |
| **Total estimated new credit** | **${total_openai:.6f}** | **${total_jev:.6f}** | Does not include local runtime or downstream K=50 uncertainty |

## Exact commands

Run from `ROOT/back/` after credits are available. The commands deliberately use new repeat tags and output directories so r1 cache/results remain auditable.

### K=10 retrieval-only downstream r2/r3

```powershell
$env:ROOT = "D:/Codes/Dongguk_University/2026-da-al-g"
$env:PAPER_JEV = "C:/Users/colin_laptop/orca/workspaces/2026-da-al-g/jev-r2an/paper_jev"
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
$variants = @("gold", "none", "jev_pair", "llm_pair", "cascade")
foreach ($repeat in @("r2", "r3")) {{
    foreach ($variant in $variants) {{
        $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\\\', '/'
        $env:DATABASE_URL = "sqlite:///$dbPath"
        $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat/openai_usage.jsonl"
        uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --variant proposed --skip-ragas --repeat-tag $repeat --run-id "downstream_${{variant}}_${{repeat}}" --resume --output-dir "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat"
    }}
}}
```

### K=10 full RAGAS graph repeats r2/r3

```powershell
$variants = @("gold", "jev_choice", "llm_pair")
foreach ($repeat in @("r2", "r3")) {{
    foreach ($variant in $variants) {{
        $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\\\', '/'
        $env:DATABASE_URL = "sqlite:///$dbPath"
        $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/full_ragas/$variant/$repeat/openai_usage.jsonl"
        uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --cases graph --variant proposed --repeat-tag $repeat --run-id "full_ragas_${{variant}}_${{repeat}}" --resume --output-dir "$env:PAPER_JEV/experiments/runs/full_ragas/$variant/$repeat"
    }}
}}
```

### K=50 best-link downstream r1/r2/r3

```powershell
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" build-dbs --db "$env:ROOT/data/data_graph/daalgi.db"
$variants = @("best_jev", "best_cascade")
foreach ($repeat in @("r1", "r2", "r3")) {{
    foreach ($variant in $variants) {{
        $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\\\', '/'
        $env:DATABASE_URL = "sqlite:///$dbPath"
        $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat/openai_usage.jsonl"
        uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --variant proposed --skip-ragas --repeat-tag $repeat --run-id "downstream_${{variant}}_${{repeat}}" --resume --output-dir "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat"
    }}
}}
```

### Finish K=100 Jev/cascade repeats and K=100 LLM pair

```powershell
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" judge --settings hybrid_100 --judges jev_pair jev_choice cascade --repeats r2 r3 --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" judge --settings hybrid_100 --judges llm_pair --repeats r1 r2 r3 --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" aggregate
```

The LLM projection assumes completing all three K=100 repeats; r1 is currently partial (302/800 calls). The K=100 Jev and cascade projection is incremental over cached lower-K scores. The K=50 downstream projection is the least certain because its link set was never evaluated downstream.
"""


def generate() -> None:
    if len(DATA["gold_links"]) != 36 or len(DATA["gold_edges"]) != 96:
        raise AssertionError("Unexpected experiment snapshot; expected 36 link records and 96 gold targets")
    if DATA.get("seed") != 20261017 or DATA.get("negative_slide_count") != 80:
        raise AssertionError("Unexpected source sampling metadata")

    models: dict[tuple[int, str], list[dict[tuple[str, str], dict[str, Any]]]] = {}
    row_data: dict[tuple[int, str, str, str], list[list[dict[str, Any]]]] = {}
    available_judges = {10: K10_JUDGES, 50: K50_JUDGES}
    for k, judges in available_judges.items():
        for judge in judges:
            maps, _ = score_maps(k, judge)
            models[(k, judge)] = maps
            for unit in ("link_record", "slide_edge"):
                row_maps = [transform_native_selection(k, judge, raw) for raw in maps] if judge in SELECTION_JUDGES else [candidate_score_map(k, raw) for raw in maps]
                row_data[(k, unit, judge, "all")] = [build_rows(k, score_map, unit) for score_map in row_maps]

    first_rows = row_data[(10, "link_record", K10_JUDGES[0], "all")][0]
    clusters, weights = cluster_weights(first_rows, BOOT_SEED)
    all_results: dict[tuple[int, str, str], dict[str, Any]] = {}
    all_rows: dict[tuple[int, str, str], list[list[dict[str, Any]]]] = {}
    for unit in ("link_record", "slide_edge"):
        for k, judges in available_judges.items():
            for judge in judges:
                rows_by_repeat = row_data[(k, unit, judge, "all")]
                other_clusters = {row["cluster"] for rows in rows_by_repeat for row in rows}
                if other_clusters != set(clusters):
                    raise AssertionError(f"Cluster set differs across {unit} K={k} {judge}")
                result = repeat_histograms(rows_by_repeat, clusters, weights)
                all_results[(k, unit, judge)] = result
                all_rows[(k, unit, judge)] = rows_by_repeat

    result_lines = [
        "# Round 2 cached re-analysis", "",
        "All values below are recomputed from `paper_jev/experiments/cache/`; the script imports no API client and makes no network calls. "
        "Jev pair, LLM pair, and cascade share the candidate-level yes/no event and are compared on probability/ranking metrics. Jev choice and LLM list use their native selected edges and are reported as discrete selection outputs; their one-of-N or multi-label scores are not compared with pair-level ECE.",
        "P/R/F1 and false-positive counts measure agreement with the current approved graph; an unapproved candidate is not independently confirmed irrelevant.", "",
        "## Evaluation units and denominators", "",
        "| Quantity | Count / mapping |", "|---|---:|",
        f"| Approved link records | {len(DATA['gold_links'])} |",
        f"| Record/article targets (existing gold edges) | {len(DATA['gold_edges'])} |",
        f"| Selected positive pages | {DATA['positive_slide_count']} |",
        f"| Positive selection-page/article edges | {sum(len(link['source_pages']) * len(link['target_articles']) for link in DATA['gold_links'])} |",
        f"| Negative slide draws / unique source slides | {DATA['negative_slide_count']} / {DATA['negative_unique_slide_count']} |",
        f"| Sampled duplicate negative draws | {DATA['negative_slide_count'] - DATA['negative_unique_slide_count']} |",
        "| Slide-article edge | Each page inside an approved selection crossed with every target article in that record; each sampled unlinked page contributes its retrieved slide/article candidates as negatives. A target omitted from that page's K candidates is retained as a zero-score false negative. |",
        "| Link-record level | Each approved record is collapsed to record/article targets; when a record spans pages, the cached probability is the maximum over its selected pages. The 80 negative slide draws remain separate negative candidate groups. |",
        "| Candidate-missing gold | Included as p=0 for recall and ECE, and always retained as a false negative; it is never threshold-predictable. PR-AUC ranks candidate-scored edges only but uses all gold positives in its recall denominator, matching the existing experiment implementation. |",
        "| False positives from negative controls | Counted at p≥0.5 on all candidate edges from the 80 negative draws, including the three duplicate draws. |", "",
        "The 36 link records and 77 unique negative slides are resampled as separate cluster strata. A sampled negative cluster carries all of its original draw copies, preserving the observed duplicate weighting. Each bootstrap uses 2,000 resamples and seed 20261018. The interval is a percentile 95% cluster-bootstrap interval for the mean metric over available API repeats; the `±` term is the sample SD across repeats and is not a confidence interval.", "",
        "## Candidate coverage", "",
        "| K | Target link/article edges covered | Candidate recall | Target page/article edges covered | Page-edge recall |", "|---:|---:|---:|---:|---:|",
    ]
    for k in (10, 50):
        link_cover = 0
        page_total = 0
        page_cover = 0
        source_map = {source["source_id"]: source for source in DATA["sources"]}
        for link in DATA["gold_links"]:
            for number in link["target_articles"]:
                cid = article_id(number)
                link_cover += int(any(cid in {c["article_id"] for c in candidates_for(source_map[slide_id(link['source_version_id'], page)], k)}
                                      for page in link["source_pages"]))
                for page in link["source_pages"]:
                    page_total += 1
                    sid = slide_id(link["source_version_id"], page)
                    page_cover += int(cid in {c["article_id"] for c in candidates_for(source_map[sid], k)})
        result_lines.append(f"| {k} | {link_cover}/96 | {link_cover / 96:.3f} | {page_cover}/{page_total} | {page_cover / page_total:.3f} |")
    result_lines += [
        "", "## Pair-level yes/no results with sample uncertainty", "",
        "The primary unit is the slide-article edge: each page in an approved selection is crossed with each target article, and each negative-slide draw contributes candidate edges. Each cell is `mean ± repeat SD; [95% cluster-bootstrap CI]`, over 3 repeats. Candidate-missing gold is p=0 in end-to-end metrics; candidate-covered metrics exclude only those missing gold edges. PR-AUC ranks candidate-scored edges with all gold positives in the recall denominator. ECE is 10-bin equal-width and only compares pair-level yes/no probabilities. Values measure agreement with the approved graph, not verified relevance accuracy.", "",
    ]
    for unit, title in (("slide_edge", "Slide-article edge unit"), ("link_record", "Link-record unit")):
        result_lines += [f"### {title}", "", "| K | Judge | P@0.5 | R@0.5 | F1@0.5 | PR-AUC | ECE |", "|---:|---|---|---|---|---|---|"]
        for k, judges in available_judges.items():
            for judge in judges:
                if judge not in PAIR_JUDGES:
                    continue
                result = all_results[(k, unit, judge)]
                result_lines.append("| " + " | ".join([str(k), judge] + [fmt_metric(result, metric) for metric in METRICS]) + " |")
        result_lines.append("")
    result_lines += [
        "Candidate-covered metrics below use the same slide-article unit and available pair-level yes/no judges:", "",
        "| K | Judge | Covered P@0.5 | Covered R@0.5 | Covered F1@0.5 | Covered PR-AUC |", "|---:|---|---|---|---|---|",
    ]
    for k, judges in available_judges.items():
        for judge in judges:
            if judge not in PAIR_JUDGES:
                continue
            covered = repeat_histograms(all_rows[(k, "slide_edge", judge)], clusters, weights, covered_only=True)
            result_lines.append("| " + " | ".join([str(k), judge] + [fmt_metric(covered, metric) for metric in ("precision", "recall", "f1", "pr_auc")]) + " |")
    result_lines += [
        "", "K=50 LLM pair has no complete cached run and is omitted; incomplete K=100 runs have no performance estimates.", "",
        "## Native selection outputs", "",
        "Selection precision/recall/F1 and FP counts use the same slide-article edge labels as the pair-level table. Top-1 accuracy is the fraction of 80 positive source pages whose Jev choice or highest-confidence selected LLM-list item matches any approved target article; an empty output is incorrect. No selection ECE is calculated.", "",
        "| K | Judge | End-to-end P/R/F1 | Candidate-covered P/R/F1 | FP edges | Positive-page top-1 accuracy |", "|---:|---|---|---|---:|---:|",
    ]
    for k in (10, 50):
        for judge in (("jev_choice", "llm_list") if k == 10 else ("jev_choice",)):
            result = all_results[(k, "slide_edge", judge)]
            rows_by_repeat = all_rows[(k, "slide_edge", judge)]
            covered = repeat_histograms(rows_by_repeat, clusters, weights, covered_only=True)
            fp_counts = [sum(row["label"] == 0 and row["p"] >= 0.5 for row in rows) for rows in rows_by_repeat]
            top1_values = [selection_top1_accuracy(judge, rows) for rows in models[(k, judge)]]
            end_to_end = " / ".join(fmt_metric(result, metric) for metric in ("precision", "recall", "f1"))
            conditional = " / ".join(fmt_metric(covered, metric) for metric in ("precision", "recall", "f1"))
            result_lines.append(f"| {k} | {judge} | {end_to_end} | {conditional} | {statistics.mean(fp_counts):.1f} ± {statistics.stdev(fp_counts):.1f} | "
                                f"{statistics.mean(top1_values):.3f} ± {statistics.stdev(top1_values):.3f} |")
    result_lines += [
        "At p≥0.5, false positives are split between wrong candidate articles on positive pages and candidate links from unlinked negative-slide draws:", "",
        "| K | Judge | FP on positive pages (mean ± repeat SD) | FP from negative draws (mean ± repeat SD) | Total FP |", "|---:|---|---:|---:|---:|",
    ]
    for k, judges in available_judges.items():
        for judge in judges:
            rows_by_repeat = all_rows[(k, "slide_edge", judge)]
            pieces = []
            for rows in rows_by_repeat:
                positive_fp = sum(row["role"] == "positive" and row["label"] == 0 and row["p"] >= 0.5 for row in rows)
                negative_fp = sum(row["role"] == "negative" and row["p"] >= 0.5 for row in rows)
                pieces.append((positive_fp, negative_fp))
            pos = [item[0] for item in pieces]
            neg = [item[1] for item in pieces]
            total = [a + b for a, b in pieces]
            result_lines.append(f"| {k} | {judge} | {statistics.mean(pos):.1f} ± {statistics.stdev(pos):.1f} | "
                                f"{statistics.mean(neg):.1f} ± {statistics.stdev(neg):.1f} | {statistics.mean(total):.1f} |")
    result_lines += ["", "## Paired cluster-bootstrap differences", "",
                     "Delta is first method minus second, paired on the same resampled link and negative-slide clusters and averaged over repeats. ECE differences are limited to the shared pair-level yes/no event.", "",
                     "| Unit | Comparison | Metric | Mean Δ ± repeat SD | 95% paired cluster-bootstrap CI |", "|---|---|---|---:|---:|"]
    comparisons = [(10, "jev_pair", "llm_pair"), (10, "cascade", "llm_pair"), (10, "cascade", "jev_pair"), (50, "jev_pair", "jev_pair@10")]
    for unit in ("slide_edge", "link_record"):
        for k, first, second in comparisons:
            left = all_results[(k, unit, first)]
            right = all_results[(10, unit, second.removesuffix("@10"))] if second.endswith("@10") else all_results[(k, unit, second)]
            for metric in METRICS:
                delta_boot = left["bootstrap"][metric] - right["bootstrap"][metric]
                repeat_delta = []
                for left_rep, right_rep in zip(left["repeat_values"], right["repeat_values"], strict=True):
                    repeat_delta.append(float(left_rep[metric][0] - right_rep[metric][0]))
                sd = statistics.stdev(repeat_delta) if len(repeat_delta) > 1 else 0.0
                label = f"{first} − {second.replace('@10', ' K=10')}" if second.endswith("@10") else f"{first} − {second}"
                result_lines.append(f"| {unit} | {label} (K={k}) | {metric} | {statistics.mean(repeat_delta):.3f} ± {sd:.3f} | "
                                    f"[{np.percentile(delta_boot, 2.5):.3f}, {np.percentile(delta_boot, 97.5):.3f}] |")
    result_lines += [
        "", "## ECE denominator alignment", "",
        "Only pair-level yes/no judges are reported. Each row gives 3-repeat mean ± SD; end-to-end includes missed gold at p=0 and candidate-covered excludes only target edges absent from that unit's candidate set. Equal-mass ECE uses 10 probability-rank bins, splitting tied-score mass fractionally at bin boundaries.", "",
        "| K | Unit | Judge | End-to-end n | Covered n | ECE equal-width, end-to-end | ECE equal-mass, end-to-end | ECE equal-width, covered | ECE equal-mass, covered |", "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for unit in ("slide_edge", "link_record"):
        for k, judges in available_judges.items():
            for judge in judges:
                if judge not in PAIR_JUDGES:
                    continue
                maps = models[(k, judge)]
                all_repeat_rows = all_rows[(k, unit, judge)]
                e2e = all_results[(k, unit, judge)]
                covered = repeat_histograms(all_repeat_rows, clusters, weights, covered_only=True)
                n_all = len(all_repeat_rows[0])
                n_covered = sum(row["covered"] for row in all_repeat_rows[0])
                result_lines.append(f"| {k} | {unit} | {judge} | {n_all} | {n_covered} | "
                                    f"{fmt_mean_sd(e2e['point']['ece'])} | {fmt_mean_sd(e2e['point']['ece_equal_mass'])} | "
                                    f"{fmt_mean_sd(covered['point']['ece'])} | {fmt_mean_sd(covered['point']['ece_equal_mass'])} |")
    result_lines += [
        "", "## Threshold selection", "",
        "Fixed 0.5 is the pre-specified operating point for pair-level probabilities in the cached experiment. Best-F1 uses the same labels and is post-hoc descriptive. The 5-fold threshold CV groups all pages/articles in a link record and keeps duplicate negative draws from the same unique slide in one fold; thresholds are selected on four folds and scored on the held-out fold. CV rows are link-record-level and pooled out-of-fold predictions, with API repeat SD separate.", "",
        "| K | Judge | Fixed P/R/F1@0.5 (mean) | Post-hoc best F1 (mean) | Post-hoc threshold (mean ± SD) | CV threshold median [min,max] | CV OOF P | CV OOF R | CV OOF F1 |", "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    cv_fold_rows: dict[tuple[int, str], dict[str, Any]] = {}
    for k, judges in available_judges.items():
        for judge in judges:
            if judge not in PAIR_JUDGES:
                continue
            rows_by_repeat = all_rows[(k, "link_record", judge)]
            fixed = [direct_metric(rows) for rows in rows_by_repeat]
            bests = [best_threshold(rows) for rows in rows_by_repeat]
            cv = cv_summary(rows_by_repeat)
            cv_fold_rows[(k, judge)] = cv
            threshold_mean = statistics.mean(item[0] for item in bests)
            threshold_sd = statistics.stdev(item[0] for item in bests) if len(bests) > 1 else 0.0
            fixed_text = " / ".join(fmt_mean_sd((statistics.mean(row[name] for row in fixed),
                                                     statistics.stdev(row[name] for row in fixed) if len(fixed) > 1 else 0.0))
                                     for name in ("precision", "recall", "f1"))
            best_f1 = statistics.mean(item[1]["f1"] for item in bests)
            result_lines.append(f"| {k} | {judge} | {fixed_text} | {best_f1:.3f} | {threshold_mean:.3f} ± {threshold_sd:.3f} | "
                                f"{cv['threshold_median']:.3f} [{cv['threshold_min']:.3f}, {cv['threshold_max']:.3f}] | "
                                f"{fmt_mean_sd((cv['mean']['precision'], cv['sd']['precision']))} | "
                                f"{fmt_mean_sd((cv['mean']['recall'], cv['sd']['recall']))} | "
                                f"{fmt_mean_sd((cv['mean']['f1'], cv['sd']['f1']))} |")
    result_lines += [
        "", "## False-positive review sample", "",
        "A false positive here means an unapproved candidate selected at p≥0.5. Since gold is incomplete, these are disagreement cases, not confirmed irrelevant links. Up to 40 candidates with max p≥0.80 were stratified by dominant judge and confidence band; two reviewer columns are left blank in `paper_jev/data/fp_review_checklist.md` and `.csv`.", "",
    ]

    records = cache_call_records()
    call_times = sorted(str(row["created_at_utc"]) for row in records if row.get("created_at_utc"))
    call_span = f"{call_times[0]} to {call_times[-1]} UTC" if call_times else "not present in cache"
    cost_data = base_and_projection()
    summary_cost = cost_data["judge"]
    cost_specs = [("baseline", judge) for judge in K10_JUDGES] + [("hybrid_50", judge) for judge in K50_JUDGES]
    cost_rows = {}
    for setting, judge in cost_specs:
        rollup = cost_rollup(records, setting, judge)
        cost_rows[(setting, judge)] = rollup
    with (PAPER / "data" / "fp_review_checklist.csv").open(encoding="utf-8", newline="") as handle:
        fp_count = sum(1 for _ in csv.DictReader(handle))
    result_lines += [f"Checklist rows: {fp_count}.", "", "## Reproducibility and cost appendix", "",
                     "| API family | Requested model id | Returned model id(s) in response cache |", "|---|---|---|"]
    all_returned: dict[str, set[str]] = defaultdict(set)
    all_requested: dict[str, set[str]] = defaultdict(set)
    for row in records:
        provider = row.get("provider", "unknown")
        all_requested[provider].add(str(row.get("model", "")))
        if (row.get("response") or {}).get("model"):
            all_returned[provider].add(str(row["response"]["model"]))
    result_lines += [f"| Jev System One | `{', '.join(sorted(all_requested['jev']))}` | `{', '.join(sorted(all_returned['jev']))}` |",
                     f"| OpenAI chat | `{', '.join(sorted(all_requested['openai']))}` | `{', '.join(sorted(all_returned['openai']))}` |", "",
                     "Prompt file SHA-256:", "", "| File | SHA-256 |", "|---|---|"]
    for path, digest in prompt_hashes():
        result_lines.append(f"| `{path}` | `{digest}` |")
    result_lines += [
        "", "| Reproduction setting | Value |", "|---|---|",
        "| Data/negative draw seed | 20261017; 80 negative draws from 77 unique slides, with replacement when needed |",
        f"| Cached API call timestamps | {call_span} |",
        "| OpenAI request settings | JSON object response, temperature 0, reasoning effort none, max_completion_tokens 4096 (from the cached runner code) |",
        "| Jev request types | Pair questions use `noul`; per-slide single choice uses `choice`; response probabilities are preserved from cache. |",
        f"| Bootstrap | {N_BOOT} cluster resamples; seed {BOOT_SEED}; 36 approved-record clusters and 77 negative-slide clusters |",
        f"| Grouped threshold CV | 5 folds; seed {CV_SEED}; grouped by approved link id and unique negative slide id |",
        f"| FP checklist stratification | seed {FP_SEED}; max p≥0.80; up to 4 per dominant-judge/confidence stratum |",
        "| Hybrid candidates | K=10 and K=50 from stored 0.6 cosine / 0.4 BM25 rankings; 160 source draws (80 positive pages, 80 negative draws) |",
        "| K=50 reuse | Jev pair imports K=10 pair scores and calls only for newly added candidates; cascade reuses these pair scores. |",
        "| Unavailable K=50 judge | LLM pair has no complete cached K=50 run. |", "",
        "Recomputed cached-call costs use `usage` tokens, not the cache's `cost_usd`: OpenAI gpt-5.6-luna input USD 0.20/M, cached input USD 0.02/M, output USD 1.20/M; Jev input USD 0.042/M and output free. Price sources: [OpenAI gpt-5.6-luna pricing](" + OPENAI_PRICE_URL + ") and [TypeSafe System One API documentation](" + JEV_PRICE_URL + "). Latency is the sum of cached per-call `latency_seconds` for sequential requests; it excludes local parsing, candidate generation, and downstream calls.", "",
        "| Setting | Judge/API stage | API calls | Input / cached input / output tokens | Recomputed USD | Cache-recorded USD | Δ USD | Summed call seconds |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for setting, judge in cost_specs:
        row = cost_rows[(setting, judge)]
        result_lines.append(f"| {setting} | {judge} | {row['calls']} | {row['input']} / {row['cached']} / {row['output']} | "
        f"{row['recomputed']:.6f} | {row['recorded']:.6f} | {fmt_delta(row['recomputed'] - row['recorded'])} | {row['latency']:.2f} |")
    for setting in ("baseline", "hybrid_50"):
        pair = cost_rows[(setting, "jev_pair")]
        cascade = cost_rows[(setting, "cascade")]
        result_lines.append(f"| {setting} | cascade pipeline = Jev pair + LLM cascade | {pair['calls'] + cascade['calls']} | "
                            f"{pair['input'] + cascade['input']} / {pair['cached'] + cascade['cached']} / {pair['output'] + cascade['output']} | "
                            f"{pair['recomputed'] + cascade['recomputed']:.6f} | {pair['recorded'] + cascade['recorded']:.6f} | "
                            f"{fmt_delta(pair['recomputed'] + cascade['recomputed'] - pair['recorded'] - cascade['recorded'])} | "
                            f"{pair['latency'] + cascade['latency']:.2f} |")
    k10_pair, k50_pair = cost_rows[("baseline", "jev_pair")], cost_rows[("hybrid_50", "jev_pair")]
    k10_cascade, k50_cascade = cost_rows[("baseline", "cascade")], cost_rows[("hybrid_50", "cascade")]
    result_lines += [
        f"| hybrid_50 | Jev pair incl. K=10 reuse | {k10_pair['calls'] + k50_pair['calls']} | "
        f"{k10_pair['input'] + k50_pair['input']} / {k10_pair['cached'] + k50_pair['cached']} / {k10_pair['output'] + k50_pair['output']} | "
        f"{k10_pair['recomputed'] + k50_pair['recomputed']:.6f} | {k10_pair['recorded'] + k50_pair['recorded']:.6f} | "
        f"{fmt_delta(k10_pair['recomputed'] + k50_pair['recomputed'] - k10_pair['recorded'] - k50_pair['recorded'])} | "
        f"{k10_pair['latency'] + k50_pair['latency']:.2f} |",
        f"| hybrid_50 | cascade pipeline incl. K=10 reuse | {k10_pair['calls'] + k10_cascade['calls'] + k50_pair['calls'] + k50_cascade['calls']} | "
        f"{k10_pair['input'] + k10_cascade['input'] + k50_pair['input'] + k50_cascade['input']} / "
        f"{k10_pair['cached'] + k10_cascade['cached'] + k50_pair['cached'] + k50_cascade['cached']} / "
        f"{k10_pair['output'] + k10_cascade['output'] + k50_pair['output'] + k50_cascade['output']} | "
        f"{k10_pair['recomputed'] + k10_cascade['recomputed'] + k50_pair['recomputed'] + k50_cascade['recomputed']:.6f} | "
        f"{k10_pair['recorded'] + k10_cascade['recorded'] + k50_pair['recorded'] + k50_cascade['recorded']:.6f} | "
        f"{fmt_delta(k10_pair['recomputed'] + k10_cascade['recomputed'] + k50_pair['recomputed'] + k50_cascade['recomputed'] - k10_pair['recorded'] - k10_cascade['recorded'] - k50_pair['recorded'] - k50_cascade['recorded'])} | "
        f"{k10_pair['latency'] + k10_cascade['latency'] + k50_pair['latency'] + k50_cascade['latency']:.2f} |",
    ]
    result_lines += ["", "Cache completeness by setting:", "", "| K | Judge | Repeat count | Score rows/repeat | Expected slide-candidate rows | Actual API calls in setting cache |",
                     "|---:|---|---:|---:|---:|---:|"]
    for k, judges in available_judges.items():
        setting = "baseline" if k == 10 else "hybrid_50"
        for judge in judges:
            maps = models[(k, judge)]
            call_count = cost_rows[(setting, judge)]["calls"]
            result_lines.append(f"| {k} | {judge} | {len(maps)} | {len(expected_pairs(k))} | {len(expected_pairs(k))} | {call_count} |")
    openai_recomputed = sum(row["recomputed"] for (setting, _), row in cost_rows.items() if setting == "baseline" and _ != "jev_pair" and _ != "jev_choice")
    jev_recomputed = sum(row["recomputed"] for (setting, _), row in cost_rows.items() if setting == "baseline" and _ in {"jev_pair", "jev_choice"})
    result_lines += [
        "", f"K=10 cache-derived judge total: OpenAI USD {openai_recomputed:.6f}, Jev USD {jev_recomputed:.6f}. "
        f"The pre-existing `summary/cost_latency.json` totals are OpenAI USD {sum(summary_cost[j]['cost_usd'] for j in ('llm_pair','llm_list','cascade')):.6f} and Jev USD {summary_cost['jev_pair']['cost_usd'] + summary_cost['jev_choice']['cost_usd']:.6f}; the per-judge cache-vs-summary values are reported above. K=50 stage rows are incremental unless marked `incl. K=10 reuse`; the cumulative cascade pipeline is USD 1.601804.", "",
        "## Credits still required", "",
        "See [pending_credit.md](pending_credit.md) for estimated costs and exact commands for K=10 downstream repeats, K=50 downstream, and completed K=100 repeats/LLM pair.", "",
        "## Notes", "",
        "The slide-edge view distributes every approved record/article target to each page selected by that record; this deliberately differs from the existing record-level max-over-pages score. Negative controls contribute false positives as candidate slide/article predictions, not as confirmed irrelevant edges. The paired intervals are descriptive resampling uncertainty on this one fixed domain and incomplete approved graph; they do not support population-level superiority claims.", "",
        "K=50 downstream, K=100 downstream-independent repeats, a complete K=100 LLM pair run, and expert adjudication of unapproved predictions remain unavailable without new credits or human review.",
    ]
    out_dir = SUMMARY / "round2"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "round2_tables.md").write_text("\n".join(result_lines) + "\n", encoding="utf-8")
    (out_dir / "pending_credit.md").write_text(make_pending_credit(cost_data), encoding="utf-8")
    print(f"Wrote {out_dir / 'round2_tables.md'}; checklist rows={fp_count}; bootstrap resamples={N_BOOT}; no API clients imported.")


if __name__ == "__main__":
    generate()
