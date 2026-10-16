# Aggregation notes

Expected repeats are r1–r3; high variation is flagged at between-repeat SD ≥ 0.10. `link_all` checkpoints are partial until a complete result file for that repeat appears; a result in `results/` takes precedence over a checkpoint for the same variant and repeat.

- bm25: missing repeat(s) r2, r3.
- dense: missing repeat(s) r1, r2, r3.
- hybrid: missing repeat(s) r1, r2, r3.
- hybrid_rerank: missing repeat(s) r1, r2, r3.
- High between-repeat variation: link_all/doc/evidence_count SD=0.187 across 3 repeats.
- High between-repeat variation: link_all/doc/retrieval_latency_seconds SD=0.120 across 3 repeats.
- High between-repeat variation: link_all/doc/answer_latency_seconds SD=0.132 across 3 repeats.
- High between-repeat variation: link_all/graph/evidence_count SD=0.107 across 3 repeats.
- High between-repeat variation: link_all/graph/answer_latency_seconds SD=0.195 across 3 repeats.
- High between-repeat variation: link_all/all/answer_latency_seconds SD=0.209 across 3 repeats.
- High between-repeat variation: proposed/doc/answer_latency_seconds SD=0.242 across 3 repeats.
- High between-repeat variation: proposed/graph/evidence_count SD=0.173 across 3 repeats.
- High between-repeat variation: proposed/graph/answer_latency_seconds SD=0.395 across 3 repeats.
- High between-repeat variation: proposed/all/answer_latency_seconds SD=0.186 across 3 repeats.
- link_all comparison uses only case-name intersections; partial run sizes are 31, 35, 31/37 cases.
- BM25 has retrieval-only results; answer-generation/RAGAS metrics are unavailable.
- hybrid_rerank was not run; its paired comparisons are marked TODO.

## Input coverage

- `bm25 r1`: full, doc 17/17, graph 20/20, all 37/37 (`results\bm25_r1.json`); retrieval only.
- `link_all r1`: partial, doc 12/17, graph 19/20, all 31/37 (`logs\r1\checkpoints\link_all_r1.json`).
- `link_all r2`: partial, doc 15/17, graph 20/20, all 35/37 (`logs\r2\checkpoints\link_all_r2.json`).
- `link_all r3`: partial, doc 12/17, graph 19/20, all 31/37 (`logs\r3\checkpoints\link_all_r3.json`).
- `proposed r1`: full, doc 17/17, graph 20/20, all 37/37 (`results\proposed_r1.json`).
- `proposed r2`: full, doc 17/17, graph 20/20, all 37/37 (`results\proposed_r2.json`).
- `proposed r3`: full, doc 17/17, graph 20/20, all 37/37 (`results\proposed_r3.json`).
