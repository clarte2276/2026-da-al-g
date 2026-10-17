# Repeat r2 run status

Full mode includes answer generation and RAGAS. Dataset size: 37 cases, including 20 graph cases.

| Variant | Status | Cases | Wall time | Graph Recall | Graph Precision | Graph Context Precision | Graph Faithfulness | Graph Answer Correctness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| link_all | Complete | 37/37 | 103.0s | 0.866667 | 0.718333 | 0.868611 | 0.984244 | 0.766269 |
| hybrid_rerank | Complete | 37/37 | 2166.8s | 0.575000 | 0.789167 | 0.958333 | 0.956732 | 0.757945 |
| hybrid | Complete | 37/37 | 2366.5s | 0.520833 | 0.230000 | 0.799167 | 0.971456 | 0.659194 |
| dense | Complete | 37/37 | 2202.5s | 0.383333 | 0.170000 | 0.476667 | 0.974799 | 0.656534 |
| bm25 | Complete | 37/37 | 2349.5s | 0.591667 | 0.260000 | 0.763056 | 0.969053 | 0.730918 |

All five completed result JSONs are in results/, and their checkpoints are under checkpoints/ here. link_all graph_check passed 19/20. hybrid_rerank, hybrid, dense, and bm25 graph_check passed 0/20 as expected for variants without graph expansion. Dense graph recall was nonzero in 16/20 graph cases (aggregate 0.383333); bm25 graph recall was nonzero in 19/20 (aggregate 0.591667). The first link_all command omitted the documented eval extra and failed at import; adding --extra eval allowed the resume to complete. The old 429 lines in link_all.log belong to the earlier run; the coordinator verified current API calls return 200.