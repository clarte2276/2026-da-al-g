"""Validate eval_set_v3.json against the read-only fragment database."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path


CASE_FIELDS = {
    "name", "question", "category", "reference_answer", "gold_evidence",
    "special_rule", "label_source", "needs_human_review",
}
EVIDENCE_FIELDS = {"document_version_id", "article", "page", "label", "via_link"}


def validate(path: Path) -> tuple[int, dict[str, int]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load eval set: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"version", "cases"}:
        raise ValueError("top level must contain exactly 'version' and 'cases'")
    if not isinstance(data["version"], str) or not data["version"]:
        raise ValueError("version must be a non-empty string")
    if not isinstance(data["cases"], list):
        raise ValueError("cases must be a list")

    errors: list[str] = []
    names: set[str] = set()
    questions: set[str] = set()
    counts = {"doc": 0, "graph": 0}
    evidence_rows: list[tuple[int, dict]] = []
    for index, case in enumerate(data["cases"], 1):
        where = f"case {index}"
        if not isinstance(case, dict) or set(case) != CASE_FIELDS:
            errors.append(f"{where}: fields must be exactly {sorted(CASE_FIELDS)}")
            continue
        for field in ("name", "question", "reference_answer"):
            if not isinstance(case[field], str) or not case[field].strip():
                errors.append(f"{where}: {field} must be a non-empty string")
        if isinstance(case["name"], str):
            if case["name"] in names:
                errors.append(f"{where}: duplicate name {case['name']!r}")
            names.add(case["name"])
        if isinstance(case["question"], str):
            normalized = " ".join(case["question"].split())
            if normalized in questions:
                errors.append(f"{where}: duplicate question {case['question']!r}")
            questions.add(normalized)
        if not isinstance(case["category"], str) or case["category"] not in counts:
            errors.append(f"{where}: category must be 'doc' or 'graph'")
        else:
            counts[case["category"]] += 1
        if not isinstance(case["special_rule"], bool):
            errors.append(f"{where}: special_rule must be boolean")
        if not isinstance(case["label_source"], str) or case["label_source"] not in {"existing_v2", "llm_drafted"}:
            errors.append(f"{where}: invalid label_source")
        if not isinstance(case["needs_human_review"], bool):
            errors.append(f"{where}: needs_human_review must be boolean")
        if case["label_source"] == "llm_drafted" and case["needs_human_review"] is not True:
            errors.append(f"{where}: llm_drafted cases must need human review")
        gold = case["gold_evidence"]
        if not isinstance(gold, list) or not gold:
            errors.append(f"{where}: gold_evidence must be a non-empty list")
            continue
        versions: set[str] = set()
        has_direct = has_linked = False
        for evidence_index, item in enumerate(gold, 1):
            loc = f"{where} gold_evidence[{evidence_index}]"
            if not isinstance(item, dict) or set(item) != EVIDENCE_FIELDS:
                errors.append(f"{loc}: fields must be exactly {sorted(EVIDENCE_FIELDS)}")
                continue
            version_id = item["document_version_id"]
            if not isinstance(version_id, str) or not version_id.strip():
                errors.append(f"{loc}: document_version_id must be a non-empty string")
                continue
            versions.add(version_id)
            article, page = item["article"], item["page"]
            if (article is None) == (page is None):
                errors.append(f"{loc}: exactly one of article or page must be set")
            if article is not None and (not isinstance(article, int) or isinstance(article, bool) or article < 1):
                errors.append(f"{loc}: article must be a positive integer or null")
            if page is not None and (not isinstance(page, int) or isinstance(page, bool) or page < 1):
                errors.append(f"{loc}: page must be a positive integer or null")
            if not isinstance(item["label"], str) or not item["label"].strip():
                errors.append(f"{loc}: label must be a non-empty string")
            if not isinstance(item["via_link"], bool):
                errors.append(f"{loc}: via_link must be boolean")
            has_linked |= item["via_link"] is True
            has_direct |= item["via_link"] is False
            evidence_rows.append((index, item))
        if case["category"] == "graph" and (len(versions) < 2 or not has_direct or not has_linked):
            errors.append(f"{where}: graph cases need direct and via-link evidence from both documents")

    if errors:
        raise ValueError("\n".join(errors))
    if counts["doc"] < 17 or counts["graph"] < 20:
        raise ValueError(f"case counts below acceptance: doc={counts['doc']} graph={counts['graph']}")

    database_url = os.environ.get("DATABASE_URL", "")
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("DATABASE_URL must be a SQLite URL loaded into the environment")
    database_path = Path(database_url.removeprefix(prefix)).resolve()
    if not database_path.is_file():
        raise ValueError(f"database file does not exist: {database_path}")

    connection = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = ON")
    try:
        versions = {item["document_version_id"] for _, item in evidence_rows}
        fragments: dict[str, list[tuple[str, dict]]] = {}
        for version_id in versions:
            rows = connection.execute(
                "SELECT text, locator_json FROM fragments WHERE version_id = ?",
                (version_id,),
            ).fetchall()
            parsed = []
            for text, locator_json in rows:
                try:
                    locator = json.loads(locator_json or "{}")
                except json.JSONDecodeError:
                    locator = {}
                parsed.append((text or "", locator if isinstance(locator, dict) else {}))
            fragments[version_id] = parsed

        for case_index, item in evidence_rows:
            version_id = item["document_version_id"]
            available = fragments.get(version_id, [])
            if item["article"] is not None:
                article = item["article"]
                pattern = re.compile(rf"(?<!\d)제\s*{article}\s*조(?!\d)")
                resolved = any(pattern.search(text) for text, _ in available)
                description = f"article {article} text"
            else:
                page = item["page"]
                resolved = any(
                    locator.get("page", locator.get("slide")) == page
                    or str(locator.get("page", locator.get("slide"))) == str(page)
                    for _, locator in available
                )
                description = f"page/slide {page} locator"
            if not resolved:
                errors.append(
                    f"case {case_index} ({data['cases'][case_index - 1]['name']}): "
                    f"{description} did not resolve in document_version_id {version_id}"
                )
    finally:
        connection.close()
    if errors:
        raise ValueError("\n".join(errors))
    return len(data["cases"]), counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("eval_set", type=Path, help="path to eval_set_v3.json")
    args = parser.parse_args()
    try:
        total, counts = validate(args.eval_set)
    except (ValueError, sqlite3.Error) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    data = json.loads(args.eval_set.read_text(encoding="utf-8"))
    drafted = sum(case["label_source"] == "llm_drafted" for case in data["cases"])
    print(f"eval_set={data['version']} total={total} doc={counts['doc']} graph={counts['graph']} llm_drafted={drafted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
