# Aggregated experiment results

Variant metrics are means of repeat-level case means ± sample SD across r1–r3; `n` is the number of repeats. All six variants have complete 37-case runs. Unavailable case-level metrics are omitted.

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

## Variant metrics

| Variant | Category | Metric | Mean ± SD | Cases per repeat |
|---|---|---|---:|---|
| bm25 | doc | recall | 0.8431 ± 0.0170 (n=3) | 17, 17, 17 |
| bm25 | doc | precision | 0.1843 ± 0.0068 (n=3) | 17, 17, 17 |
| bm25 | doc | mrr | 0.7173 ± 0.0102 (n=3) | 17, 17, 17 |
| bm25 | doc | ndcg_at_10 | 0.7401 ± 0.0134 (n=3) | 17, 17, 17 |
| bm25 | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| bm25 | doc | evidence_count | 5.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| bm25 | doc | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| bm25 | doc | retrieval_latency_seconds | 0.3068 ± 0.0032 (n=3) | 17, 17, 17 |
| bm25 | doc | answer_latency_seconds | 4.0058 ± 0.2795 (n=3) | 17, 17, 17 |
| bm25 | doc | faithfulness | 0.9798 ± 0.0063 (n=3) | 17, 17, 17 |
| bm25 | doc | answer_relevancy | 0.8078 ± 0.0033 (n=3) | 17, 17, 17 |
| bm25 | doc | answer_correctness | 0.7432 ± 0.0070 (n=3) | 17, 17, 17 |
| bm25 | doc | context_precision | 0.7072 ± 0.0330 (n=3) | 17, 17, 17 |
| bm25 | doc | context_recall | 0.8691 ± 0.0190 (n=3) | 17, 17, 17 |
| bm25 | graph | recall | 0.5917 ± 0.0000 (n=3) | 20, 20, 20 |
| bm25 | graph | precision | 0.2600 ± 0.0000 (n=3) | 20, 20, 20 |
| bm25 | graph | mrr | 0.8767 ± 0.0000 (n=3) | 20, 20, 20 |
| bm25 | graph | ndcg_at_10 | 0.6317 ± 0.0026 (n=3) | 20, 20, 20 |
| bm25 | graph | linked_gold_recall | 0.2750 ± 0.0000 (n=3) | 20, 20, 20 |
| bm25 | graph | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| bm25 | graph | evidence_count | 5.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| bm25 | graph | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| bm25 | graph | retrieval_latency_seconds | 0.1601 ± 0.0030 (n=3) | 20, 20, 20 |
| bm25 | graph | answer_latency_seconds | 5.6218 ± 0.0109 (n=3) | 20, 20, 20 |
| bm25 | graph | faithfulness | 0.9607 ± 0.0237 (n=3) | 20, 20, 20 |
| bm25 | graph | answer_relevancy | 0.8146 ± 0.0213 (n=3) | 20, 20, 20 |
| bm25 | graph | answer_correctness | 0.7339 ± 0.0065 (n=3) | 20, 20, 20 |
| bm25 | graph | context_precision | 0.7940 ± 0.0279 (n=3) | 20, 20, 20 |
| bm25 | graph | context_recall | 0.7780 ± 0.0122 (n=3) | 20, 20, 20 |
| bm25 | all | recall | 0.7072 ± 0.0078 (n=3) | 37, 37, 37 |
| bm25 | all | precision | 0.2252 ± 0.0031 (n=3) | 37, 37, 37 |
| bm25 | all | mrr | 0.8035 ± 0.0047 (n=3) | 37, 37, 37 |
| bm25 | all | ndcg_at_10 | 0.6815 ± 0.0049 (n=3) | 37, 37, 37 |
| bm25 | all | linked_gold_recall | 0.2750 ± 0.0000 (n=3) | 37, 37, 37 |
| bm25 | all | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| bm25 | all | evidence_count | 5.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| bm25 | all | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| bm25 | all | retrieval_latency_seconds | 0.2275 ± 0.0027 (n=3) | 37, 37, 37 |
| bm25 | all | answer_latency_seconds | 4.8793 ± 0.1280 (n=3) | 37, 37, 37 |
| bm25 | all | faithfulness | 0.9695 ± 0.0151 (n=3) | 37, 37, 37 |
| bm25 | all | answer_relevancy | 0.8115 ± 0.0120 (n=3) | 37, 37, 37 |
| bm25 | all | answer_correctness | 0.7381 ± 0.0061 (n=3) | 37, 37, 37 |
| bm25 | all | context_precision | 0.7541 ± 0.0285 (n=3) | 37, 37, 37 |
| bm25 | all | context_recall | 0.8198 ± 0.0152 (n=3) | 37, 37, 37 |
| dense | doc | recall | 0.4510 ± 0.0340 (n=3) | 17, 17, 17 |
| dense | doc | precision | 0.1137 ± 0.0068 (n=3) | 17, 17, 17 |
| dense | doc | mrr | 0.2804 ± 0.0148 (n=3) | 17, 17, 17 |
| dense | doc | ndcg_at_10 | 0.3291 ± 0.0187 (n=3) | 17, 17, 17 |
| dense | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| dense | doc | evidence_count | 5.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| dense | doc | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| dense | doc | retrieval_latency_seconds | 0.6998 ± 0.2380 (n=3) | 17, 17, 17 |
| dense | doc | answer_latency_seconds | 2.8169 ± 0.2910 (n=3) | 17, 17, 17 |
| dense | doc | faithfulness | 0.9662 ± 0.0304 (n=3) | 17, 17, 17 |
| dense | doc | answer_relevancy | 0.4550 ± 0.0276 (n=3) | 17, 17, 17 |
| dense | doc | answer_correctness | 0.5143 ± 0.0148 (n=3) | 17, 17, 17 |
| dense | doc | context_precision | 0.3211 ± 0.0499 (n=3) | 17, 17, 17 |
| dense | doc | context_recall | 0.5000 ± 0.0196 (n=3) | 17, 17, 17 |
| dense | graph | recall | 0.3833 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | precision | 0.1700 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | mrr | 0.5208 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | ndcg_at_10 | 0.3506 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | linked_gold_recall | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | evidence_count | 5.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| dense | graph | retrieval_latency_seconds | 0.3453 ± 0.0170 (n=3) | 20, 20, 20 |
| dense | graph | answer_latency_seconds | 4.8923 ± 0.1942 (n=3) | 20, 20, 20 |
| dense | graph | faithfulness | 0.9778 ± 0.0050 (n=3) | 20, 20, 20 |
| dense | graph | answer_relevancy | 0.7876 ± 0.0136 (n=3) | 20, 20, 20 |
| dense | graph | answer_correctness | 0.6615 ± 0.0215 (n=3) | 20, 20, 20 |
| dense | graph | context_precision | 0.5108 ± 0.0501 (n=3) | 20, 20, 20 |
| dense | graph | context_recall | 0.6245 ± 0.0032 (n=3) | 20, 20, 20 |
| dense | all | recall | 0.4144 ± 0.0156 (n=3) | 37, 37, 37 |
| dense | all | precision | 0.1441 ± 0.0031 (n=3) | 37, 37, 37 |
| dense | all | mrr | 0.4104 ± 0.0068 (n=3) | 37, 37, 37 |
| dense | all | ndcg_at_10 | 0.3407 ± 0.0086 (n=3) | 37, 37, 37 |
| dense | all | linked_gold_recall | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| dense | all | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| dense | all | evidence_count | 5.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| dense | all | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| dense | all | retrieval_latency_seconds | 0.5082 ± 0.1056 (n=3) | 37, 37, 37 |
| dense | all | answer_latency_seconds | 3.9388 ± 0.2385 (n=3) | 37, 37, 37 |
| dense | all | faithfulness | 0.9724 ± 0.0115 (n=3) | 37, 37, 37 |
| dense | all | answer_relevancy | 0.6348 ± 0.0184 (n=3) | 37, 37, 37 |
| dense | all | answer_correctness | 0.5939 ± 0.0089 (n=3) | 37, 37, 37 |
| dense | all | context_precision | 0.4236 ± 0.0434 (n=3) | 37, 37, 37 |
| dense | all | context_recall | 0.5673 ± 0.0105 (n=3) | 37, 37, 37 |
| hybrid | doc | recall | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid | doc | precision | 0.2235 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid | doc | mrr | 0.8690 ± 0.0292 (n=3) | 17, 17, 17 |
| hybrid | doc | ndcg_at_10 | 0.9035 ± 0.0205 (n=3) | 17, 17, 17 |
| hybrid | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid | doc | evidence_count | 5.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid | doc | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid | doc | retrieval_latency_seconds | 0.5086 ± 0.0121 (n=3) | 17, 17, 17 |
| hybrid | doc | answer_latency_seconds | 3.8436 ± 0.1726 (n=3) | 17, 17, 17 |
| hybrid | doc | faithfulness | 0.9956 ± 0.0047 (n=3) | 17, 17, 17 |
| hybrid | doc | answer_relevancy | 0.8266 ± 0.0045 (n=3) | 17, 17, 17 |
| hybrid | doc | answer_correctness | 0.8249 ± 0.0309 (n=3) | 17, 17, 17 |
| hybrid | doc | context_precision | 0.8381 ± 0.0236 (n=3) | 17, 17, 17 |
| hybrid | doc | context_recall | 0.9922 ± 0.0068 (n=3) | 17, 17, 17 |
| hybrid | graph | recall | 0.5208 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid | graph | precision | 0.2300 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid | graph | mrr | 0.8394 ± 0.0170 (n=3) | 20, 20, 20 |
| hybrid | graph | ndcg_at_10 | 0.5607 ± 0.0077 (n=3) | 20, 20, 20 |
| hybrid | graph | linked_gold_recall | 0.1500 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid | graph | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid | graph | evidence_count | 5.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid | graph | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid | graph | retrieval_latency_seconds | 0.3202 ± 0.0053 (n=3) | 20, 20, 20 |
| hybrid | graph | answer_latency_seconds | 5.1591 ± 0.2914 (n=3) | 20, 20, 20 |
| hybrid | graph | faithfulness | 0.9699 ± 0.0051 (n=3) | 20, 20, 20 |
| hybrid | graph | answer_relevancy | 0.8287 ± 0.0062 (n=3) | 20, 20, 20 |
| hybrid | graph | answer_correctness | 0.6827 ± 0.0278 (n=3) | 20, 20, 20 |
| hybrid | graph | context_precision | 0.7594 ± 0.0518 (n=3) | 20, 20, 20 |
| hybrid | graph | context_recall | 0.7144 ± 0.0004 (n=3) | 20, 20, 20 |
| hybrid | all | recall | 0.7410 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid | all | precision | 0.2270 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid | all | mrr | 0.8530 ± 0.0151 (n=3) | 37, 37, 37 |
| hybrid | all | ndcg_at_10 | 0.7182 ± 0.0101 (n=3) | 37, 37, 37 |
| hybrid | all | linked_gold_recall | 0.1500 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid | all | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid | all | evidence_count | 5.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid | all | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid | all | retrieval_latency_seconds | 0.4068 ± 0.0083 (n=3) | 37, 37, 37 |
| hybrid | all | answer_latency_seconds | 4.5547 ± 0.1356 (n=3) | 37, 37, 37 |
| hybrid | all | faithfulness | 0.9817 ± 0.0049 (n=3) | 37, 37, 37 |
| hybrid | all | answer_relevancy | 0.8277 ± 0.0029 (n=3) | 37, 37, 37 |
| hybrid | all | answer_correctness | 0.7481 ± 0.0114 (n=3) | 37, 37, 37 |
| hybrid | all | context_precision | 0.7956 ± 0.0364 (n=3) | 37, 37, 37 |
| hybrid | all | context_recall | 0.8420 ± 0.0030 (n=3) | 37, 37, 37 |
| hybrid_rerank | doc | recall | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | precision | 0.6346 ± 0.0349 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | mrr | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | ndcg_at_10 | 0.9984 ± 0.0027 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | evidence_count | 2.4510 ± 0.1225 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | retrieval_latency_seconds | 1.6499 ± 0.0305 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | answer_latency_seconds | 3.7377 ± 0.2744 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | faithfulness | 0.9751 ± 0.0147 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | answer_relevancy | 0.8224 ± 0.0020 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | answer_correctness | 0.8324 ± 0.0135 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | context_precision | 0.9706 ± 0.0170 (n=3) | 17, 17, 17 |
| hybrid_rerank | doc | context_recall | 0.9933 ± 0.0061 (n=3) | 17, 17, 17 |
| hybrid_rerank | graph | recall | 0.5861 ± 0.0192 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | precision | 0.7808 ± 0.0382 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | mrr | 0.9417 ± 0.0382 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | ndcg_at_10 | 0.6487 ± 0.0205 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | linked_gold_recall | 0.2333 ± 0.0144 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | evidence_count | 2.0833 ± 0.0577 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | retrieval_latency_seconds | 1.5226 ± 0.0199 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | answer_latency_seconds | 4.9720 ± 0.1726 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | faithfulness | 0.9613 ± 0.0142 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | answer_relevancy | 0.8262 ± 0.0149 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | answer_correctness | 0.7447 ± 0.0157 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | context_precision | 0.9458 ± 0.0532 (n=3) | 20, 20, 20 |
| hybrid_rerank | graph | context_recall | 0.7848 ± 0.0158 (n=3) | 20, 20, 20 |
| hybrid_rerank | all | recall | 0.7763 ± 0.0104 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | precision | 0.7137 ± 0.0203 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | mrr | 0.9685 ± 0.0206 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | ndcg_at_10 | 0.8094 ± 0.0102 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | linked_gold_recall | 0.2333 ± 0.0144 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | evidence_count | 2.2523 ± 0.0563 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | linked_evidence_count | 0.0000 ± 0.0000 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | retrieval_latency_seconds | 1.5811 ± 0.0212 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | answer_latency_seconds | 4.4049 ± 0.1787 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | faithfulness | 0.9677 ± 0.0101 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | answer_relevancy | 0.8245 ± 0.0087 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | answer_correctness | 0.7850 ± 0.0023 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | context_precision | 0.9572 ± 0.0215 (n=3) | 37, 37, 37 |
| hybrid_rerank | all | context_recall | 0.8806 ± 0.0090 (n=3) | 37, 37, 37 |
| link_all | doc | recall | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| link_all | doc | precision | 0.6618 ± 0.0291 (n=3) | 17, 17, 17 |
| link_all | doc | mrr | 0.9118 ± 0.0170 (n=3) | 17, 17, 17 |
| link_all | doc | ndcg_at_10 | 0.9344 ± 0.0085 (n=3) | 17, 17, 17 |
| link_all | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| link_all | doc | evidence_count | 2.3922 ± 0.1358 (n=3) | 17, 17, 17 |
| link_all | doc | linked_evidence_count | 0.0588 ± 0.0000 (n=3) | 17, 17, 17 |
| link_all | doc | retrieval_latency_seconds | 1.9449 ± 0.0274 (n=3) | 17, 17, 17 |
| link_all | doc | answer_latency_seconds | 5.0061 ± 0.1338 (n=3) | 17, 17, 17 |
| link_all | doc | faithfulness | 0.9797 ± 0.0112 (n=3) | 17, 17, 17 |
| link_all | doc | answer_relevancy | 0.8201 ± 0.0124 (n=3) | 17, 17, 17 |
| link_all | doc | answer_correctness | 0.8358 ± 0.0281 (n=3) | 17, 17, 17 |
| link_all | doc | context_precision | 0.8877 ± 0.0062 (n=3) | 17, 17, 17 |
| link_all | doc | context_recall | 0.9897 ± 0.0025 (n=3) | 17, 17, 17 |
| link_all | graph | recall | 0.8500 ± 0.0144 (n=3) | 20, 20, 20 |
| link_all | graph | precision | 0.7209 ± 0.0023 (n=3) | 20, 20, 20 |
| link_all | graph | mrr | 0.9583 ± 0.0144 (n=3) | 20, 20, 20 |
| link_all | graph | ndcg_at_10 | 0.8510 ± 0.0194 (n=3) | 20, 20, 20 |
| link_all | graph | linked_gold_recall | 0.7500 ± 0.0000 (n=3) | 20, 20, 20 |
| link_all | graph | special_rule_hit | 1.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| link_all | graph | evidence_count | 3.0833 ± 0.0289 (n=3) | 20, 20, 20 |
| link_all | graph | linked_evidence_count | 1.1000 ± 0.0000 (n=3) | 20, 20, 20 |
| link_all | graph | retrieval_latency_seconds | 2.1566 ± 0.3882 (n=3) | 20, 20, 20 |
| link_all | graph | answer_latency_seconds | 7.6408 ± 0.1956 (n=3) | 20, 20, 20 |
| link_all | graph | faithfulness | 0.9814 ± 0.0028 (n=3) | 20, 20, 20 |
| link_all | graph | answer_relevancy | 0.8244 ± 0.0143 (n=3) | 20, 20, 20 |
| link_all | graph | answer_correctness | 0.7575 ± 0.0287 (n=3) | 20, 20, 20 |
| link_all | graph | context_precision | 0.8773 ± 0.0082 (n=3) | 20, 20, 20 |
| link_all | graph | context_recall | 0.9382 ± 0.0074 (n=3) | 20, 20, 20 |
| link_all | all | recall | 0.9189 ± 0.0078 (n=3) | 37, 37, 37 |
| link_all | all | precision | 0.6937 ± 0.0145 (n=3) | 37, 37, 37 |
| link_all | all | mrr | 0.9369 ± 0.0156 (n=3) | 37, 37, 37 |
| link_all | all | ndcg_at_10 | 0.8894 ± 0.0143 (n=3) | 37, 37, 37 |
| link_all | all | linked_gold_recall | 0.7500 ± 0.0000 (n=3) | 37, 37, 37 |
| link_all | all | special_rule_hit | 0.6667 ± 0.0000 (n=3) | 37, 37, 37 |
| link_all | all | evidence_count | 2.7658 ± 0.0780 (n=3) | 37, 37, 37 |
| link_all | all | linked_evidence_count | 0.6216 ± 0.0000 (n=3) | 37, 37, 37 |
| link_all | all | retrieval_latency_seconds | 2.0593 ± 0.1986 (n=3) | 37, 37, 37 |
| link_all | all | answer_latency_seconds | 6.4303 ± 0.0525 (n=3) | 37, 37, 37 |
| link_all | all | faithfulness | 0.9806 ± 0.0036 (n=3) | 37, 37, 37 |
| link_all | all | answer_relevancy | 0.8224 ± 0.0037 (n=3) | 37, 37, 37 |
| link_all | all | answer_correctness | 0.7935 ± 0.0139 (n=3) | 37, 37, 37 |
| link_all | all | context_precision | 0.8821 ± 0.0054 (n=3) | 37, 37, 37 |
| link_all | all | context_recall | 0.9619 ± 0.0050 (n=3) | 37, 37, 37 |
| proposed | doc | recall | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| proposed | doc | precision | 0.6480 ± 0.0145 (n=3) | 17, 17, 17 |
| proposed | doc | mrr | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| proposed | doc | ndcg_at_10 | 0.9969 ± 0.0027 (n=3) | 17, 17, 17 |
| proposed | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| proposed | doc | evidence_count | 2.4118 ± 0.0000 (n=3) | 17, 17, 17 |
| proposed | doc | linked_evidence_count | 0.0588 ± 0.0000 (n=3) | 17, 17, 17 |
| proposed | doc | retrieval_latency_seconds | 1.9054 ± 0.0689 (n=3) | 17, 17, 17 |
| proposed | doc | answer_latency_seconds | 4.4123 ± 0.2415 (n=3) | 17, 17, 17 |
| proposed | doc | faithfulness | 0.9838 ± 0.0146 (n=3) | 17, 17, 17 |
| proposed | doc | answer_relevancy | 0.8264 ± 0.0094 (n=3) | 17, 17, 17 |
| proposed | doc | answer_correctness | 0.8449 ± 0.0019 (n=3) | 17, 17, 17 |
| proposed | doc | context_precision | 0.9673 ± 0.0057 (n=3) | 17, 17, 17 |
| proposed | doc | context_recall | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 |
| proposed | graph | recall | 0.8389 ± 0.0459 (n=3) | 20, 20, 20 |
| proposed | graph | precision | 0.7419 ± 0.0217 (n=3) | 20, 20, 20 |
| proposed | graph | mrr | 0.9750 ± 0.0000 (n=3) | 20, 20, 20 |
| proposed | graph | ndcg_at_10 | 0.8430 ± 0.0282 (n=3) | 20, 20, 20 |
| proposed | graph | linked_gold_recall | 0.7083 ± 0.0629 (n=3) | 20, 20, 20 |
| proposed | graph | special_rule_hit | 1.0000 ± 0.0000 (n=3) | 20, 20, 20 |
| proposed | graph | evidence_count | 3.0000 ± 0.1732 (n=3) | 20, 20, 20 |
| proposed | graph | linked_evidence_count | 0.9500 ± 0.0500 (n=3) | 20, 20, 20 |
| proposed | graph | retrieval_latency_seconds | 2.6778 ± 0.0387 (n=3) | 20, 20, 20 |
| proposed | graph | answer_latency_seconds | 7.5991 ± 0.3951 (n=3) | 20, 20, 20 |
| proposed | graph | faithfulness | 0.9850 ± 0.0016 (n=3) | 20, 20, 20 |
| proposed | graph | answer_relevancy | 0.8422 ± 0.0104 (n=3) | 20, 20, 20 |
| proposed | graph | answer_correctness | 0.7558 ± 0.0120 (n=3) | 20, 20, 20 |
| proposed | graph | context_precision | 0.9233 ± 0.0334 (n=3) | 20, 20, 20 |
| proposed | graph | context_recall | 0.9163 ± 0.0109 (n=3) | 20, 20, 20 |
| proposed | all | recall | 0.9129 ± 0.0248 (n=3) | 37, 37, 37 |
| proposed | all | precision | 0.6988 ± 0.0088 (n=3) | 37, 37, 37 |
| proposed | all | mrr | 0.9865 ± 0.0000 (n=3) | 37, 37, 37 |
| proposed | all | ndcg_at_10 | 0.9137 ± 0.0156 (n=3) | 37, 37, 37 |
| proposed | all | linked_gold_recall | 0.7083 ± 0.0629 (n=3) | 37, 37, 37 |
| proposed | all | special_rule_hit | 0.6667 ± 0.0000 (n=3) | 37, 37, 37 |
| proposed | all | evidence_count | 2.7297 ± 0.0936 (n=3) | 37, 37, 37 |
| proposed | all | linked_evidence_count | 0.5405 ± 0.0270 (n=3) | 37, 37, 37 |
| proposed | all | retrieval_latency_seconds | 2.3229 ± 0.0296 (n=3) | 37, 37, 37 |
| proposed | all | answer_latency_seconds | 6.1349 ± 0.1863 (n=3) | 37, 37, 37 |
| proposed | all | faithfulness | 0.9845 ± 0.0076 (n=3) | 37, 37, 37 |
| proposed | all | answer_relevancy | 0.8349 ± 0.0035 (n=3) | 37, 37, 37 |
| proposed | all | answer_correctness | 0.7967 ± 0.0068 (n=3) | 37, 37, 37 |
| proposed | all | context_precision | 0.9435 ± 0.0188 (n=3) | 37, 37, 37 |
| proposed | all | context_recall | 0.9547 ± 0.0059 (n=3) | 37, 37, 37 |

