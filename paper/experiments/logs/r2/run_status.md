# Repeat r2 run status

Full mode includes answer generation and RAGAS. Dataset size: 37 cases, including 20 graph cases.

| Variant | Status | Cases | Wall time | Graph Recall | Graph Precision | Graph Context Precision | Graph Faithfulness | Graph Answer Correctness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| link_all | Stopped after resumed run error; graph cases complete | 35/37 (20/20 graph) | 13.9s | 0.866667 | 0.718333 | 0.868611 | 0.984244 | 0.766269 |
| hybrid_rerank | Not run after link_all error | 0/37 | 0.0s | n/a | n/a | n/a | n/a | n/a |
| hybrid | Not run after link_all error | 0/37 | 0.0s | n/a | n/a | n/a | n/a | n/a |
| dense | Not run after link_all error | 0/37 | 0.0s | n/a | n/a | n/a | n/a | n/a |
| bm25 | Not run after link_all error | 0/37 | 0.0s | n/a | n/a | n/a | n/a | n/a |

The link_all checkpoint remains under checkpoints/link_all_r2.json; it contains 35 cases. The missing cases are earthquake_control_initial_stop and earthquake_driver_speed. The resumed process exited 1 with a Python traceback after 13.9 seconds; PowerShell truncated the current stderr details. The prior r2 log records 429 insufficient_quota / credit_balance_exhausted, so all remaining runs were stopped pending coordinator direction. No final *_r2.json result was produced.