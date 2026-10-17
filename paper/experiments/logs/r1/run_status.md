# Repeat r1 status

Dataset: `eval_set_v3.json` (37 cases: 17 doc, 20 graph). Full mode was used (`ragas_skipped=false`) for completed variants. Wall times are measured for this dispatched work; link_all is the successful resume invocation.

| Variant | Status | Cases | Wall time | Graph Recall | Graph Precision | Graph Context Precision | Graph Faithfulness | Graph Answer Correctness | Graph checks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| link_all | complete | 37/37 | 397.1 s | 0.8417 | 0.7226 | 0.8850 | 0.9811 | 0.7254 | 18/20 |
| hybrid_rerank | complete | 37/37 | 2185.8 s | 0.5750 | 0.7392 | 0.8875 | 0.9500 | 0.7489 | 0/20 |
| hybrid | complete | 37/37 | 2358.0 s | 0.5208 | 0.2300 | 0.7008 | 0.9741 | 0.7134 | 0/20 |
| dense | complete | 37/37 | 2274.2 s | 0.3833 | 0.1700 | 0.5683 | 0.9749 | 0.6430 | 0/20 |
| bm25 | complete | 37/37 | 2309.5 s | 0.5917 | 0.2600 | 0.8171 | 0.9339 | 0.7293 | 0/20 |

`dense` completed in full mode after resuming the six-case checkpoint. Total wall time is 2,274.2 s (314.9 s in the initial partial run plus 1,959.3 s for the successful resume); all 37 cases have RAGAS metrics. The diagnostic in `diag/dense_diag.md` found a complete 4,288 x 1,536 corpus with nonzero dense scores, but dense top-10 missed both tested gold articles while hybrid ranked each exact version/article first. Article units inherit their parent chunk embedding, so neighboring articles can tie on dense score; BM25 helps hybrid separate them. This is a baseline representation limitation, not an evaluation-side matching issue. The final dense checkpoint is saved under `checkpoints/dense_r1.json`.

The previous retrieval-only `bm25_r1.json` was identical to `archives/ragas_results_bm25_retrieval_only_r1_latest.json` and was removed from `results/`; the archived copy remains. The successful link_all resume reused its 31 existing cases and completed six missing cases. An initial import attempt lacked the declared `eval` extra and made no evaluation calls. All r1 logs were scrubbed and checked for API-key patterns.