## Source-separated graph metrics

`existing_v2` is development data (5 graph cases); `llm_drafted` is held-out data (15 graph cases), whose labels remain unreviewed. Metrics are averaged within each repeat and then across repeats.

| Source | Variant | Metric | Mean ± SD | Cases per repeat |
|---|---|---|---:|---|
| existing_v2 (graph) | bm25 | precision | 0.2400 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | bm25 | recall | 0.3667 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | bm25 | linked_gold_recall | 0.1000 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | bm25 | mrr | 0.5067 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | bm25 | context_precision | 0.5067 ± 0.0601 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | bm25 | context_recall | 0.6735 ± 0.0106 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | bm25 | answer_correctness | 0.6710 ± 0.0343 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | bm25 | retrieval_latency_seconds | 0.1561 ± 0.0018 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | precision | 0.1600 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | recall | 0.2333 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | linked_gold_recall | 0.0000 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | mrr | 0.4500 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | context_precision | 0.3000 ± 0.1641 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | context_recall | 0.4564 ± 0.0149 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | answer_correctness | 0.5642 ± 0.0940 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | dense | retrieval_latency_seconds | 0.3185 ± 0.0154 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | precision | 0.2000 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | recall | 0.2833 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | linked_gold_recall | 0.0000 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | mrr | 0.5133 ± 0.0058 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | context_precision | 0.4089 ± 0.0975 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | context_recall | 0.5277 ± 0.0130 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | answer_correctness | 0.5521 ± 0.0286 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid | retrieval_latency_seconds | 0.3093 ± 0.0108 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | precision | 0.5456 ± 0.0694 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | recall | 0.4778 ± 0.0385 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | linked_gold_recall | 0.0667 ± 0.0577 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | mrr | 1.0000 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | context_precision | 0.9167 ± 0.0601 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | context_recall | 0.7469 ± 0.0114 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | answer_correctness | 0.7381 ± 0.0159 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | hybrid_rerank | retrieval_latency_seconds | 1.5329 ± 0.0456 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | precision | 0.6190 ± 0.0545 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | recall | 0.6667 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | linked_gold_recall | 0.4000 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | mrr | 0.8667 ± 0.0577 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | context_precision | 0.6811 ± 0.0647 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | context_recall | 0.8845 ± 0.0211 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | answer_correctness | 0.7418 ± 0.0202 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | link_all | retrieval_latency_seconds | 1.7409 ± 0.1461 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | precision | 0.5689 ± 0.0385 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | recall | 0.6889 ± 0.0385 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | linked_gold_recall | 0.4333 ± 0.0577 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | mrr | 1.0000 ± 0.0000 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | context_precision | 0.7896 ± 0.0737 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | context_recall | 0.8335 ± 0.0189 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | answer_correctness | 0.7392 ± 0.0259 (n=3) | 5, 5, 5 |
| existing_v2 (graph) | proposed | retrieval_latency_seconds | 2.7981 ± 0.1380 (n=3) | 5, 5, 5 |
| llm_drafted (graph) | bm25 | precision | 0.2667 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | bm25 | recall | 0.6667 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | bm25 | linked_gold_recall | 0.3333 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | bm25 | mrr | 1.0000 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | bm25 | context_precision | 0.8898 ± 0.0217 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | bm25 | context_recall | 0.8128 ± 0.0139 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | bm25 | answer_correctness | 0.7548 ± 0.0033 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | bm25 | retrieval_latency_seconds | 0.1615 ± 0.0035 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | precision | 0.1733 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | recall | 0.4333 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | linked_gold_recall | 0.0000 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | mrr | 0.5444 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | context_precision | 0.5811 ± 0.0150 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | context_recall | 0.6806 ± 0.0058 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | answer_correctness | 0.6940 ± 0.0045 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | dense | retrieval_latency_seconds | 0.3542 ± 0.0241 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | precision | 0.2400 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | recall | 0.6000 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | linked_gold_recall | 0.2000 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | mrr | 0.9481 ± 0.0231 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | context_precision | 0.8763 ± 0.0390 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | context_recall | 0.7766 ± 0.0045 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | answer_correctness | 0.7262 ± 0.0288 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid | retrieval_latency_seconds | 0.3239 ± 0.0035 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | precision | 0.8593 ± 0.0321 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | recall | 0.6222 ± 0.0385 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | linked_gold_recall | 0.2889 ± 0.0385 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | mrr | 0.9222 ± 0.0509 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | context_precision | 0.9556 ± 0.0509 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | context_recall | 0.7974 ± 0.0221 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | answer_correctness | 0.7470 ± 0.0260 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | hybrid_rerank | retrieval_latency_seconds | 1.5191 ± 0.0414 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | precision | 0.7548 ± 0.0206 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | recall | 0.9111 ± 0.0192 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | linked_gold_recall | 0.8667 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | mrr | 0.9889 ± 0.0192 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | context_precision | 0.9427 ± 0.0314 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | context_recall | 0.9561 ± 0.0123 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | answer_correctness | 0.7628 ± 0.0319 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | link_all | retrieval_latency_seconds | 2.2952 ± 0.4964 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | precision | 0.7996 ± 0.0172 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | recall | 0.8889 ± 0.0509 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | linked_gold_recall | 0.8000 ± 0.0667 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | mrr | 0.9667 ± 0.0000 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | context_precision | 0.9679 ± 0.0204 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | context_recall | 0.9438 ± 0.0205 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | answer_correctness | 0.7613 ± 0.0096 (n=3) | 15, 15, 15 |
| llm_drafted (graph) | proposed | retrieval_latency_seconds | 2.6378 ± 0.0305 (n=3) | 15, 15, 15 |

