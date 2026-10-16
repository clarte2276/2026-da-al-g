from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CHECKPOINTS = ROOT / "logs"
SUMMARY = ROOT / "summary"
EVAL_SET = ROOT.parent / "data" / "eval_set_v3.json"
DATA_README = ROOT.parent / "data" / "README.md"
HUMAN_CHECKLIST = ROOT.parent / "data" / "human_review_checklist.md"
VARIANTS = ("bm25", "dense", "hybrid", "hybrid_rerank", "link_all", "proposed")
REPEATS = ("r1", "r2", "r3")
CATEGORIES = ("doc", "graph", "all")
EXPECTED_CASES = {"doc": 17, "graph": 20, "all": 37}
SOURCE_GROUPS = ("existing_v2", "llm_drafted")
SOURCE_METRICS = ("precision", "recall", "mrr", "context_precision", "context_recall", "answer_correctness")
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
METRICS = RETRIEVAL_METRICS + ANSWER_METRICS
PAIRED_METRICS = (
    "precision",
    "recall",
    "mrr",
    "ndcg_at_10",
    "faithfulness",
    "answer_relevancy",
    "answer_correctness",
    "context_precision",
    "context_recall",
)
TODO = "TODO(실험 미완료)"


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
    candidates: list[dict[str, Any]] = []
    paths = [(p, "results") for p in sorted(RESULTS.glob("*.json"))]
    paths += [(p, "checkpoint") for p in sorted(CHECKPOINTS.glob("r*/checkpoints/link_all_r*.json"))]
    for path, source in paths:
        try:
            candidates.append(_load(path, source))
        except (OSError, json.JSONDecodeError) as exc:
            notes.append(f"- Could not read `{path.relative_to(ROOT)}`: {exc}.")

    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for run in candidates:
        key = (run["variant"], run["repeat"])
        current = selected.get(key)
        rank = (
            run["source"] == "results",
            bool(run["payload"].get("evaluation_complete")),
            len(run["rows"]),
            str(run["path"]),
        )
        if current is None:
            selected[key] = run
            continue
        current_rank = (
            current["source"] == "results",
            bool(current["payload"].get("evaluation_complete")),
            len(current["rows"]),
            str(current["path"]),
        )
        if rank > current_rank:
            notes.append(f"- `{current['path'].relative_to(ROOT)}` superseded by `{run['path'].relative_to(ROOT)}` for {key[0]} {key[1]}.")
            selected[key] = run
        else:
            notes.append(f"- `{run['path'].relative_to(ROOT)}` ignored in favor of `{current['path'].relative_to(ROOT)}` for {key[0]} {key[1]}.")
    return sorted(selected.values(), key=lambda r: (r["variant"], r["repeat"]))


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
                    "partial": any(count < len(names) for count in case_counts),
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


def _summaries(runs: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    summaries: dict[tuple[str, str, str], dict[str, Any]] = {}
    for variant in VARIANTS:
        variant_runs = [run for run in runs if run["variant"] == variant]
        for category in CATEGORIES:
            case_counts = [len(_rows_for(run, category)) for run in variant_runs]
            partial = any(count < EXPECTED_CASES[category] for count in case_counts)
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
                    "partial": partial,
                }
    return summaries


