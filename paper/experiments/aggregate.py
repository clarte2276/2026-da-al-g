from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
SUMMARY = ROOT / "summary"
EVAL_SET = ROOT.parent / "data" / "eval_set_v3.json"
DATA_README = ROOT.parent / "data" / "README.md"
HUMAN_CHECKLIST = ROOT.parent / "data" / "human_review_checklist.md"
VARIANTS = ("bm25", "dense", "hybrid", "hybrid_rerank", "link_all", "proposed")
REPEATS = ("r1", "r2", "r3")
CATEGORIES = ("doc", "graph", "all")
EXPECTED_CASES = {"doc": 17, "graph": 20, "all": 37}
SOURCE_GROUPS = ("existing_v2", "llm_drafted")
SOURCE_METRICS = (
    "precision", "recall", "linked_gold_recall", "mrr", "context_precision", "context_recall",
    "answer_correctness", "retrieval_latency_seconds",
)
RETRIEVAL_METRICS = (
    "recall",
    "precision",
    "mrr",
    "ndcg_at_10",
    "linked_gold_recall",
    "special_rule_hit",
    "evidence_count",
    "linked_evidence_count",
    "retrieval_latency_seconds",
    "answer_latency_seconds",
)
ANSWER_METRICS = (
    "faithfulness",
    "answer_relevancy",
    "answer_correctness",
    "context_precision",
    "context_recall",
)
METRICS = tuple(dict.fromkeys(RETRIEVAL_METRICS + ANSWER_METRICS))
PAIRED_METRICS = (
    "recall",
    "linked_gold_recall",
    "context_precision",
    "answer_correctness",
    "precision",
    "mrr",
    "ndcg_at_10",
    "faithfulness",
    "answer_relevancy",
    "context_recall",
)
COMPARISONS = (("link_all", "hybrid_rerank"), ("proposed", "hybrid_rerank"), ("proposed", "link_all"))
BOOTSTRAPS = 10_000