## Paired case-level comparisons

Each graph case is averaged over r1–r3, then paired by case name. Mean differences are first variant minus second variant; 95% CIs are percentile bootstrap intervals over cases (10,000 resamples, fixed seed), and p-values are two-sided exact Wilcoxon signed-rank tests with zero differences omitted. `n` is the number of paired cases (nonzero pairs); p-values are unadjusted exploratory results.

| Source group | Comparison | Metric | Mean difference [95% CI] | p-value | n paired (nonzero) |
|---|---|---|---:|---:|---:|
| all_graph (graph) | link_all - hybrid_rerank | recall | 0.2639 [0.1583, 0.3667] | 0.0004 | 20 (14) |
| all_graph (graph) | link_all - hybrid_rerank | linked_gold_recall | 0.5167 [0.3083, 0.7167] | 0.0005 | 20 (12) |
| all_graph (graph) | link_all - hybrid_rerank | context_precision | -0.0685 [-0.1358, -0.0036] | 0.0771 | 20 (13) |
| all_graph (graph) | link_all - hybrid_rerank | answer_correctness | 0.0128 [-0.0299, 0.0696] | 0.7841 | 20 (20) |
| all_graph (graph) | link_all - hybrid_rerank | precision | -0.0600 [-0.1730, 0.0614] | 0.2375 | 20 (13) |
| all_graph (graph) | link_all - hybrid_rerank | mrr | 0.0167 [-0.0667, 0.0917] | 0.8125 | 20 (5) |
| all_graph (graph) | link_all - hybrid_rerank | ndcg_at_10 | 0.2023 [0.1131, 0.2880] | 0.0008 | 20 (16) |
| all_graph (graph) | link_all - hybrid_rerank | faithfulness | 0.0200 [-0.0089, 0.0561] | 0.6221 | 20 (12) |
| all_graph (graph) | link_all - hybrid_rerank | answer_relevancy | -0.0019 [-0.0176, 0.0136] | 0.7841 | 20 (20) |
| all_graph (graph) | link_all - hybrid_rerank | context_recall | 0.1534 [0.0805, 0.2325] | 0.0009 | 20 (15) |
| all_graph (graph) | proposed - hybrid_rerank | recall | 0.2528 [0.1611, 0.3444] | 0.0002 | 20 (13) |
| all_graph (graph) | proposed - hybrid_rerank | linked_gold_recall | 0.4750 [0.2833, 0.6667] | 0.0005 | 20 (12) |
| all_graph (graph) | proposed - hybrid_rerank | context_precision | -0.0225 [-0.0748, 0.0310] | 0.7737 | 20 (13) |
| all_graph (graph) | proposed - hybrid_rerank | answer_correctness | 0.0111 [-0.0343, 0.0710] | 0.5958 | 20 (20) |
| all_graph (graph) | proposed - hybrid_rerank | precision | -0.0389 [-0.1408, 0.0633] | 0.4238 | 20 (11) |
| all_graph (graph) | proposed - hybrid_rerank | mrr | 0.0333 [0.0000, 0.0833] | 0.5000 | 20 (2) |
| all_graph (graph) | proposed - hybrid_rerank | ndcg_at_10 | 0.1943 [0.1204, 0.2675] | 0.0002 | 20 (15) |
| all_graph (graph) | proposed - hybrid_rerank | faithfulness | 0.0237 [-0.0061, 0.0605] | 0.5317 | 20 (12) |
| all_graph (graph) | proposed - hybrid_rerank | answer_relevancy | 0.0160 [0.0022, 0.0303] | 0.0897 | 20 (20) |
| all_graph (graph) | proposed - hybrid_rerank | context_recall | 0.1315 [0.0630, 0.2053] | 0.0006 | 20 (14) |
| all_graph (graph) | proposed - link_all | recall | -0.0111 [-0.0583, 0.0250] | 0.7500 | 20 (4) |
| all_graph (graph) | proposed - link_all | linked_gold_recall | -0.0417 [-0.1167, 0.0167] | 0.5000 | 20 (3) |
| all_graph (graph) | proposed - link_all | context_precision | 0.0460 [0.0094, 0.0891] | 0.0673 | 20 (14) |
| all_graph (graph) | proposed - link_all | answer_correctness | -0.0017 [-0.0219, 0.0212] | 0.6215 | 20 (20) |
| all_graph (graph) | proposed - link_all | precision | 0.0211 [-0.0365, 0.0924] | 0.9844 | 20 (11) |
| all_graph (graph) | proposed - link_all | mrr | 0.0167 [-0.0417, 0.0833] | 0.7500 | 20 (3) |
| all_graph (graph) | proposed - link_all | ndcg_at_10 | -0.0080 [-0.0474, 0.0288] | 0.7822 | 20 (11) |
| all_graph (graph) | proposed - link_all | faithfulness | 0.0037 [-0.0003, 0.0081] | 0.1309 | 20 (10) |
| all_graph (graph) | proposed - link_all | answer_relevancy | 0.0178 [0.0061, 0.0315] | 0.0073 | 20 (20) |
| all_graph (graph) | proposed - link_all | context_recall | -0.0220 [-0.0619, 0.0091] | 0.3828 | 20 (8) |
| existing_v2 (graph) | link_all - hybrid_rerank | recall | 0.1889 [0.0722, 0.2833] | 0.1250 | 5 (4) |
| existing_v2 (graph) | link_all - hybrid_rerank | linked_gold_recall | 0.3333 [0.0333, 0.7000] | 0.2500 | 5 (3) |
| existing_v2 (graph) | link_all - hybrid_rerank | context_precision | -0.2356 [-0.3189, -0.1522] | 0.0625 | 5 (5) |
| existing_v2 (graph) | link_all - hybrid_rerank | answer_correctness | 0.0037 [-0.0385, 0.0459] | 1.0000 | 5 (5) |
| existing_v2 (graph) | link_all - hybrid_rerank | precision | 0.0735 [-0.0667, 0.1924] | 0.3750 | 5 (4) |
| existing_v2 (graph) | link_all - hybrid_rerank | mrr | -0.1333 [-0.3333, 0.0000] | 0.5000 | 5 (2) |
| existing_v2 (graph) | link_all - hybrid_rerank | ndcg_at_10 | 0.0796 [-0.0547, 0.1640] | 0.6250 | 5 (5) |
| existing_v2 (graph) | link_all - hybrid_rerank | faithfulness | -0.0014 [-0.0042, 0.0000] | 1.0000 | 5 (1) |
| existing_v2 (graph) | link_all - hybrid_rerank | answer_relevancy | 0.0028 [-0.0283, 0.0432] | 0.8125 | 5 (5) |
| existing_v2 (graph) | link_all - hybrid_rerank | context_recall | 0.1376 [0.0160, 0.2593] | 0.2500 | 5 (4) |
| existing_v2 (graph) | proposed - hybrid_rerank | recall | 0.2111 [0.1000, 0.2944] | 0.1250 | 5 (4) |
| existing_v2 (graph) | proposed - hybrid_rerank | linked_gold_recall | 0.3667 [0.0667, 0.7000] | 0.2500 | 5 (3) |
| existing_v2 (graph) | proposed - hybrid_rerank | context_precision | -0.1270 [-0.2489, -0.0052] | 0.3125 | 5 (5) |
| existing_v2 (graph) | proposed - hybrid_rerank | answer_correctness | 0.0011 [-0.0535, 0.0786] | 0.6250 | 5 (5) |
| existing_v2 (graph) | proposed - hybrid_rerank | precision | 0.0233 [-0.1000, 0.1178] | 0.8750 | 5 (4) |
| existing_v2 (graph) | proposed - hybrid_rerank | mrr | 0.0000 [0.0000, 0.0000] | 1.0000 | 5 (0) |
| existing_v2 (graph) | proposed - hybrid_rerank | ndcg_at_10 | 0.1322 [0.0510, 0.1940] | 0.1250 | 5 (5) |
| existing_v2 (graph) | proposed - hybrid_rerank | faithfulness | -0.0053 [-0.0113, 0.0000] | 0.5000 | 5 (2) |
| existing_v2 (graph) | proposed - hybrid_rerank | answer_relevancy | 0.0095 [-0.0151, 0.0487] | 0.8125 | 5 (5) |
| existing_v2 (graph) | proposed - hybrid_rerank | context_recall | 0.0867 [0.0054, 0.1811] | 0.2500 | 5 (4) |
| existing_v2 (graph) | proposed - link_all | recall | 0.0222 [0.0000, 0.0667] | 1.0000 | 5 (1) |
| existing_v2 (graph) | proposed - link_all | linked_gold_recall | 0.0333 [0.0000, 0.1000] | 1.0000 | 5 (1) |
| existing_v2 (graph) | proposed - link_all | context_precision | 0.1085 [0.0022, 0.2200] | 0.3125 | 5 (5) |
| existing_v2 (graph) | proposed - link_all | answer_correctness | -0.0026 [-0.0399, 0.0417] | 0.8125 | 5 (5) |
| existing_v2 (graph) | proposed - link_all | precision | -0.0502 [-0.0968, -0.0092] | 0.1250 | 5 (4) |
| existing_v2 (graph) | proposed - link_all | mrr | 0.1333 [0.0000, 0.3333] | 0.5000 | 5 (2) |
| existing_v2 (graph) | proposed - link_all | ndcg_at_10 | 0.0526 [0.0009, 0.1123] | 0.3125 | 5 (5) |
| existing_v2 (graph) | proposed - link_all | faithfulness | -0.0039 [-0.0099, 0.0000] | 0.5000 | 5 (2) |
| existing_v2 (graph) | proposed - link_all | answer_relevancy | 0.0067 [-0.0059, 0.0180] | 0.4375 | 5 (5) |
| existing_v2 (graph) | proposed - link_all | context_recall | -0.0510 [-0.1276, -0.0049] | 0.1250 | 5 (4) |
| llm_drafted (graph) | link_all - hybrid_rerank | recall | 0.2889 [0.1556, 0.4222] | 0.0039 | 15 (10) |
| llm_drafted (graph) | link_all - hybrid_rerank | linked_gold_recall | 0.5778 [0.3333, 0.8000] | 0.0039 | 15 (9) |
| llm_drafted (graph) | link_all - hybrid_rerank | context_precision | -0.0128 [-0.0737, 0.0484] | 1.0000 | 15 (8) |
| llm_drafted (graph) | link_all - hybrid_rerank | answer_correctness | 0.0158 [-0.0374, 0.0894] | 0.8040 | 15 (15) |
| llm_drafted (graph) | link_all - hybrid_rerank | precision | -0.1044 [-0.2370, 0.0444] | 0.1562 | 15 (9) |
| llm_drafted (graph) | link_all - hybrid_rerank | mrr | 0.0667 [0.0000, 0.1333] | 0.2500 | 15 (3) |
| llm_drafted (graph) | link_all - hybrid_rerank | ndcg_at_10 | 0.2432 [0.1368, 0.3408] | 0.0020 | 15 (11) |
| llm_drafted (graph) | link_all - hybrid_rerank | faithfulness | 0.0272 [-0.0115, 0.0739] | 0.5195 | 15 (11) |
| llm_drafted (graph) | link_all - hybrid_rerank | answer_relevancy | -0.0034 [-0.0209, 0.0127] | 0.8469 | 15 (15) |
| llm_drafted (graph) | link_all - hybrid_rerank | context_recall | 0.1587 [0.0690, 0.2519] | 0.0049 | 15 (11) |
| llm_drafted (graph) | proposed - hybrid_rerank | recall | 0.2667 [0.1444, 0.3778] | 0.0039 | 15 (9) |
| llm_drafted (graph) | proposed - hybrid_rerank | linked_gold_recall | 0.5111 [0.2889, 0.7333] | 0.0039 | 15 (9) |
| llm_drafted (graph) | proposed - hybrid_rerank | context_precision | 0.0123 [-0.0210, 0.0667] | 0.5312 | 15 (8) |
| llm_drafted (graph) | proposed - hybrid_rerank | answer_correctness | 0.0144 [-0.0408, 0.0891] | 0.7197 | 15 (15) |
| llm_drafted (graph) | proposed - hybrid_rerank | precision | -0.0596 [-0.1852, 0.0737] | 0.5156 | 15 (7) |
| llm_drafted (graph) | proposed - hybrid_rerank | mrr | 0.0444 [0.0000, 0.1111] | 0.5000 | 15 (2) |
| llm_drafted (graph) | proposed - hybrid_rerank | ndcg_at_10 | 0.2150 [0.1216, 0.3060] | 0.0039 | 15 (10) |
| llm_drafted (graph) | proposed - hybrid_rerank | faithfulness | 0.0333 [-0.0053, 0.0806] | 0.3340 | 15 (10) |
| llm_drafted (graph) | proposed - hybrid_rerank | answer_relevancy | 0.0181 [0.0033, 0.0322] | 0.0554 | 15 (15) |
| llm_drafted (graph) | proposed - hybrid_rerank | context_recall | 0.1464 [0.0638, 0.2402] | 0.0039 | 15 (10) |
| llm_drafted (graph) | proposed - link_all | recall | -0.0222 [-0.0778, 0.0222] | 0.7500 | 15 (3) |
| llm_drafted (graph) | proposed - link_all | linked_gold_recall | -0.0667 [-0.1778, 0.0000] | 0.5000 | 15 (2) |
| llm_drafted (graph) | proposed - link_all | context_precision | 0.0252 [-0.0019, 0.0606] | 0.1289 | 15 (9) |
| llm_drafted (graph) | proposed - link_all | answer_correctness | -0.0014 [-0.0248, 0.0250] | 0.7197 | 15 (15) |
| llm_drafted (graph) | proposed - link_all | precision | 0.0448 [-0.0296, 0.1363] | 0.5000 | 15 (7) |
| llm_drafted (graph) | proposed - link_all | mrr | -0.0222 [-0.0667, 0.0000] | 1.0000 | 15 (1) |
| llm_drafted (graph) | proposed - link_all | ndcg_at_10 | -0.0282 [-0.0736, 0.0112] | 0.2500 | 15 (6) |
| llm_drafted (graph) | proposed - link_all | faithfulness | 0.0062 [0.0020, 0.0113] | 0.0156 | 15 (8) |
| llm_drafted (graph) | proposed - link_all | answer_relevancy | 0.0216 [0.0068, 0.0391] | 0.0125 | 15 (15) |
| llm_drafted (graph) | proposed - link_all | context_recall | -0.0123 [-0.0603, 0.0205] | 1.0000 | 15 (4) |