def _format(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else TODO


def _format_cell(summary: dict[str, Any]) -> str:
    value = summary["mean"]
    if value is None:
        return TODO
    sd = "—" if summary["std"] is None else f"{summary['std']:.4f}"
    return f"{value:.4f} ± {sd} (n={summary['repeats']})"


def _comparison_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_variant = {
        variant: [run for run in runs if run["variant"] == variant]
        for variant in VARIANTS
    }
    rows: list[dict[str, Any]] = []
    for comparator in ("link_all", "hybrid_rerank"):
        for category in CATEGORIES:
            for metric in PAIRED_METRICS:
                left_runs = by_variant["proposed"]
                right_runs = by_variant[comparator]
                left: dict[str, list[float]] = defaultdict(list)
                right: dict[str, list[float]] = defaultdict(list)
                for run in left_runs:
                    for case, value in _metric_values(run, category, metric).items():
                        left[case].append(value)
                for run in right_runs:
                    for case, value in _metric_values(run, category, metric).items():
                        right[case].append(value)
                common = sorted(left.keys() & right.keys())
                differences = [mean(left[case]) - mean(right[case]) for case in common]
                p_value, nonzero = _exact_wilcoxon(differences)
                rows.append({
                    "comparison": f"proposed - {comparator}",
                    "category": category,
                    "metric": metric,
                    "mean_difference": mean(differences) if differences else None,
                    "p_value": p_value,
                    "n": len(differences),
                    "n_nonzero": nonzero,
                    "partial": comparator == "link_all" and any(
                        len(_rows_for(run, category)) < EXPECTED_CASES[category] for run in right_runs
                    ),
                })
    return rows


def _coverage_notes(runs: list[dict[str, Any]], notes: list[str]) -> list[str]:
    lines = ["## Input coverage", ""]
    if not runs:
        lines.append("- No readable result files were found.")
        return lines
    for run in runs:
        row_counts = {cat: len(_rows_for(run, cat)) for cat in CATEGORIES}
        complete = run["payload"].get("evaluation_complete")
        failed = run["payload"].get("failed") or run["payload"].get("error")
        state = "failed" if failed or complete is False else (
            "full" if row_counts["all"] == EXPECTED_CASES["all"] else "partial"
        )
        extra = "; retrieval only" if run["payload"].get("ragas_skipped") else ""
        lines.append(
            f"- `{run['variant']} {run['repeat']}`: {state}, "
            f"doc {row_counts['doc']}/{EXPECTED_CASES['doc']}, "
            f"graph {row_counts['graph']}/{EXPECTED_CASES['graph']}, "
            f"all {row_counts['all']}/{EXPECTED_CASES['all']} "
            f"(`{run['path'].relative_to(ROOT)}`){extra}."
        )
    for variant in VARIANTS:
        present = {run["repeat"] for run in runs if run["variant"] == variant}
        missing = [repeat for repeat in REPEATS if repeat not in present]
        if missing:
            notes.append(f"- {variant}: missing repeat(s) {', '.join(missing)}.")
    return lines


def _write_markdown(
    runs: list[dict[str, Any]],
    summaries: dict[tuple[str, str, str], dict[str, Any]],
    source_summaries: dict[tuple[str, str, str], dict[str, Any]],
    comparisons: list[dict[str, Any]],
    notes: list[str],
) -> None:
    lines = [
        "# Aggregated experiment results",
        "",
        "Each cell is the mean of repeat-level case means ± sample SD across repeats. "
        "`n` is the number of repeats with that metric; `—` means the SD is undefined for one repeat. "
        "Partial runs remain in the summary and are identified below. Unavailable metrics are omitted; "
        "all reported p-values are unadjusted exploratory results.",
        "",
        *_coverage_notes(runs, notes),
        "",
        "## Variant metrics",
        "",
        "| Variant | Category | Metric | Mean ± SD | Cases per repeat | Partial |",
        "|---|---|---|---:|---|:---:|",
    ]
    for variant in VARIANTS:
        for category in CATEGORIES:
            for metric in METRICS:
                item = summaries[(variant, category, metric)]
                if item["mean"] is None:
                    continue
                counts = ", ".join(str(value) for value in item["case_counts"]) or "—"
                lines.append(
                    f"| {variant} | {category} | {metric} | {_format_cell(item)} | {counts} | "
                    f"{'yes' if item['partial'] else 'no'} |"
                )

    lines += [
        "",
        "## Source-separated graph metrics",
        "",
        "`existing_v2` is development data; `llm_drafted` is the 20-case new set, whose labels remain unreviewed. "
        "Metrics are averaged within each repeat and then across repeats.",
        "",
        "| Source | Variant | Metric | Mean ± SD | Cases per repeat | Partial |",
        "|---|---|---|---:|---|:---:|",
    ]
    for source in SOURCE_GROUPS:
        for variant in VARIANTS:
            for metric in SOURCE_METRICS:
                item = source_summaries[(variant, source, metric)]
                if item["mean"] is None:
                    continue
                counts = ", ".join(str(value) for value in item["case_counts"]) or "—"
                lines.append(
                    f"| {source} (graph) | {variant} | {metric} | {_format_cell(item)} | {counts} | "
                    f"{'yes' if item['partial'] else 'no'} |"
                )

    lines += [
        "",
        "## Paired case-level comparisons",
        "",
        "For each case, scores are averaged across available repeats before pairing by case name. "
        "Differences are proposed minus comparator; p-values use a two-sided exact Wilcoxon signed-rank test "
        "with zero differences omitted. `n` is the number of paired cases (the test uses nonzero pairs).",
        "",
        "| Comparison | Category | Metric | Mean difference | p-value | n paired (nonzero) | Coverage |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for item in comparisons:
        if not item["n"]:
            continue
        difference = _format(item["mean_difference"])
        p_value = _format(item["p_value"])
        n = f"{item['n']} ({item['n_nonzero']})" if item["n"] else "0"
        coverage = "partial" if item["partial"] else ("available" if item["n"] else "not run")
        lines.append(
            f"| {item['comparison']} | {item['category']} | {item['metric']} | {difference} | "
            f"{p_value} | {n} | {coverage} |"
        )
    (SUMMARY / "main_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(
    summaries: dict[tuple[str, str, str], dict[str, Any]],
    source_summaries: dict[tuple[str, str, str], dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> None:
    columns = (
        "record_type", "variant", "comparison", "source_group", "category", "metric", "mean", "std",
        "repeat_count", "case_counts", "mean_difference", "p_value", "n", "n_nonzero", "partial",
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
                "partial": item["partial"],
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
                "partial": item["partial"],
            })
        for item in comparisons:
            writer.writerow({
                "record_type": "paired_comparison",
                "comparison": item["comparison"],
                "category": item["category"],
                "metric": item["metric"],
                "mean_difference": item["mean_difference"],
                "p_value": item["p_value"],
                "n": item["n"],
                "n_nonzero": item["n_nonzero"],
                "partial": item["partial"],
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
        "Expected repeats are r1–r3; high variation is flagged at between-repeat SD ≥ 0.10. "
        "`link_all` checkpoints are partial until a complete result file for that repeat appears; "
        "a result in `results/` takes precedence over a checkpoint for the same variant and repeat.",
        "",
    ]
    runs = _load_runs(notes)
    source_graph_cases = _source_graph_cases()
    summaries = _summaries(runs)
    source_summaries = _source_summaries(runs, source_graph_cases)
    comparisons = _comparison_rows(runs)
    coverage = _coverage_notes(runs, notes)
    _variance_notes(summaries, notes)

    link_runs = [run for run in runs if run["variant"] == "link_all"]
    if link_runs:
        counts = [len(run["rows"]) for run in link_runs]
        if any(count < EXPECTED_CASES["all"] for count in counts):
            notes.append(
                f"- link_all comparison uses only case-name intersections; partial run sizes are "
                f"{', '.join(map(str, counts))}/{EXPECTED_CASES['all']} cases."
            )
    bm25_runs = [run for run in runs if run["variant"] == "bm25"]
    if any(run["payload"].get("ragas_skipped") for run in bm25_runs):
        notes.append("- BM25 has retrieval-only results; answer-generation/RAGAS metrics are unavailable.")
    if not any(run["variant"] == "proposed" for run in runs):
        notes.append("- No proposed results were found; proposed comparisons are unavailable.")
    if not any(run["variant"] == "hybrid_rerank" for run in runs):
        notes.append("- hybrid_rerank was not run; no variant or paired-comparison metrics are available.")
    notes.append("- Source split: existing_v2 has 12 doc/5 graph cases (17 total); llm_drafted has 5 doc/15 graph cases (20 total).")
    used_links, approved_links = _link_coverage()
    notes.append(f"- New graph cases cover {used_links}/{approved_links} distinct approved links, based on the human-review checklist.")
    if coverage:
        notes += ["", *coverage]
    (SUMMARY / "notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    _write_markdown(runs, summaries, source_summaries, comparisons, notes)
    _write_csv(summaries, source_summaries, comparisons)
    print(f"Wrote {SUMMARY / 'main_table.md'}, {SUMMARY / 'main_table.csv'}, and {SUMMARY / 'notes.md'}")


if __name__ == "__main__":
    main()
