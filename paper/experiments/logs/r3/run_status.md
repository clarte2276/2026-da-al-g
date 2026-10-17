# Repeat r3 status

## Completed full evaluations

All five requested variants completed the generation, retrieval, and RAGAS evaluation in full mode. Each result has 37/37 dataset cases, 20 graph cases with all listed metrics scored, and `ragas_skipped=false`. Link_all resumed from its saved 31/37 checkpoint; the other four variants ran fresh.

| Variant | Graph Recall | Graph Precision | Context Precision | Faithfulness | Answer Correctness | Wall time (s) | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| link_all | 0.8417 | 0.7217 | 0.8783 | 0.9787 | 0.7809 | 393.1 | `results/link_all_r3.json` |
| hybrid_rerank | 0.6083 | 0.8142 | 0.9917 | 0.9773 | 0.7273 | 2150.2 | `results/hybrid_rerank_r3.json` |
| hybrid | 0.5208 | 0.2300 | 0.7783 | 0.9642 | 0.6755 | 2335.8 | `results/hybrid_r3.json` |
| dense | 0.3833 | 0.1700 | 0.4875 | 0.9836 | 0.6851 | 2361.9 | `results/dense_r3.json` |
| bm25 | 0.5917 | 0.2600 | 0.8019 | 0.9791 | 0.7413 | 2333.4 | `results/bm25_r3.json` |

Logs and checkpoints are under `logs/r3/` and `logs/r3/checkpoints/`. The earlier partial `link_all_r3` checkpoint was resumed successfully. Low dense retrieval recall is expected: article units inherit parent chunk embeddings, so dense-only retrieval can tie within a chunk.

## Existing proposed result

`proposed_r3` remains as its separate full 37-case result: graph Recall 0.8417, Precision 0.7658, Context Precision 0.9153, Faithfulness 0.9832, Answer Correctness 0.7525; wall time 2686.7 seconds.
