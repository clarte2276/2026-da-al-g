from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import statistics
import shutil
import sqlite3
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import run_experiment as exp

HERE = Path(__file__).resolve().parent
BASE_CACHE = HERE / "cache"
FOLLOWUP_CACHE = BASE_CACHE / "followup"
SUMMARY_DIR = HERE / "summary"
RUNS_DIR = HERE / "runs"
K_VALUES = (10, 20, 50, 100)
SETTINGS = ("hybrid_10", "hybrid_20", "hybrid_50", "hybrid_100", "rules",
            "rules_hybrid_50", "rules_hybrid_100")
ARTICLE_REF = re.compile(r"\uC81C\s*(\d+)\s*\uC870(?:\s*\uC758\s*(\d+))?(?:\s*\uC81C\s*\d+\s*\uD56D)?")
APPENDIX_REF = re.compile(r"\uBCC4\s*\uD45C(?:\s*(\d+)(?:\s*\uC758\s*(\d+))?)?")


def normalized(value: str) -> str:
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFKC", value).casefold())


def article_sort(value: str) -> tuple[int, int]:
    match = re.match(r"(\d+)(?:\D+(\d+))?", value)
    return (int(match.group(1)), int(match.group(2) or 0)) if match else (0, 0)


def rule_candidates(source: dict[str, Any], data: dict[str, Any]) -> tuple[set[str], bool, bool]:
    text = f"{source.get('title', '')}\n{source.get('text', '')}"
    articles = data["articles"]
    references: set[str] = set()
    for match in ARTICLE_REF.finditer(text):
        number, subnumber = match.groups()
        number = str(int(number))
        exact = f"{number}\uC758{int(subnumber)}" if subnumber else number
        if exact in articles:
            references.add(exact)
        elif number in articles:
            references.add(number)

    appendix_refs = {
        f"{int(match.group(1))}\uC758{int(match.group(2) or 0)}" if match.group(1) else None
        for match in APPENDIX_REF.finditer(text)
    }
    appendix_refs.discard(None)
    if appendix_refs:
        for number, article in articles.items():
            article_text = article.get("text", "")
            for match in APPENDIX_REF.finditer(article_text):
                appendix = (f"{int(match.group(1))}\uC758{int(match.group(2) or 0)}"
                            if match.group(1) else None)
                if appendix is None or appendix in appendix_refs:
                    references.add(number)

    document_name = str(data.get("regulation_filename", ""))
    stem = Path(document_name).stem
    document_mentioned = len(normalized(stem)) >= 3 and normalized(stem) in normalized(text)
    if document_mentioned:
        references.update(articles)
    return references, bool(ARTICLE_REF.search(text)), document_mentioned