def _load(path: Path, source: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stem = path.stem
    variant = str(payload.get("rag_variant") or re.sub(r"_r\d+$", "", stem))
    repeat = str(payload.get("repeat_tag") or (re.search(r"r\d+$", stem) or [""])[0])
    rows = payload.get("document_cases", [])
    if not isinstance(rows, list):
        rows = []
    return {
        "path": path,
        "source": source,
        "variant": variant,
        "repeat": repeat,
        "rows": rows,
        "payload": payload,
    }


def _load_runs(notes: list[str]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in sorted(RESULTS.glob("*.json")):
        try:
            run = _load(path, "results")
        except (OSError, json.JSONDecodeError) as exc:
            notes.append(f"- Could not read `{path.relative_to(ROOT)}`: {exc}.")
            continue
        runs.append(run)
    runs.sort(key=lambda r: (r["variant"], r["repeat"]))
    expected = {(variant, repeat) for variant in VARIANTS for repeat in REPEATS}
    found = [(run["variant"], run["repeat"]) for run in runs]
    if len(found) != len(expected) or set(found) != expected:
        raise ValueError(f"Expected one result for every variant/repeat; found {found}")
    for run in runs:
        cases = [row.get("case") for row in run["rows"]]
        if len(cases) != EXPECTED_CASES["all"] or len(set(cases)) != len(cases):
            raise ValueError(f"{run['path'].name} must contain 37 unique cases")
        if not run["payload"].get("evaluation_complete") or run["payload"].get("ragas_skipped"):
            raise ValueError(f"{run['path'].name} is not a complete full evaluation")
    return runs


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _case_category(row: dict[str, Any]) -> str:
    category = row.get("category")
    return category if category in ("doc", "graph") else "doc"


def _rows_for(run: dict[str, Any], category: str) -> list[dict[str, Any]]:
    rows = run["rows"]
    if category == "all":
        return rows
    return [row for row in rows if _case_category(row) == category]


def _source_graph_cases() -> dict[str, set[str]]:
    cases = json.loads(EVAL_SET.read_text(encoding="utf-8"))["cases"]
    groups = {
        source: {case["name"] for case in cases if case["label_source"] == source and case["category"] == "graph"}
        for source in SOURCE_GROUPS
    }
    if len(cases) != 37 or {source: len(names) for source, names in groups.items()} != {"existing_v2": 5, "llm_drafted": 15}:
        raise ValueError("Unexpected eval_set_v3 graph source split")
    return groups


def _link_coverage() -> tuple[int, int]:
    count = re.search(r"approved-link query returned (\d+) rows", DATA_README.read_text(encoding="utf-8"))
    links = set(re.findall(r"Link ID: `([^`]+)`", HUMAN_CHECKLIST.read_text(encoding="utf-8")))
    if not count or not links:
        raise ValueError("Could not read the approved-link coverage from paper/data")
    return len(links), int(count.group(1))


def _source_summaries(
    runs: list[dict[str, Any]], graph_cases: dict[str, set[str]]
) -> dict[tuple[str, str, str], dict[str, Any]]:
    summaries: dict[tuple[str, str, str], dict[str, Any]] = {}
    for source, names in graph_cases.items():
        for variant in VARIANTS:
            variant_runs = [run for run in runs if run["variant"] == variant]
            case_counts = [sum(row.get("case") in names for row in run["rows"]) for run in variant_runs]
            for metric in SOURCE_METRICS:
                repeat_means = []
                for run in variant_runs:
                    values = [_number(row.get(metric)) for row in run["rows"] if row.get("case") in names]
                    present = [value for value in values if value is not None]
                    if present:
                        repeat_means.append(mean(present))
                summaries[(variant, source, metric)] = {
                    "mean": mean(repeat_means) if repeat_means else None,
                    "std": stdev(repeat_means) if len(repeat_means) > 1 else None,
                    "repeats": len(repeat_means),
                    "case_counts": case_counts,
                }
    return summaries


def _run_mean(run: dict[str, Any], category: str, metric: str) -> float | None:
    values = [_number(row.get(metric)) for row in _rows_for(run, category)]
    present = [value for value in values if value is not None]
    return mean(present) if present else None


def _metric_values(run: dict[str, Any], category: str, metric: str) -> dict[str, float]:
    return {
        str(row["case"]): value
        for row in _rows_for(run, category,)
        if row.get("case") is not None and (value := _number(row.get(metric))) is not None
    }


def _exact_wilcoxon(differences: list[float]) -> tuple[float | None, int]:
    values = [value for value in differences if abs(value) > 1e-12]
    if not values:
        return (1.0 if differences else None), 0

    ordered = sorted(enumerate(abs(value) for value in values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and math.isclose(ordered[end][1], ordered[index][1], rel_tol=0, abs_tol=1e-12):
            end += 1
        average_rank = ((index + 1) + end) / 2
        for pos in range(index, end):
            ranks[ordered[pos][0]] = average_rank
        index = end

    # Doubling ranks keeps tied average ranks integral in the exact subset-sum distribution.
    rank_twice = [round(rank * 2) for rank in ranks]
    observed = sum(rank for rank, value in zip(rank_twice, values) if value > 0)
    distribution = {0: 1}
    for rank in rank_twice:
        updated = distribution.copy()
        for total, count in distribution.items():
            updated[total + rank] = updated.get(total + rank, 0) + count
        distribution = updated
    total = 2 ** len(values)
    lower = sum(count for score, count in distribution.items() if score <= observed)
    upper = sum(count for score, count in distribution.items() if score >= observed)
    return min(1.0, 2 * min(lower, upper) / total), len(values)


def _bootstrap_ci(differences: list[float], seed: str) -> tuple[float | None, float | None]:
    if not differences:
        return None, None
    rng = random.Random(seed)
    n = len(differences)
    samples = sorted(
        mean(differences[rng.randrange(n)] for _ in range(n))
        for _ in range(BOOTSTRAPS)
    )

    def percentile(p: float) -> float:
        position = (len(samples) - 1) * p
        lower = math.floor(position)
        upper = math.ceil(position)
        return samples[lower] + (samples[upper] - samples[lower]) * (position - lower)

    return percentile(0.025), percentile(0.975)


def _summaries(runs: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    summaries: dict[tuple[str, str, str], dict[str, Any]] = {}
    for variant in VARIANTS:
        variant_runs = [run for run in runs if run["variant"] == variant]
        for category in CATEGORIES:
            case_counts = [len(_rows_for(run, category)) for run in variant_runs]
            for metric in METRICS:
                repeat_means = [
                    value
                    for run in variant_runs
                    if (value := _run_mean(run, category, metric)) is not None
                ]
                summaries[(variant, category, metric)] = {
                    "mean": mean(repeat_means) if repeat_means else None,
                    "std": stdev(repeat_means) if len(repeat_means) > 1 else None,
                    "repeats": len(repeat_means),
                    "case_counts": case_counts,
                }
    return summaries


def _format(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "—"


def _format_cell(summary: dict[str, Any]) -> str:
    value = summary["mean"]
    if value is None:
        return "—"
    sd = "—" if summary["std"] is None else f"{summary['std']:.4f}"
    return f"{value:.4f} ± {sd} (n={summary['repeats']})"


def _comparison_rows(
    runs: list[dict[str, Any]], graph_cases: dict[str, set[str]]
) -> list[dict[str, Any]]:
    by_variant = {
        variant: {run["repeat"]: run for run in runs if run["variant"] == variant}
        for variant in VARIANTS
    }
    group_cases = {"all_graph": set.union(*graph_cases.values()), **graph_cases}
    rows: list[dict[str, Any]] = []
    for source, names in group_cases.items():
        for first, second in COMPARISONS:
            for metric in PAIRED_METRICS:
                case_values: dict[str, dict[str, list[float]]] = {first: defaultdict(list), second: defaultdict(list)}
                for variant in (first, second):
                    for repeat in REPEATS:
                        run = by_variant[variant].get(repeat)
                        run_values = _metric_values(run, "graph", metric) if run else {}
                        for case, value in run_values.items():
                            if case in names:
                                case_values[variant][case].append(value)
                common = sorted(case_values[first].keys() & case_values[second].keys())
                differences = [
                    mean(case_values[first][case]) - mean(case_values[second][case])
                    for case in common
                ]
                p_value, nonzero = _exact_wilcoxon(differences)
                if len(common) > len(names):
                    raise ValueError(f"Paired comparison exceeded {source} graph case count")
                ci_lower, ci_upper = _bootstrap_ci(
                    differences, f"{source}|{first}-{second}|{metric}"
                )
                rows.append({
                    "source_group": source,
                    "comparison": f"{first} - {second}",
                    "category": "graph",
                    "metric": metric,
                    "mean_difference": mean(differences) if differences else None,
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "p_value": p_value,
                    "n": len(differences),
                    "n_nonzero": nonzero,
                })
    return rows


def _coverage_notes(runs: list[dict[str, Any]]) -> list[str]:
    lines = ["## Input coverage", ""]
    if not runs:
        lines.append("- No readable result files were found.")
        return lines
    for run in runs:
        row_counts = {cat: len(_rows_for(run, cat)) for cat in CATEGORIES}
        lines.append(
            f"- `{run['variant']} {run['repeat']}`: "
            f"doc {row_counts['doc']}/{EXPECTED_CASES['doc']}, "
            f"graph {row_counts['graph']}/{EXPECTED_CASES['graph']}, "
            f"all {row_counts['all']}/{EXPECTED_CASES['all']} "
            f"(`{run['path'].relative_to(ROOT)}`)."
        )
    return lines


def _write_markdown(
    runs: list[dict[str, Any]],
    summaries: dict[tuple[str, str, str], dict[str, Any]],
    source_summaries: dict[tuple[str, str, str], dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> None:
    lines = [
        "# Aggregated experiment results",
        "",
        "Variant metrics are means of repeat-level case means ± sample SD across r1–r3; `n` is the number "
        "of repeats. All six variants have complete 37-case runs. Unavailable case-level metrics are omitted.",
        "",
        *_coverage_notes(runs),
        "",
        "## Variant metrics",
        "",
        "| Variant | Category | Metric | Mean ± SD | Cases per repeat |",
        "|---|---|---|---:|---|",
    ]
    for variant in VARIANTS:
        for category in CATEGORIES:
            for metric in METRICS:
                item = summaries[(variant, category, metric)]
                if item["mean"] is None:
                    continue
                counts = ", ".join(str(value) for value in item["case_counts"])
                lines.append(f"| {variant} | {category} | {metric} | {_format_cell(item)} | {counts} |")

    lines += [
        "",
        "## Source-separated graph metrics",
        "",
        "`existing_v2` is development data (5 graph cases); `llm_drafted` is held-out data (15 graph cases), "
        "whose labels remain unreviewed. "
        "Metrics are averaged within each repeat and then across repeats.",
        "",
        "| Source | Variant | Metric | Mean ± SD | Cases per repeat |",
        "|---|---|---|---:|---|",
    ]
    for source in SOURCE_GROUPS:
        for variant in VARIANTS:
            for metric in SOURCE_METRICS:
                item = source_summaries[(variant, source, metric)]
                if item["mean"] is None:
                    continue
                counts = ", ".join(str(value) for value in item["case_counts"])
                lines.append(f"| {source} (graph) | {variant} | {metric} | {_format_cell(item)} | {counts} |")

    lines += [
        "",
        "## Paired case-level comparisons",
        "",
        "Each graph case is averaged over r1–r3, then paired by case name. Mean differences are first variant "
        "minus second variant; 95% CIs are percentile bootstrap intervals over cases (10,000 resamples, fixed "
        "seed), and p-values are two-sided exact Wilcoxon signed-rank tests with zero differences omitted. "
        "`n` is the number of paired cases (nonzero pairs); p-values are unadjusted exploratory results.",
        "",
        "| Source group | Comparison | Metric | Mean difference [95% CI] | p-value | n paired (nonzero) |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in comparisons:
        ci = f"[{_format(item['ci_lower'])}, {_format(item['ci_upper'])}]"
        n = f"{item['n']} ({item['n_nonzero']})"
        lines.append(
            f"| {item['source_group']} (graph) | {item['comparison']} | {item['metric']} | "
            f"{_format(item['mean_difference'])} {ci} | {_format(item['p_value'])} | {n} |"
        )
    (SUMMARY / "main_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(
    summaries: dict[tuple[str, str, str], dict[str, Any]],
    source_summaries: dict[tuple[str, str, str], dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> None:
    columns = (
        "record_type", "variant", "comparison", "source_group", "category", "metric", "mean", "std",
        "repeat_count", "case_counts", "mean_difference", "ci_lower", "ci_upper", "p_value", "n", "n_nonzero",
    )
    with (SUMMARY / "main_table.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for (variant, category, metric), item in summaries.items():
            writer.writerow({
                "record_type": "variant_metric",
                "variant": variant,
                "category": category,
                "metric": metric,
                "mean": item["mean"],
                "std": item["std"],
                "repeat_count": item["repeats"],
                "case_counts": ",".join(map(str, item["case_counts"])),
            })
        for (variant, source, metric), item in source_summaries.items():
            writer.writerow({
                "record_type": "source_metric",
                "variant": variant,
                "source_group": source,
                "category": "graph",
                "metric": metric,
                "mean": item["mean"],
                "std": item["std"],
                "repeat_count": item["repeats"],
                "case_counts": ",".join(map(str, item["case_counts"])),
            })
        for item in comparisons:
            writer.writerow({
                "record_type": "paired_comparison",
                "comparison": item["comparison"],
                "source_group": item["source_group"],
                "category": item["category"],
                "metric": item["metric"],
                "mean_difference": item["mean_difference"],
                "ci_lower": item["ci_lower"],
                "ci_upper": item["ci_upper"],
                "p_value": item["p_value"],
                "n": item["n"],
                "n_nonzero": item["n_nonzero"],
            })


def _variance_notes(summaries: dict[tuple[str, str, str], dict[str, Any]], notes: list[str]) -> None:
    for (variant, category, metric), item in summaries.items():
        if item["std"] is not None and item["std"] >= 0.10:
            notes.append(
                f"- High between-repeat variation: {variant}/{category}/{metric} "
                f"SD={item['std']:.3f} across {item['repeats']} repeats."
            )


def main() -> None:
    SUMMARY.mkdir(parents=True, exist_ok=True)
    notes = [
        "# Aggregation notes",
        "",
        "Expected input is 18 complete result JSONs: six variants × r1–r3, each with 37 cases. "
        "Between-repeat SD ≥ 0.10 is flagged below.",
        "",
    ]
    runs = _load_runs(notes)
    source_graph_cases = _source_graph_cases()
    summaries = _summaries(runs)
    source_summaries = _source_summaries(runs, source_graph_cases)
    comparisons = _comparison_rows(runs, source_graph_cases)
    assert len(comparisons) == 3 * len(COMPARISONS) * len(PAIRED_METRICS)
    assert _exact_wilcoxon([1.0, -1.0]) == (1.0, 2)
    assert _bootstrap_ci([0.25, 0.25], "self-check") == (0.25, 0.25)
    _variance_notes(summaries, notes)

    notes.append("- Source split: existing_v2 has 12 doc/5 graph cases (17 total); llm_drafted has 5 doc/15 graph cases (20 total).")
    for field, label in (
        ("llm_model", "Generation and evaluation judge model"),
        ("embedding_model", "Search embedding model"),
        ("evaluator_embedding_model", "Evaluation embedding model"),
    ):
        values = sorted({str(run["payload"].get(field)) for run in runs if run["payload"].get(field)})
        if values:
            notes.append(f"- {label}: {', '.join(f'`{value}`' for value in values)} (result metadata).")
    notes.append(
        "- Paired comparisons cover the 20 graph cases and separately report the 5-case development and "
        "15-case held-out groups. Each case is averaged over all three repeats. Bootstrap intervals are "
        "percentile intervals over cases; exact Wilcoxon p-values are unadjusted. Cases can share regulations "
        "or links, and the held-out labels remain unreviewed."
    )
    used_links, approved_links = _link_coverage()
    notes.append(f"- New graph cases cover {used_links}/{approved_links} distinct approved links, based on the human-review checklist.")
    notes += ["", *_coverage_notes(runs)]
    (SUMMARY / "notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    _write_markdown(runs, summaries, source_summaries, comparisons)
    _write_csv(summaries, source_summaries, comparisons)
    print(f"Wrote {SUMMARY / 'main_table.md'}, {SUMMARY / 'main_table.csv'}, and {SUMMARY / 'notes.md'}")


if __name__ == "__main__":
    main()
