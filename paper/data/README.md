# Evaluation set v3

This folder contains the evaluation cases, a database-backed label validator, and the manual review checklist.

The per-case `needs_human_review` flags in `eval_set_v3.json` are superseded by the recorded review outcome in [human_review_record.md](human_review_record.md). The checklist records the status of each reviewed case.

## Counts

| Category | Existing v2 | Drafted | Total |
|---|---:|---:|---:|
| Document-only (`doc`) | 12 | 5 | 17 |
| Graph (`graph`) | 5 | 15 | 20 |
| **All cases** | **17** | **20** | **37** |

`existing_v2` preserves the 17 cases in `back/scripts/ragas_eval.py`: 12 direct regulation cases and five graph-required guide cases. The checked-in script contains 17 cases total, although the task brief describes 17 doc plus five graph. Five document-only cases were added from regulation articles 347, 350, 354, 355, and 356 to meet the stated `doc >= 17` acceptance count. They are marked `llm_drafted` and included in the review checklist.

## How cases were made

- Existing v2 questions and reference answers were copied from `DOCUMENT_CASES` and `REFERENCE_V2`; regulation article numbers resolve to version `35315ef6-c82f-44fd-904c-62b78bdc474a`.
- The five existing graph cases also label the guide slides/pages cited by their v2 answers. Guide pages are direct evidence (`via_link=false`); regulation articles are marked `via_link=true` only when that article is in the approved link target (for example, Article 35 in `guide_pantograph` is direct evidence).
- Fifteen new graph cases each use one distinct approved `DocumentLink`, with one guide slide and one regulation article. Questions and answers were written from the selected guide and regulation texts. Retrieval output was not used.
- The approved-link query returned 36 rows in the shared database, while the task brief expected 37. The checklist records the queries and link IDs used.

## Known limitations

The 20 `llm_drafted` cases were reviewed by one expert using the checklist; all were marked OK with no edits or deletions. This includes the five document-only cases added to reconcile the source-case count with the acceptance count. The reviewer was not blind to the link structure, and a single review provides no inter-annotator agreement measure. The 15 link-derived graph cases remain conditional on the links used to draft them, so review does not remove that sampling limitation. The database currently exposes 36 approved links, one fewer than the count in the task brief.

Run the validator from `back/` with the supplied database environment:

```bash
PYTHONPATH=. PYTHONIOENCODING=utf-8 uv run --extra dev --extra hwp python ../paper/data/validate_eval_set.py ../paper/data/eval_set_v3.json
```
