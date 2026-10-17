# Aggregation notes

Expected input is 18 complete result JSONs: six variants × r1–r3, each with 37 cases. Between-repeat SD ≥ 0.10 is flagged below.

- High between-repeat variation: bm25/doc/answer_latency_seconds SD=0.280 across 3 repeats.
- High between-repeat variation: bm25/all/answer_latency_seconds SD=0.128 across 3 repeats.
- High between-repeat variation: dense/doc/retrieval_latency_seconds SD=0.238 across 3 repeats.
- High between-repeat variation: dense/doc/answer_latency_seconds SD=0.291 across 3 repeats.
- High between-repeat variation: dense/graph/answer_latency_seconds SD=0.194 across 3 repeats.
- High between-repeat variation: dense/all/retrieval_latency_seconds SD=0.106 across 3 repeats.
- High between-repeat variation: dense/all/answer_latency_seconds SD=0.239 across 3 repeats.
- High between-repeat variation: hybrid/doc/answer_latency_seconds SD=0.173 across 3 repeats.
- High between-repeat variation: hybrid/graph/answer_latency_seconds SD=0.291 across 3 repeats.
- High between-repeat variation: hybrid/all/answer_latency_seconds SD=0.136 across 3 repeats.
- High between-repeat variation: hybrid_rerank/doc/evidence_count SD=0.122 across 3 repeats.
- High between-repeat variation: hybrid_rerank/doc/answer_latency_seconds SD=0.274 across 3 repeats.
- High between-repeat variation: hybrid_rerank/graph/answer_latency_seconds SD=0.173 across 3 repeats.
- High between-repeat variation: hybrid_rerank/all/answer_latency_seconds SD=0.179 across 3 repeats.
- High between-repeat variation: link_all/doc/evidence_count SD=0.136 across 3 repeats.
- High between-repeat variation: link_all/doc/answer_latency_seconds SD=0.134 across 3 repeats.
- High between-repeat variation: link_all/graph/retrieval_latency_seconds SD=0.388 across 3 repeats.
- High between-repeat variation: link_all/graph/answer_latency_seconds SD=0.196 across 3 repeats.
- High between-repeat variation: link_all/all/retrieval_latency_seconds SD=0.199 across 3 repeats.
- High between-repeat variation: proposed/doc/answer_latency_seconds SD=0.242 across 3 repeats.
- High between-repeat variation: proposed/graph/evidence_count SD=0.173 across 3 repeats.
- High between-repeat variation: proposed/graph/answer_latency_seconds SD=0.395 across 3 repeats.
- High between-repeat variation: proposed/all/answer_latency_seconds SD=0.186 across 3 repeats.
- Source split: existing_v2 has 12 doc/5 graph cases (17 total); llm_drafted has 5 doc/15 graph cases (20 total).
- Generation and evaluation judge model: `gpt-5.6-luna` (result metadata).
- Search embedding model: `text-embedding-3-small` (result metadata).
- Evaluation embedding model: `text-embedding-3-large` (result metadata).
- Paired comparisons cover the 20 graph cases and separately report the 5-case development and 15-case held-out groups. Each case is averaged over all three repeats. Bootstrap intervals are percentile intervals over cases; exact Wilcoxon p-values are unadjusted. Cases can share regulations or links, and the held-out labels remain unreviewed.
- New graph cases cover 15/36 distinct approved links, based on the human-review checklist.

## Input coverage

- `bm25 r1`: doc 17/17, graph 20/20, all 37/37 (`results\bm25_r1.json`).
- `bm25 r2`: doc 17/17, graph 20/20, all 37/37 (`results\bm25_r2.json`).
- `bm25 r3`: doc 17/17, graph 20/20, all 37/37 (`results\bm25_r3.json`).
- `dense r1`: doc 17/17, graph 20/20, all 37/37 (`results\dense_r1.json`).
- `dense r2`: doc 17/17, graph 20/20, all 37/37 (`results\dense_r2.json`).
- `dense r3`: doc 17/17, graph 20/20, all 37/37 (`results\dense_r3.json`).
- `hybrid r1`: doc 17/17, graph 20/20, all 37/37 (`results\hybrid_r1.json`).
- `hybrid r2`: doc 17/17, graph 20/20, all 37/37 (`results\hybrid_r2.json`).
- `hybrid r3`: doc 17/17, graph 20/20, all 37/37 (`results\hybrid_r3.json`).
- `hybrid_rerank r1`: doc 17/17, graph 20/20, all 37/37 (`results\hybrid_rerank_r1.json`).
- `hybrid_rerank r2`: doc 17/17, graph 20/20, all 37/37 (`results\hybrid_rerank_r2.json`).
- `hybrid_rerank r3`: doc 17/17, graph 20/20, all 37/37 (`results\hybrid_rerank_r3.json`).
- `link_all r1`: doc 17/17, graph 20/20, all 37/37 (`results\link_all_r1.json`).
- `link_all r2`: doc 17/17, graph 20/20, all 37/37 (`results\link_all_r2.json`).
- `link_all r3`: doc 17/17, graph 20/20, all 37/37 (`results\link_all_r3.json`).
- `proposed r1`: doc 17/17, graph 20/20, all 37/37 (`results\proposed_r1.json`).
- `proposed r2`: doc 17/17, graph 20/20, all 37/37 (`results\proposed_r2.json`).
- `proposed r3`: doc 17/17, graph 20/20, all 37/37 (`results\proposed_r3.json`).