def candidate_lists(data: dict[str, Any]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    result = {}
    for source in data["sources"]:
        hybrid = source.get("candidates_100", source.get("candidates_20", []))
        by_number = {str(candidate["article"]): candidate for candidate in hybrid}
        rule_ids, has_article_ref, has_document_name = rule_candidates(source, data)
        rules = []
        for number in sorted(rule_ids, key=article_sort):
            article = data["articles"].get(number)
            if article is None:
                continue
            rules.append(by_number.get(number, {
                "article_id": article["id"], "article": number, "score": 0.0,
            }))
        variants = {f"hybrid_{k}": hybrid[:k] for k in K_VALUES}
        variants["rules"] = rules
        for k in (50, 100):
            merged = list(hybrid[:k])
            seen = {candidate["article_id"] for candidate in merged}
            merged.extend(candidate for candidate in rules if candidate["article_id"] not in seen)
            variants[f"rules_hybrid_{k}"] = merged
        result[source["source_id"]] = variants
        source["rule_features"] = {
            "explicit_article_mention": has_article_ref,
            "document_name_mention": has_document_name,
        }
    return result


def selected_data(data: dict[str, Any], setting: str, lists: dict[str, dict[str, list[dict[str, Any]]]] | None = None) -> dict[str, Any]:
    if setting not in SETTINGS:
        raise ValueError(f"Unknown candidate setting: {setting}")
    lists = lists or candidate_lists(data)
    selected = copy.deepcopy(data)
    source_map = {source["source_id"]: source for source in selected["sources"]}
    for source in selected["sources"]:
        source["candidates"] = lists[source["source_id"]][setting]
    for group in selected["metric_groups"]:
        candidates = {}
        for source_id in group["source_ids"]:
            for candidate in source_map[source_id]["candidates"]:
                old = candidates.get(candidate["article_id"])
                if old is None or candidate["score"] > old["score"]:
                    candidates[candidate["article_id"]] = candidate
        group["candidates"] = sorted(candidates.values(), key=lambda row: (-row["score"], article_sort(str(row["article"]))))
    return selected


def candidate_stats(data: dict[str, Any], lists: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    sources = {source["source_id"]: source for source in data["sources"]}
    links = {link["link_id"]: link for link in data["gold_links"]}
    stats = {}
    for setting in SETTINGS:
        candidate_ids = {
            source_id: {item["article_id"] for item in settings[setting]}
            for source_id, settings in lists.items()
        }
        hits = sum(
            any(edge["article_id"] in candidate_ids.get(exp.source_id(link["source_version_id"], page), set())
                for page in link["source_pages"])
            for edge in data["gold_edges"] for link in (links[edge["link_id"]],)
        )
        complete = sum(
            all(any(exp.article_id(data["target_version_id"], article) in candidate_ids.get(
                exp.source_id(link["source_version_id"], page), set()) for page in link["source_pages"])
                for article in link["target_articles"])
            for link in data["gold_links"]
        )
        counts = [len(items[setting]) for items in lists.values()]
        stats[setting] = {
            "gold_edge_recall_count": hits, "gold_edge_count": len(data["gold_edges"]),
            "gold_edge_recall": hits / max(1, len(data["gold_edges"])),
            "complete_records": complete, "records": len(data["gold_links"]),
            "record_recall": complete / max(1, len(data["gold_links"])),
            "slide_count": len(counts), "candidate_count_total": sum(counts),
            "candidate_count_mean_per_slide": statistics.mean(counts) if counts else 0.0,
            "candidate_count_median_per_slide": statistics.median(counts) if counts else 0.0,
            "candidate_count_min_per_slide": min(counts) if counts else 0,
            "candidate_count_max_per_slide": max(counts) if counts else 0,
            "slides_with_explicit_article_mention": sum(source.get("rule_features", {}).get("explicit_article_mention", False)
                                                         for source in sources.values()),
            "slides_with_document_name_mention": sum(source.get("rule_features", {}).get("document_name_mention", False)
                                                      for source in sources.values()),
        }
    return stats


def setting_cache(setting: str) -> Path:
    return FOLLOWUP_CACHE / setting


def score_cache(setting: str, judge: str, repeat: str) -> dict[tuple[str, str], dict[str, Any]]:
    old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
    try:
        exp.CACHE_DIR, exp.CACHE_SETTING = setting_cache(setting), setting
        return exp.load_judge_scores(judge, repeat)
    finally:
        exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting


def run_jev_pair_incremental(data: dict[str, Any], setting: str, key: str, repeat: str) -> None:
    target_pairs = {(source["source_id"], candidate["article_id"])
                    for source in data["sources"] for candidate in source["candidates"]}
    old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
    try:
        imported: dict[tuple[str, str], dict[str, Any]] = {}
        exp.CACHE_DIR, exp.CACHE_SETTING = BASE_CACHE, "baseline"
        imported.update(exp.load_judge_scores("jev_pair", repeat))
        if setting == "hybrid_100":
            exp.CACHE_DIR, exp.CACHE_SETTING = setting_cache("hybrid_50"), "hybrid_50"
            imported.update(exp.load_judge_scores("jev_pair", repeat))
        imported = {pair: row for pair, row in imported.items() if pair in target_pairs}

        cache = setting_cache(setting)
        exp.CACHE_DIR, exp.CACHE_SETTING = cache, setting
        import_path = cache / "jev_pair" / repeat / "batch_999_import_lower_k.json"
        exp.write_json(import_path, {"parsed_scores": [
            {"source_id": sid, "candidate_id": cid, "probability": float(row["probability"])}
            for (sid, cid), row in sorted(imported.items())
        ]})
        existing = exp.load_judge_scores("jev_pair", repeat)
        present = set(existing)
        missing = target_pairs - present
        if missing:
            partial = copy.deepcopy(data)
            for source in partial["sources"]:
                source["candidates"] = [candidate for candidate in source["candidates"]
                                         if (source["source_id"], candidate["article_id"]) in missing]
            exp.run_jev_pair(partial, key, repeat)
        completed = exp.load_judge_scores("jev_pair", repeat)
        missing_after = target_pairs - set(completed)
        if missing_after:
            raise RuntimeError(f"Jev pair cache is incomplete for {setting}/{repeat}: {len(missing_after)} pairs")
    finally:
        exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting


def run_jev_choice_chunked(data: dict[str, Any], setting: str, key: str, repeat: str) -> None:
    root = setting_cache(setting)
    merged_rows = []
    for chunk_index, start in enumerate(range(0, 100, 50)):
        chunk = copy.deepcopy(data)
        for source in chunk["sources"]:
            source["candidates"] = source["candidates"][start:start + 50]
        old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
        try:
            exp.CACHE_DIR = root / "choice_chunks" / f"chunk_{chunk_index:02d}"
            exp.CACHE_SETTING = setting
            exp.run_jev_choice(chunk, key, repeat)
            scores = exp.load_judge_scores("jev_choice", repeat)
            expected = {(source["source_id"], candidate["article_id"])
                        for source in chunk["sources"] for candidate in source["candidates"]}
            if expected - set(scores):
                raise RuntimeError(f"Jev choice chunk {chunk_index} is missing {len(expected - set(scores))} scores")
            merged_rows.extend({"source_id": sid, "candidate_id": cid,
                                "probability": float(row["probability"]), "choice": row.get("choice", "none")}
                               for (sid, cid), row in sorted(scores.items()) if (sid, cid) in expected)
        finally:
            exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting
    exp.write_json(root / "jev_choice" / repeat / "batch_900_chunked_import.json", {
        "parsed_scores": merged_rows,
    })


def judge(args: argparse.Namespace) -> None:
    data = exp.load_data()
    if not data["sources"] or "candidates_100" not in data["sources"][0]:
        raise RuntimeError("Run the updated prepare command first to populate candidates_100.")
    lists = candidate_lists(data)
    openai_key, jev_key, model = exp.load_env(args)
    if any(name in args.judges for name in ("jev_pair", "jev_choice", "cascade")) and not jev_key:
        raise RuntimeError("JEV_API_KEY is required for the requested judges")
    if any(name in args.judges for name in ("cascade", "llm_pair")) and not openai_key:
        raise RuntimeError("OPENAI_API_KEY is required for the requested judges")
    for setting in args.settings:
        data_for_setting = selected_data(data, setting, lists)
        for repeat in args.repeats:
            if "jev_pair" in args.judges:
                run_jev_pair_incremental(data_for_setting, setting, jev_key, repeat)
                print(f"completed jev_pair {setting} {repeat}", flush=True)
            if "jev_choice" in args.judges:
                old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
                try:
                    exp.CACHE_DIR, exp.CACHE_SETTING = setting_cache(setting), setting
                    if setting == "hybrid_100":
                        run_jev_choice_chunked(data_for_setting, setting, jev_key, repeat)
                    else:
                        exp.run_jev_choice(data_for_setting, jev_key, repeat)
                finally:
                    exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting
                print(f"completed jev_choice {setting} {repeat}", flush=True)
            if "cascade" in args.judges:
                old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
                try:
                    exp.CACHE_DIR, exp.CACHE_SETTING = setting_cache(setting), setting
                    exp.run_cascade(data_for_setting, openai_key, model, repeat)
                finally:
                    exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting
                print(f"completed cascade {setting} {repeat}", flush=True)
            if "llm_pair" in args.judges:
                if setting != "hybrid_100" or repeat != "r1":
                    continue
                baseline_cost = exp.call_summary({"llm_pair"}, "baseline")["cost_usd"]
                baseline_pairs = max(1, len(data["sources"]) * 10 * len(exp.REPEATS))
                projected_cost = baseline_cost * (len(data_for_setting["sources"]) * 100) / baseline_pairs
                projected_with_margin = projected_cost * 1.25
                if exp.total_spend("openai") + projected_with_margin > exp.OPENAI_CAP_USD:
                    exp.write_json(RUNS_DIR / "llm_pair_k100_status.json", {
                        "status": "projected/not run", "reason": "25% margin projection exceeds remaining OpenAI budget",
                        "projected_one_repeat_usd": projected_cost,
                        "projected_with_25_percent_margin_usd": projected_with_margin,
                    })
                    print(f"skipped llm_pair hybrid_100: projected USD {projected_cost:.6f} "
                          "does not fit the remaining OpenAI budget with 25% margin", flush=True)
                    continue
                old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
                old_token_rate, old_batch_size = exp.OPENAI_TOKEN_ESTIMATE_PER_CHAR, exp.OPENAI_PAIR_BATCH_SIZE
                try:
                    exp.CACHE_DIR, exp.CACHE_SETTING = setting_cache(setting), setting
                    # Baseline prompts measured 0.554 input tokens per serialized character; keep a 1.0-token guard rate.
                    exp.OPENAI_TOKEN_ESTIMATE_PER_CHAR, exp.OPENAI_PAIR_BATCH_SIZE = 1.0, 20
                    exp.run_llm_pair(data_for_setting, openai_key, model, repeat)
                finally:
                    exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting
                    exp.OPENAI_TOKEN_ESTIMATE_PER_CHAR, exp.OPENAI_PAIR_BATCH_SIZE = old_token_rate, old_batch_size
                exp.write_json(RUNS_DIR / "llm_pair_k100_status.json", {
                    "status": "measured", "projected_one_repeat_usd": projected_cost,
                    "projected_with_25_percent_margin_usd": projected_with_margin,
                })
                print(f"completed llm_pair {setting} {repeat}", flush=True)
    print(f"Cumulative Jev USD {exp.total_spend('jev'):.6f} / {exp.JEV_CAP_USD:.2f}; "
          f"OpenAI USD {exp.total_spend('openai'):.6f} / {exp.OPENAI_CAP_USD:.2f}")


def metric_summary(data: dict[str, Any], judge: str, setting: str, repeats: tuple[str, ...]) -> dict[str, Any]:
    pairs, gold = exp.pair_set(data)
    covered = set(pairs) & gold
    rows, conditional = [], []
    available_repeats = []
    old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
    try:
        exp.CACHE_DIR = BASE_CACHE if setting == "hybrid_10" else setting_cache(setting)
        exp.CACHE_SETTING = "baseline" if setting == "hybrid_10" else setting
        for repeat in repeats:
            if judge != "score_only":
                expected = {(source["source_id"], candidate["article_id"])
                            for source in data["sources"] for candidate in source["candidates"]}
                if expected - set(exp.load_judge_scores(judge, repeat)):
                    continue
            scores = exp.pair_predictions(data, judge, repeat if judge != "score_only" else None)
            rows.append(exp.score_metrics(scores, pairs, gold, judge != "score_only"))
            conditional.append(exp.score_metrics(scores, pairs, covered, judge != "score_only"))
            available_repeats.append(repeat)
    finally:
        exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting
    if not rows:
        raise RuntimeError(f"No complete {judge} repeat is available for {setting}")
    fields = ("precision_05", "recall_05", "f1_05", "best_f1", "best_threshold", "pr_auc", "ece")
    summarize = lambda values: {field: exp.mean_sd([row[field] for row in values]) for field in fields}
    return {
        "candidate_setting": setting, "judge": judge, "repeats": available_repeats,
        "repeat_count": len(available_repeats),
        "pairs": len(pairs), "gold_edges": len(gold), "gold_edges_covered": len(covered),
        "gold_edge_coverage": len(covered) / max(1, len(gold)),
        "end_to_end": summarize(rows), "conditional": summarize(conditional),
        "end_to_end_per_repeat": [{key: value for key, value in row.items() if key != "reliability_bins"} for row in rows],
        "conditional_per_repeat": [{key: value for key, value in row.items() if key != "reliability_bins"} for row in conditional],
    }


def metric_display(summary: dict[str, Any], section: str = "end_to_end") -> dict[str, str]:
    out = {}
    for field in ("precision_05", "recall_05", "f1_05", "pr_auc", "ece"):
        avg, sd = summary[section][field]
        out[field] = exp.fmt(avg, sd)
    return out


def candidate_cost(setting: str, judges: set[str]) -> dict[str, Any]:
    old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
    try:
        exp.CACHE_DIR = BASE_CACHE if setting == "baseline" else setting_cache(setting)
        exp.CACHE_SETTING = setting
        return exp.call_summary(judges, setting)
    finally:
        exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting


def build_aggregate(data: dict[str, Any], lists: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    candidates = candidate_stats(data, lists)
    conditional = []
    baseline = selected_data(data, "hybrid_10", lists)
    old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
    try:
        exp.CACHE_DIR, exp.CACHE_SETTING = BASE_CACHE, "baseline"
        for judge in ("score_only", "jev_pair", "jev_choice", "llm_pair", "llm_list", "cascade"):
            conditional.append(metric_summary(baseline, judge, "hybrid_10", ("r1",) if judge == "score_only" else exp.REPEATS))
    finally:
        exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting

    scale = []
    for setting in ("hybrid_50", "hybrid_100"):
        data_for_setting = selected_data(data, setting, lists)
        for judge in ("jev_pair", "jev_choice", "cascade"):
            scale.append(metric_summary(data_for_setting, judge, setting, exp.REPEATS))
            conditional.append(scale[-1])
    llm_scores = score_cache("hybrid_100", "llm_pair", "r1")
    expected_llm_pairs = sum(len(source["candidates"]) for source in selected_data(data, "hybrid_100", lists)["sources"])
    if len(llm_scores) == expected_llm_pairs:
        llm = metric_summary(selected_data(data, "hybrid_100", lists), "llm_pair", "hybrid_100", ("r1",))
        llm["repeat_note"] = "one repeat"
        scale.append(llm)
        conditional.append(llm)

    costs = {}
    for setting in ("hybrid_50", "hybrid_100"):
        costs[setting] = {
            name: candidate_cost(setting, {name})
            for name in ("jev_pair", "jev_choice", "cascade", "llm_pair")
        }
        costs[setting]["cascade_pipeline"] = candidate_cost(setting, {"jev_pair", "cascade"})
    base_pair_cost = candidate_cost("baseline", {"jev_pair"})
    pair_cumulative = {"hybrid_50": base_pair_cost["cost_usd"] + costs["hybrid_50"]["jev_pair"]["cost_usd"]}
    pair_cumulative["hybrid_100"] = pair_cumulative["hybrid_50"] + costs["hybrid_100"]["jev_pair"]["cost_usd"]
    for setting in ("hybrid_50", "hybrid_100"):
        costs[setting]["jev_pair"]["cost_usd_including_reused_lower_k"] = pair_cumulative[setting]
        costs[setting]["cascade_pipeline"]["cost_usd_including_reused_lower_k"] = (
            (candidate_cost("baseline", {"jev_pair", "cascade"})["cost_usd"] if setting == "hybrid_50" else
             candidate_cost("baseline", {"jev_pair", "cascade"})["cost_usd"]
             + costs["hybrid_50"]["cascade_pipeline"]["cost_usd"])
            + costs[setting]["cascade_pipeline"]["cost_usd"]
        )
    llm_baseline = candidate_cost("baseline", {"llm_pair"})
    llm_status_path = RUNS_DIR / "llm_pair_k100_status.json"
    llm_status = exp.read_json(llm_status_path) if llm_status_path.is_file() else {}
    llm_complete = len(llm_scores) == expected_llm_pairs
    llm_projected = {
        "status": "measured" if llm_complete else llm_status.get("status", "incomplete/not run"),
        "pairs_at_k100": len(selected_data(data, "hybrid_100", lists)["sources"]) * 100,
        "baseline_k10_pairs_across_three_repeats": 3 * 160 * 10,
        "measured_k10_cost_usd": llm_baseline["cost_usd"],
        "projected_one_repeat_usd": llm_baseline["cost_usd"] * (160 * 100) / max(1, 3 * 160 * 10),
    }
    if llm_complete:
        llm_projected["measured_cost_usd"] = costs["hybrid_100"]["llm_pair"]["cost_usd"]
    elif llm_status:
        llm_projected.update(llm_status)
        llm_projected["partial_usage"] = costs["hybrid_100"]["llm_pair"]

    f1_rows = [row for row in scale if row["judge"] in {"jev_pair", "jev_choice"} and row["repeat_count"] == 3]
    best_jev = max(f1_rows, key=lambda row: (row["end_to_end"]["f1_05"][0] or 0,
                                             100 if row["candidate_setting"] == "hybrid_100" else 50))
    cascade_rows = [row for row in scale if row["judge"] == "cascade" and row["repeat_count"] == 3]
    best_cascade = max(cascade_rows, key=lambda row: (row["end_to_end"]["f1_05"][0] or 0,
                                                      100 if row["candidate_setting"] == "hybrid_100" else 50))

    return {
        "candidate_generation": candidates, "conditional_judge_metrics": conditional,
        "large_k_metrics": scale, "costs": costs, "llm_pair_k100": llm_projected,
        "best_jev": {"judge": best_jev["judge"], "setting": best_jev["candidate_setting"]},
        "best_cascade": {"judge": "cascade", "setting": best_cascade["candidate_setting"]},
        "cumulative_spend_usd": {"openai": exp.total_spend("openai"), "jev": exp.total_spend("jev")},
        "uncertainty_band": list(exp.UNCERTAINTY_BAND),
    }


def downstream_row(variant: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    result_path = RUNS_DIR / "downstream" / variant / "ragas_results.json"
    cost_path = RUNS_DIR / "downstream" / variant / "openai_usage.jsonl"
    if not result_path.is_file():
        return None, exp.usage_cost_summary(cost_path)
    payload = exp.read_json(result_path)
    eval_set = exp.read_json(HERE / "data" / "eval_set_v3.json")
    graph_names = {case["name"] for case in eval_set.get("cases", []) if case.get("category") == "graph"}
    rows = payload.get("document_cases", [])
    metrics = {}
    for metric in ("recall", "mrr", "ndcg_at_10", "linked_gold_recall"):
        values = [float(row[metric]) for row in rows if isinstance(row.get(metric), (int, float))]
        metrics[metric] = statistics.mean(values) if values else None
    return {"cases": len(rows), "metrics": metrics, "graph_cases": sum(row.get("case") in graph_names for row in rows)}, exp.usage_cost_summary(cost_path)


def append_followup_tables(markdown: str, summary: dict[str, Any], downstream: dict[str, Any]) -> str:
    # Rebuild only this generated appendix so aggregate can be rerun from caches.
    marker = "\n## Follow-up experiments"
    if marker in markdown:
        markdown = markdown.split(marker, 1)[0]
    lines = ["", "## Follow-up experiments", "", "### Candidate recall by setting", "",
             "Rule candidates use explicit article and appendix references; a regulation filename mention admits that document's article units. "
             "Union settings keep hybrid ranking order, then append rule-only candidates.", "",
             "| Setting | Gold edges recalled | Edge recall | Link records fully covered | Record recall | Mean candidates/slide | Total candidates |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for setting, row in summary["candidate_generation"].items():
        lines.append(f"| {setting} | {row['gold_edge_recall_count']}/{row['gold_edge_count']} | {row['gold_edge_recall']:.3f} | "
                     f"{row['complete_records']}/{row['records']} | {row['record_recall']:.3f} | "
                     f"{row['candidate_count_mean_per_slide']:.1f} | {row['candidate_count_total']} |")

    lines += ["", "### Conditional judge metrics", "",
              "End-to-end rows above retain missed gold edges as false negatives. These metrics condition on gold edges present in at least one slide's candidate set; candidate-missing gold edges are excluded from the recall denominator.", "",
              "| Candidate setting | Judge | Repeats | Gold edges covered | Coverage | P@0.5 | R@0.5 | F1@0.5 | PR-AUC | ECE |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary["conditional_judge_metrics"]:
        values = metric_display(row, "conditional")
        lines.append(f"| {row['candidate_setting']} | {row['judge']} | {row['repeat_count']} | {row['gold_edges_covered']}/{row['gold_edges']} | "
                     f"{row['gold_edge_coverage']:.3f} | {values['precision_05']} | {values['recall_05']} | "
                     f"{values['f1_05']} | {values['pr_auc']} | {values['ece']} |")

    lines += ["", "### Large-K Jev, cascade, and LLM scale study", "",
              "Jev pair K=50/K=100 API cost is incremental: K=10 and lower-K pair judgments are reused because pair questions are independent. "
              "The cumulative column includes those reused Jev pair calls. Cascade uses the same inclusive Jev probability band shown in notes.md.", "",
              "| Setting | Judge | Repeats | P@0.5 | R@0.5 | F1@0.5 | PR-AUC | Calls (incremental) | Input tokens | Cost USD (incremental) | Cost USD (incl. reuse) |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary["large_k_metrics"]:
        setting, judge = row["candidate_setting"], row["judge"]
        values = metric_display(row)
        cost_judge = "cascade_pipeline" if judge == "cascade" else judge
        usage = summary["costs"][setting][cost_judge]
        reuse = usage.get("cost_usd_including_reused_lower_k", usage["cost_usd"])
        lines.append(f"| {setting} | {judge} | {row['repeat_count']} | {values['precision_05']} | {values['recall_05']} | {values['f1_05']} | {values['pr_auc']} | "
                     f"{usage['calls']} | {usage['input_tokens']} | {usage['cost_usd']:.6f} | {reuse:.6f} |")
    llm = summary["llm_pair_k100"]
    llm_cost = summary["costs"]["hybrid_100"]["llm_pair"]
    partial = llm.get("partial_usage")
    status = (f"measured one repeat; USD {llm.get('measured_cost_usd', 0):.6f}" if llm["status"] == "measured" else
              f"{llm['status']}; projected USD {llm['projected_one_repeat_usd']:.6f}" +
              (f"; partial USD {partial['cost_usd']:.6f}" if partial else ""))
    llm_metric = next((row for row in summary["large_k_metrics"] if row["judge"] == "llm_pair"), None)
    llm_values = metric_display(llm_metric) if llm_metric else {key: "n/a" for key in ("precision_05", "recall_05", "f1_05", "pr_auc")}
    llm_repeats = llm_metric["repeat_count"] if llm_metric else 0
    lines.append(f"| hybrid_100 | llm_pair | {llm_repeats or 'n/a'} | {llm_values['precision_05']} | {llm_values['recall_05']} | {llm_values['f1_05']} | "
                 f"{llm_values['pr_auc']} | {llm_cost['calls'] if llm['status'] == 'measured' or partial else 'n/a'} | "
                 f"{llm_cost['input_tokens'] if llm['status'] == 'measured' or partial else 'n/a'} | {status} | n/a |")
    lines += ["", f"Best large-K Jev link set (by F1@0.5): `{summary['best_jev']['judge']}` / `{summary['best_jev']['setting']}`. "
              f"Best large-K cascade link set (by F1@0.5): `{summary['best_cascade']['setting']}`. "
              f"Cumulative experiment spend: OpenAI USD {summary['cumulative_spend_usd']['openai']:.6f} / 15.00; "
              f"Jev USD {summary['cumulative_spend_usd']['jev']:.6f} / 5.00."]
    incomplete = [f"{row['candidate_setting']} {row['judge']} ({row['repeat_count']}/3 repeats)"
                  for row in summary["large_k_metrics"] if row["judge"] in {"jev_pair", "jev_choice", "cascade"}
                  and row["repeat_count"] != 3]
    if incomplete:
        lines += ["", "Incomplete Jev-derived scale rows: " + ", ".join(incomplete) + "."]

    downstream_rows = []
    for variant in ("best_jev", "best_cascade"):
        result, cost = downstream_row(variant)
        downstream[variant] = ({"result": result, "cost": cost} if result else
                               {**downstream.get(variant, {}), "status": "not_run"})
        if not result:
            downstream[variant].setdefault("reason", "No downstream result was recorded")
        if not result:
            downstream_rows.append(f"| {variant} | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |")
            continue
        m = result["metrics"]
        show = lambda name: "n/a" if m[name] is None else f"{m[name]:.3f}"
        downstream_rows.append(f"| {variant} | {result['cases']} | {show('recall')} | {show('mrr')} | "
                               f"{show('ndcg_at_10')} | {show('linked_gold_recall')} |")
    lines += ["", "### Large-K downstream link sets", "", "| Link set | Cases | Recall | MRR | nDCG@10 | Linked-gold recall |",
              "|---|---:|---:|---:|---:|---:|", *downstream_rows]
    not_run = [f"{variant}: {value['reason']}" for variant, value in downstream.items() if value.get("status") == "not_run"]
    if not_run:
        lines += ["", "Downstream status: " + "; ".join(not_run) + "."]
    return markdown.rstrip() + "\n" + "\n".join(lines) + "\n"


def write_csv(summary: dict[str, Any]) -> None:
    path = SUMMARY_DIR / "main_table.csv"
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            old_rows = [row for row in csv.DictReader(handle) if row.get("section", "") in {"", "original"}]
    else:
        old_rows = []
    status_path = RUNS_DIR / "followup_downstream_status.json"
    downstream_status = exp.read_json(status_path) if status_path.is_file() else {}
    fields = ["section", "candidate_setting", "judge", "precision_at_0.5", "recall_at_0.5", "f1_at_0.5",
              "best_f1", "best_threshold", "pr_auc", "ece", "determinism", "repeats", "gold_edges_covered",
              "gold_edge_coverage", "candidate_count_mean_per_slide", "candidate_count_total", "candidate_recall",
              "calls", "input_tokens", "cost_usd", "status", "cases", "retrieval_recall", "mrr",
              "ndcg_at_10", "linked_gold_recall", "partial_cost_usd"]
    rows = [{"section": "original", **row} for row in old_rows]
    for setting, row in summary["candidate_generation"].items():
        rows.append({"section": "candidate_recall", "candidate_setting": setting,
                     "candidate_count_mean_per_slide": f"{row['candidate_count_mean_per_slide']:.3f}",
                     "candidate_count_total": row["candidate_count_total"],
                     "candidate_recall": f"{row['gold_edge_recall']:.6f}"})
    for row in summary["conditional_judge_metrics"]:
        values = metric_display(row, "conditional")
        rows.append({"section": "conditional", "candidate_setting": row["candidate_setting"], "judge": row["judge"],
                     "precision_at_0.5": values["precision_05"], "recall_at_0.5": values["recall_05"],
                     "f1_at_0.5": values["f1_05"], "pr_auc": values["pr_auc"], "ece": values["ece"],
                     "repeats": row["repeat_count"], "gold_edges_covered": row["gold_edges_covered"],
                     "gold_edge_coverage": f"{row['gold_edge_coverage']:.6f}"})
    for row in summary["large_k_metrics"]:
        values = metric_display(row)
        setting, judge = row["candidate_setting"], row["judge"]
        usage = summary["costs"][setting]["cascade_pipeline" if judge == "cascade" else judge]
        rows.append({"section": "large_k", "candidate_setting": setting, "judge": judge,
                     "precision_at_0.5": values["precision_05"], "recall_at_0.5": values["recall_05"],
                     "f1_at_0.5": values["f1_05"], "pr_auc": values["pr_auc"], "repeats": row["repeat_count"],
                     "calls": usage["calls"],
                     "input_tokens": usage["input_tokens"], "cost_usd": f"{usage['cost_usd']:.6f}"})
    llm = summary["llm_pair_k100"]
    llm_cost = summary["costs"]["hybrid_100"]["llm_pair"]
    rows.append({"section": "llm_projection", "candidate_setting": "hybrid_100", "judge": "llm_pair",
                 "status": llm["status"],
                 "cost_usd": f"{llm.get('measured_cost_usd', llm['projected_one_repeat_usd']):.6f}",
                 "calls": llm_cost["calls"] if llm.get("partial_usage") else "",
                 "input_tokens": llm_cost["input_tokens"] if llm.get("partial_usage") else "",
                 "partial_cost_usd": f"{llm_cost['cost_usd']:.6f}" if llm.get("partial_usage") else ""})
    baseline_downstream = exp.collect_downstream() or {}
    baseline_costs = exp.collect_downstream_costs()
    for variant in ("gold", "none", "jev_pair", "llm_pair", "cascade", "best_jev", "best_cascade"):
        if variant in baseline_downstream:
            downstream_metrics = baseline_downstream[variant]["metrics"]["all"]
            cases = baseline_downstream[variant]["cases"]
            cost = baseline_costs.get(variant)
        else:
            result, cost = downstream_row(variant)
            if not result:
                if variant in {"best_jev", "best_cascade"}:
                    rows.append({"section": "downstream", "candidate_setting": variant,
                                 "status": "NOT RUN: " + downstream_status.get(variant, {}).get("reason", "no result recorded")})
                continue
            downstream_metrics, cases = result["metrics"], result["cases"]
        rows.append({"section": "downstream", "candidate_setting": variant,
                     "judge": "" if variant in {"gold", "none"} else variant, "cases": cases,
                     "retrieval_recall": downstream_metrics["recall"], "mrr": downstream_metrics["mrr"],
                     "ndcg_at_10": downstream_metrics["ndcg_at_10"],
                     "linked_gold_recall": downstream_metrics["linked_gold_recall"],
                     "calls": cost["calls"] if cost else "", "input_tokens": cost["input_tokens"] if cost else "",
                     "cost_usd": f"{cost['cost_usd']:.6f}" if cost else ""})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def aggregate(_: argparse.Namespace) -> None:
    data = exp.load_data()
    lists = candidate_lists(data)
    summary = build_aggregate(data, lists)
    status_path = RUNS_DIR / "followup_downstream_status.json"
    downstream = exp.read_json(status_path) if status_path.is_file() else {}
    if not isinstance(downstream, dict):
        downstream = {}
    path = SUMMARY_DIR / "main_table.md"
    markdown = path.read_text(encoding="utf-8") if path.exists() else "# Main results\n"
    markdown = append_followup_tables(markdown, summary, downstream)
    path.write_text(markdown, encoding="utf-8")
    exp.write_json(SUMMARY_DIR / "followup_summary.json", summary)
    for key in ("best_jev", "best_cascade"):
        result, cost = downstream_row(key)
        if result:
            downstream[key] = {"result": result, "cost": cost}
    exp.write_json(SUMMARY_DIR / "followup_downstream.json", downstream)
    write_csv(summary)
    notes_path = SUMMARY_DIR / "notes.md"
    notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else "# Experiment notes\n"
    notes = notes.split("\n## Follow-up experiments", 1)[0]
    llm = summary["llm_pair_k100"]
    partial = llm.get("partial_usage")
    notes += (
        "\n\n## Follow-up experiments\n\n"
        "Candidate settings use the stored 0.6 cosine / 0.4 BM25 rank at K=10, 20, 50, and 100. Rule candidates parse explicit article-number and clause references, "
        "plus appendix references, then map them to article units; a regulation filename mention maps to all articles in that document. "
        "Union settings preserve hybrid order and append rule-only article units. No embedding API was called. Candidate counts and recall are reported by setting.\n\n"
        "Conditional precision, recall, F1, PR-AUC, and ECE use only gold edges covered by that setting; end-to-end tables continue to count candidate-missing gold as false negatives. "
        "Jev pair K=50/K=100 reuse the previous K's pair scores because each pair question is independent. Jev choice K=100 uses two 50-candidate requests per slide "
        "after the full request exceeded Jev's context limit. Three repeats were requested; K=50 completed all three. Cascade uses "
        f"the inclusive {exp.UNCERTAINTY_BAND[0]:.2f}-{exp.UNCERTAINTY_BAND[1]:.2f} band.\n\n"
        f"LLM pair K=100: {llm['status']}; full one-repeat cost is USD {llm.get('measured_cost_usd', llm['projected_one_repeat_usd']):.6f}, "
        f"projected from K=10 per-pair API usage at USD {llm['projected_one_repeat_usd']:.6f}"
        + (f"; partial calls {partial['calls']}, {partial['input_tokens']} input tokens, USD {partial['cost_usd']:.6f}. "
           if partial else ". ")
        + "See README.md for exact commands.\n\n"
        f"Cumulative spend after follow-up: OpenAI USD {summary['cumulative_spend_usd']['openai']:.6f} / 15.00; "
        f"Jev USD {summary['cumulative_spend_usd']['jev']:.6f} / 5.00. API response cache entries are under cache/followup/.\n"
    )
    incomplete = [row for row in summary["large_k_metrics"]
                  if row["candidate_setting"] == "hybrid_100" and row["judge"] in {"jev_pair", "jev_choice", "cascade"}
                  and row["repeat_count"] < 3]
    if incomplete:
        notes += ("\nK=100 Jev-derived results have one complete repeat: the next Jev request returned HTTP 402 billing_error "
                  "(no organization credits available), so the remaining repeats were not run. The best-link downstream choice "
                  "uses a complete three-repeat K=50 result. No further Jev requests after the billing error were attempted.\n")
    if llm.get("completed_batches"):
        notes += (f"K=100 LLM pair stopped after {llm['completed_batches']}/{llm['expected_batches']} batches "
                  "because OpenAI returned HTTP 429 insufficient_quota (no credits remaining); no retry was made.\n")
    not_run = [f"{key}: {value['reason']}" for key, value in downstream.items() if value.get("status") == "not_run"]
    if not_run:
        notes += "Downstream status: " + "; ".join(not_run) + ".\n"
    notes_path.write_text(notes, encoding="utf-8")
    print(path)


def build_database(source_db: Path, data: dict[str, Any], judge_name: str, setting: str, output: Path) -> int:
    chosen = selected_data(data, setting)
    maps = []
    old_cache, old_setting = exp.CACHE_DIR, exp.CACHE_SETTING
    try:
        exp.CACHE_DIR, exp.CACHE_SETTING = setting_cache(setting), setting
        for repeat in exp.REPEATS:
            raw = exp.load_judge_scores(judge_name, repeat)
            if not raw:
                raise RuntimeError(f"Missing {judge_name} score cache for {setting}/{repeat}")
            maps.append(exp.pair_predictions(chosen, judge_name, repeat))
    finally:
        exp.CACHE_DIR, exp.CACHE_SETTING = old_cache, old_setting
    pairs, _ = exp.pair_set(chosen)
    group_map = {group["source_id"]: group for group in chosen["metric_groups"]}
    predicted = [pair for pair in pairs if sum(mapping.get(pair, 0.0) >= 0.5 for mapping in maps) >= 2]
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_db, output)
    now = datetime.now(UTC).isoformat()
    with sqlite3.connect(output) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("DELETE FROM document_links")
        inserted = set()
        for sid, cid in predicted:
            group = group_map[sid]
            candidate = next(row for row in group["candidates"] if row["article_id"] == cid)
            article = chosen["articles"][str(candidate["article"])]
            key = (group["source_version_id"], tuple(group["source_pages"]), cid)
            if key in inserted:
                continue
            inserted.add(key)
            conn.execute(
                "INSERT INTO document_links (id,source_version_id,target_version_id,source_selection,target_selection,"
                "relation_type,note,status,created_by,approved_by,created_at,approved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), group["source_version_id"], article["version_id"],
                 json.dumps(group["selection"], ensure_ascii=False),
                 json.dumps({"kind": "text", "version_id": article["version_id"], "ranges": [
                     {"start": article["start"], "end": article["end"], "exact": article["text"]}
                 ]}, ensure_ascii=False), "REFERENCES",
                 f"paper_jev follow-up {judge_name}; three-repeat majority; threshold 0.5; {setting}",
                 "approved", "paper_jev-experiment", "paper_jev-experiment", now, now),
            )
    return len(inserted)


def build_dbs(args: argparse.Namespace) -> None:
    data = exp.load_data()
    summary = exp.read_json(SUMMARY_DIR / "followup_summary.json")
    runtime = exp.PAPER_ROOT / "runtime"
    variants = {
        "best_jev": summary["best_jev"],
        "best_cascade": summary["best_cascade"],
    }
    manifest = {}
    for variant, selected in variants.items():
        output = runtime / f"links_{variant}.sqlite"
        count = build_database(args.db.resolve(), data, selected["judge"], selected["setting"], output)
        manifest[variant] = {**selected, "database": str(output.relative_to(exp.PAPER_ROOT)), "document_links": count}
    exp.write_json(RUNS_DIR / "db_manifest_followup.json", manifest)
    print(json.dumps(manifest, ensure_ascii=True, indent=2))


def candidate_stats_command(_: argparse.Namespace) -> None:
    data = exp.load_data()
    if not data["sources"] or "candidates_100" not in data["sources"][0]:
        raise RuntimeError("Run the updated prepare command first to populate candidates_100.")
    lists = candidate_lists(data)
    stats = candidate_stats(data, lists)
    assert all(len(lists[sid]["hybrid_100"]) == 100 for sid in lists)
    assert all(len(lists[sid]["rules_hybrid_50"]) >= len(lists[sid]["hybrid_50"]) for sid in lists)
    valid_ids = {article["id"] for article in data["articles"].values()}
    assert all(candidate["article_id"] in valid_ids for variants in lists.values()
               for candidates in variants.values() for candidate in candidates)
    exp.write_json(SUMMARY_DIR / "candidate_recall_settings.json", stats)
    print(json.dumps(stats, ensure_ascii=True, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Candidate and judge follow-up experiment")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("judge")
    run.add_argument("--settings", nargs="+", choices=("hybrid_50", "hybrid_100"), default=["hybrid_50", "hybrid_100"])
    run.add_argument("--judges", nargs="+", choices=("jev_pair", "jev_choice", "cascade", "llm_pair"),
                     default=["jev_pair", "jev_choice", "cascade"])
    run.add_argument("--repeats", nargs="+", choices=exp.REPEATS, default=list(exp.REPEATS))
    run.add_argument("--openai-env", type=Path)
    run.add_argument("--jev-env", type=Path)
    agg = sub.add_parser("aggregate")
    sub.add_parser("candidate-stats")
    dbs = sub.add_parser("build-dbs")
    dbs.add_argument("--db", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "judge":
        judge(args)
    elif args.command == "aggregate":
        aggregate(args)
    elif args.command == "candidate-stats":
        candidate_stats_command(args)
    else:
        build_dbs(args)


if __name__ == "__main__":
    main()
