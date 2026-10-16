# Retrieval experiments

Run commands from `back/`. Each run writes `ragas_results.json`, a run archive, and resumable checkpoints under its output directory. Set `OPENAI_API_KEY`, `DATABASE_URL`, and `STORAGE_ROOT` in the process environment first.

## Variants

| Variant | Retrieval path |
| --- | --- |
| `bm25` | BM25 lexical score only; no reranking or graph/link expansion. |
| `dense` | Embedding cosine score only; no reranking or graph/link expansion. |
| `hybrid` | Current 0.6 dense + 0.4 BM25 score; no reranking or graph/link expansion. |
| `hybrid_rerank` | Hybrid scoring followed by the first LLM rerank; no graph/link expansion. |
| `link_all` | Hybrid scoring and first rerank, then legacy broad expansion: direct evidence first, followed by hop and descending score, capped at `top_k × 3`; linked evidence is not reranked. |
| `proposed` | Production path: hybrid scoring, first rerank, expansion, keep all direct evidence, then rerank linked evidence (up to `top_k × 2`). This is the default. |

## Matching and metrics

A retrieved item matches a gold item when `document_version_id` is equal and either its covered regulation article equals the gold `article`, or its locator page/slide equals the gold `page`. Each gold item can count once. Ranking uses the final ordered evidence list passed to the answer model.

| Field | Definition |
| --- | --- |
| `recall` | Unique gold hits / number of gold items; null when there are no gold items. |
| `precision` | Unique gold hits / evidence count; zero when no evidence was retrieved. |
| `mrr` | Reciprocal rank of the first matching evidence item; zero when there is no hit. |
| `ndcg_at_10` | Binary-relevance DCG through rank 10, divided by ideal DCG for up to 10 gold items. |
| `linked_gold_recall` | Hits among gold items marked `via_link=true` / number of such items; null when none are marked. |
| `special_rule_hit` | For `special_rule=true`, whether any `via_link` gold item was retrieved; otherwise null. |
| `evidence_count` / `linked_evidence_count` | Final evidence count / evidence with `hop > 0` or a link ID. |
| `retrieval_latency_seconds` / `answer_latency_seconds` | Retrieval wall time / remaining answer-flow time; answer latency is null in retrieval-only runs. |
| `token_usage` | Prompt, completion, and total tokens from ChatService OpenAI responses when returned by the API. |

`retrieval_averages` reports means for `doc`, `graph`, and `all`; undefined per-case values are omitted from the mean. Existing RAGAS means remain in `averages`. Built-in cases derive article gold from `reference_articles`; a JSON dataset supplies `reference_answer` and `gold_evidence` directly.

## Run one repeat

This command runs the proposed variant for repeat `r1` using the evaluation contract. Change the variant, repeat tag, and output directory for another run.

```bash
PYTHONPATH=. PYTHONIOENCODING=utf-8 uv run --extra eval python scripts/ragas_eval.py --dataset ../paper/data/eval_set_v3.json --variant proposed --repeat-tag r1 --output-dir runtime/paper-exp/proposed-r1
```

For retrieval metrics only, add `--skip-ragas`; it skips answer generation and all judging calls.
