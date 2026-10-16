# Aggregated experiment results

Each cell is the mean of repeat-level case means ± sample SD across repeats. `n` is the number of repeats with that metric; `—` means the SD is undefined for one repeat. Partial runs remain in the summary and are identified below.

## Input coverage

- `bm25 r1`: full, doc 17/17, graph 20/20, all 37/37 (`results\bm25_r1.json`); retrieval only.
- `link_all r1`: partial, doc 12/17, graph 19/20, all 31/37 (`logs\r1\checkpoints\link_all_r1.json`).
- `link_all r2`: partial, doc 15/17, graph 20/20, all 35/37 (`logs\r2\checkpoints\link_all_r2.json`).
- `link_all r3`: partial, doc 12/17, graph 19/20, all 31/37 (`logs\r3\checkpoints\link_all_r3.json`).
- `proposed r1`: full, doc 17/17, graph 20/20, all 37/37 (`results\proposed_r1.json`).
- `proposed r2`: full, doc 17/17, graph 20/20, all 37/37 (`results\proposed_r2.json`).
- `proposed r3`: full, doc 17/17, graph 20/20, all 37/37 (`results\proposed_r3.json`).

## Variant metrics

| Variant | Category | Metric | Mean ± SD | Cases per repeat | Partial |
|---|---|---|---:|---|:---:|
| bm25 | doc | recall | 0.8235 ± — (n=1) | 17 | no |
| bm25 | doc | precision | 0.1765 ± — (n=1) | 17 | no |
| bm25 | doc | mrr | 0.7500 ± — (n=1) | 17 | no |
| bm25 | doc | ndcg_at_10 | 0.7611 ± — (n=1) | 17 | no |
| bm25 | doc | linked_gold_recall | TODO(실험 미완료) | 17 | no |
| bm25 | doc | special_rule_hit | 0.0000 ± — (n=1) | 17 | no |
| bm25 | doc | evidence_count | 5.0000 ± — (n=1) | 17 | no |
| bm25 | doc | linked_evidence_count | 0.0000 ± — (n=1) | 17 | no |
| bm25 | doc | retrieval_latency_seconds | 0.2929 ± — (n=1) | 17 | no |
| bm25 | doc | answer_latency_seconds | TODO(실험 미완료) | 17 | no |
| bm25 | doc | faithfulness | TODO(실험 미완료) | 17 | no |
| bm25 | doc | answer_relevancy | TODO(실험 미완료) | 17 | no |
| bm25 | doc | answer_correctness | TODO(실험 미완료) | 17 | no |
| bm25 | doc | context_precision | TODO(실험 미완료) | 17 | no |
| bm25 | doc | context_recall | TODO(실험 미완료) | 17 | no |
| bm25 | graph | recall | 0.5750 ± — (n=1) | 20 | no |
| bm25 | graph | precision | 0.2500 ± — (n=1) | 20 | no |
| bm25 | graph | mrr | 0.8167 ± — (n=1) | 20 | no |
| bm25 | graph | ndcg_at_10 | 0.6031 ± — (n=1) | 20 | no |
| bm25 | graph | linked_gold_recall | 0.2750 ± — (n=1) | 20 | no |
| bm25 | graph | special_rule_hit | 0.0000 ± — (n=1) | 20 | no |
| bm25 | graph | evidence_count | 5.0000 ± — (n=1) | 20 | no |
| bm25 | graph | linked_evidence_count | 0.0000 ± — (n=1) | 20 | no |
| bm25 | graph | retrieval_latency_seconds | 0.1521 ± — (n=1) | 20 | no |
| bm25 | graph | answer_latency_seconds | TODO(실험 미완료) | 20 | no |
| bm25 | graph | faithfulness | TODO(실험 미완료) | 20 | no |
| bm25 | graph | answer_relevancy | TODO(실험 미완료) | 20 | no |
| bm25 | graph | answer_correctness | TODO(실험 미완료) | 20 | no |
| bm25 | graph | context_precision | TODO(실험 미완료) | 20 | no |
| bm25 | graph | context_recall | TODO(실험 미완료) | 20 | no |
| bm25 | all | recall | 0.6892 ± — (n=1) | 37 | no |
| bm25 | all | precision | 0.2162 ± — (n=1) | 37 | no |
| bm25 | all | mrr | 0.7860 ± — (n=1) | 37 | no |
| bm25 | all | ndcg_at_10 | 0.6757 ± — (n=1) | 37 | no |
| bm25 | all | linked_gold_recall | 0.2750 ± — (n=1) | 37 | no |
| bm25 | all | special_rule_hit | 0.0000 ± — (n=1) | 37 | no |
| bm25 | all | evidence_count | 5.0000 ± — (n=1) | 37 | no |
| bm25 | all | linked_evidence_count | 0.0000 ± — (n=1) | 37 | no |
| bm25 | all | retrieval_latency_seconds | 0.2168 ± — (n=1) | 37 | no |
| bm25 | all | answer_latency_seconds | TODO(실험 미완료) | 37 | no |
| bm25 | all | faithfulness | TODO(실험 미완료) | 37 | no |
| bm25 | all | answer_relevancy | TODO(실험 미완료) | 37 | no |
| bm25 | all | answer_correctness | TODO(실험 미완료) | 37 | no |
| bm25 | all | context_precision | TODO(실험 미완료) | 37 | no |
| bm25 | all | context_recall | TODO(실험 미완료) | 37 | no |
| dense | doc | recall | TODO(실험 미완료) | — | no |
| dense | doc | precision | TODO(실험 미완료) | — | no |
| dense | doc | mrr | TODO(실험 미완료) | — | no |
| dense | doc | ndcg_at_10 | TODO(실험 미완료) | — | no |
| dense | doc | linked_gold_recall | TODO(실험 미완료) | — | no |
| dense | doc | special_rule_hit | TODO(실험 미완료) | — | no |
| dense | doc | evidence_count | TODO(실험 미완료) | — | no |
| dense | doc | linked_evidence_count | TODO(실험 미완료) | — | no |
| dense | doc | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| dense | doc | answer_latency_seconds | TODO(실험 미완료) | — | no |
| dense | doc | faithfulness | TODO(실험 미완료) | — | no |
| dense | doc | answer_relevancy | TODO(실험 미완료) | — | no |
| dense | doc | answer_correctness | TODO(실험 미완료) | — | no |
| dense | doc | context_precision | TODO(실험 미완료) | — | no |
| dense | doc | context_recall | TODO(실험 미완료) | — | no |
| dense | graph | recall | TODO(실험 미완료) | — | no |
| dense | graph | precision | TODO(실험 미완료) | — | no |
| dense | graph | mrr | TODO(실험 미완료) | — | no |
| dense | graph | ndcg_at_10 | TODO(실험 미완료) | — | no |
| dense | graph | linked_gold_recall | TODO(실험 미완료) | — | no |
| dense | graph | special_rule_hit | TODO(실험 미완료) | — | no |
| dense | graph | evidence_count | TODO(실험 미완료) | — | no |
| dense | graph | linked_evidence_count | TODO(실험 미완료) | — | no |
| dense | graph | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| dense | graph | answer_latency_seconds | TODO(실험 미완료) | — | no |
| dense | graph | faithfulness | TODO(실험 미완료) | — | no |
| dense | graph | answer_relevancy | TODO(실험 미완료) | — | no |
| dense | graph | answer_correctness | TODO(실험 미완료) | — | no |
| dense | graph | context_precision | TODO(실험 미완료) | — | no |
| dense | graph | context_recall | TODO(실험 미완료) | — | no |
| dense | all | recall | TODO(실험 미완료) | — | no |
| dense | all | precision | TODO(실험 미완료) | — | no |
| dense | all | mrr | TODO(실험 미완료) | — | no |
| dense | all | ndcg_at_10 | TODO(실험 미완료) | — | no |
| dense | all | linked_gold_recall | TODO(실험 미완료) | — | no |
| dense | all | special_rule_hit | TODO(실험 미완료) | — | no |
| dense | all | evidence_count | TODO(실험 미완료) | — | no |
| dense | all | linked_evidence_count | TODO(실험 미완료) | — | no |
| dense | all | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| dense | all | answer_latency_seconds | TODO(실험 미완료) | — | no |
| dense | all | faithfulness | TODO(실험 미완료) | — | no |
| dense | all | answer_relevancy | TODO(실험 미완료) | — | no |
| dense | all | answer_correctness | TODO(실험 미완료) | — | no |
| dense | all | context_precision | TODO(실험 미완료) | — | no |
| dense | all | context_recall | TODO(실험 미완료) | — | no |
| hybrid | doc | recall | TODO(실험 미완료) | — | no |
| hybrid | doc | precision | TODO(실험 미완료) | — | no |
| hybrid | doc | mrr | TODO(실험 미완료) | — | no |
| hybrid | doc | ndcg_at_10 | TODO(실험 미완료) | — | no |
| hybrid | doc | linked_gold_recall | TODO(실험 미완료) | — | no |
| hybrid | doc | special_rule_hit | TODO(실험 미완료) | — | no |
| hybrid | doc | evidence_count | TODO(실험 미완료) | — | no |
| hybrid | doc | linked_evidence_count | TODO(실험 미완료) | — | no |
| hybrid | doc | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid | doc | answer_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid | doc | faithfulness | TODO(실험 미완료) | — | no |
| hybrid | doc | answer_relevancy | TODO(실험 미완료) | — | no |
| hybrid | doc | answer_correctness | TODO(실험 미완료) | — | no |
| hybrid | doc | context_precision | TODO(실험 미완료) | — | no |
| hybrid | doc | context_recall | TODO(실험 미완료) | — | no |
| hybrid | graph | recall | TODO(실험 미완료) | — | no |
| hybrid | graph | precision | TODO(실험 미완료) | — | no |
| hybrid | graph | mrr | TODO(실험 미완료) | — | no |
| hybrid | graph | ndcg_at_10 | TODO(실험 미완료) | — | no |
| hybrid | graph | linked_gold_recall | TODO(실험 미완료) | — | no |
| hybrid | graph | special_rule_hit | TODO(실험 미완료) | — | no |
| hybrid | graph | evidence_count | TODO(실험 미완료) | — | no |
| hybrid | graph | linked_evidence_count | TODO(실험 미완료) | — | no |
| hybrid | graph | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid | graph | answer_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid | graph | faithfulness | TODO(실험 미완료) | — | no |
| hybrid | graph | answer_relevancy | TODO(실험 미완료) | — | no |
| hybrid | graph | answer_correctness | TODO(실험 미완료) | — | no |
| hybrid | graph | context_precision | TODO(실험 미완료) | — | no |
| hybrid | graph | context_recall | TODO(실험 미완료) | — | no |
| hybrid | all | recall | TODO(실험 미완료) | — | no |
| hybrid | all | precision | TODO(실험 미완료) | — | no |
| hybrid | all | mrr | TODO(실험 미완료) | — | no |
| hybrid | all | ndcg_at_10 | TODO(실험 미완료) | — | no |
| hybrid | all | linked_gold_recall | TODO(실험 미완료) | — | no |
| hybrid | all | special_rule_hit | TODO(실험 미완료) | — | no |
| hybrid | all | evidence_count | TODO(실험 미완료) | — | no |
| hybrid | all | linked_evidence_count | TODO(실험 미완료) | — | no |
| hybrid | all | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid | all | answer_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid | all | faithfulness | TODO(실험 미완료) | — | no |
| hybrid | all | answer_relevancy | TODO(실험 미완료) | — | no |
| hybrid | all | answer_correctness | TODO(실험 미완료) | — | no |
| hybrid | all | context_precision | TODO(실험 미완료) | — | no |
| hybrid | all | context_recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | precision | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | mrr | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | ndcg_at_10 | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | linked_gold_recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | special_rule_hit | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | evidence_count | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | linked_evidence_count | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | answer_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | faithfulness | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | answer_relevancy | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | answer_correctness | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | context_precision | TODO(실험 미완료) | — | no |
| hybrid_rerank | doc | context_recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | precision | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | mrr | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | ndcg_at_10 | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | linked_gold_recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | special_rule_hit | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | evidence_count | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | linked_evidence_count | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | answer_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | faithfulness | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | answer_relevancy | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | answer_correctness | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | context_precision | TODO(실험 미완료) | — | no |
| hybrid_rerank | graph | context_recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | precision | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | mrr | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | ndcg_at_10 | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | linked_gold_recall | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | special_rule_hit | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | evidence_count | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | linked_evidence_count | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | retrieval_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | answer_latency_seconds | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | faithfulness | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | answer_relevancy | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | answer_correctness | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | context_precision | TODO(실험 미완료) | — | no |
| hybrid_rerank | all | context_recall | TODO(실험 미완료) | — | no |
| link_all | doc | recall | 1.0000 ± 0.0000 (n=3) | 12, 15, 12 | yes |
| link_all | doc | precision | 0.6119 ± 0.0148 (n=3) | 12, 15, 12 | yes |
| link_all | doc | mrr | 0.9204 ± 0.0305 (n=3) | 12, 15, 12 | yes |
| link_all | doc | ndcg_at_10 | 0.9411 ± 0.0176 (n=3) | 12, 15, 12 | yes |
| link_all | doc | linked_gold_recall | TODO(실험 미완료) | 12, 15, 12 | yes |
| link_all | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 12, 15, 12 | yes |
| link_all | doc | evidence_count | 2.6278 ± 0.1873 (n=3) | 12, 15, 12 | yes |
| link_all | doc | linked_evidence_count | 0.0778 ± 0.0096 (n=3) | 12, 15, 12 | yes |
| link_all | doc | retrieval_latency_seconds | 1.9895 ± 0.1197 (n=3) | 12, 15, 12 | yes |
| link_all | doc | answer_latency_seconds | 5.4472 ± 0.1316 (n=3) | 12, 15, 12 | yes |
| link_all | doc | faithfulness | 0.9742 ± 0.0113 (n=3) | 12, 15, 12 | yes |
| link_all | doc | answer_relevancy | 0.8214 ± 0.0064 (n=3) | 12, 15, 12 | yes |
| link_all | doc | answer_correctness | 0.8316 ± 0.0351 (n=3) | 12, 15, 12 | yes |
| link_all | doc | context_precision | 0.8902 ± 0.0183 (n=3) | 12, 15, 12 | yes |
| link_all | doc | context_recall | 0.9861 ± 0.0048 (n=3) | 12, 15, 12 | yes |
| link_all | graph | recall | 0.8532 ± 0.0176 (n=3) | 19, 20, 19 | yes |
| link_all | graph | precision | 0.7374 ± 0.0170 (n=3) | 19, 20, 19 | yes |
| link_all | graph | mrr | 0.9654 ± 0.0156 (n=3) | 19, 20, 19 | yes |
| link_all | graph | ndcg_at_10 | 0.8562 ± 0.0204 (n=3) | 19, 20, 19 | yes |
| link_all | graph | linked_gold_recall | 0.7412 ± 0.0076 (n=3) | 19, 20, 19 | yes |
| link_all | graph | special_rule_hit | 1.0000 ± 0.0000 (n=3) | 19, 20, 19 | yes |
| link_all | graph | evidence_count | 2.9807 ± 0.1066 (n=3) | 19, 20, 19 | yes |
| link_all | graph | linked_evidence_count | 1.0684 ± 0.0273 (n=3) | 19, 20, 19 | yes |
| link_all | graph | retrieval_latency_seconds | 1.7030 ± 0.0425 (n=3) | 19, 20, 19 | yes |
| link_all | graph | answer_latency_seconds | 7.6406 ± 0.1954 (n=3) | 19, 20, 19 | yes |
| link_all | graph | faithfulness | 0.9812 ± 0.0034 (n=3) | 19, 20, 19 | yes |
| link_all | graph | answer_relevancy | 0.8249 ± 0.0144 (n=3) | 19, 20, 19 | yes |
| link_all | graph | answer_correctness | 0.7603 ± 0.0293 (n=3) | 19, 20, 19 | yes |
| link_all | graph | context_precision | 0.8834 ± 0.0132 (n=3) | 19, 20, 19 | yes |
| link_all | graph | context_recall | 0.9359 ± 0.0093 (n=3) | 19, 20, 19 | yes |
| link_all | all | recall | 0.9119 ± 0.0131 (n=3) | 31, 35, 31 | yes |
| link_all | all | precision | 0.6876 ± 0.0073 (n=3) | 31, 35, 31 | yes |
| link_all | all | mrr | 0.9477 ± 0.0183 (n=3) | 31, 35, 31 | yes |
| link_all | all | ndcg_at_10 | 0.8903 ± 0.0202 (n=3) | 31, 35, 31 | yes |
| link_all | all | linked_gold_recall | 0.7412 ± 0.0076 (n=3) | 31, 35, 31 | yes |
| link_all | all | special_rule_hit | 0.6667 ± 0.0000 (n=3) | 31, 35, 31 | yes |
| link_all | all | evidence_count | 2.8353 ± 0.0648 (n=3) | 31, 35, 31 | yes |
| link_all | all | linked_evidence_count | 0.6707 ± 0.0117 (n=3) | 31, 35, 31 | yes |
| link_all | all | retrieval_latency_seconds | 1.8159 ± 0.0542 (n=3) | 31, 35, 31 | yes |
| link_all | all | answer_latency_seconds | 6.7627 ± 0.2095 (n=3) | 31, 35, 31 | yes |
| link_all | all | faithfulness | 0.9782 ± 0.0027 (n=3) | 31, 35, 31 | yes |
| link_all | all | answer_relevancy | 0.8238 ± 0.0061 (n=3) | 31, 35, 31 | yes |
| link_all | all | answer_correctness | 0.7883 ± 0.0207 (n=3) | 31, 35, 31 | yes |
| link_all | all | context_precision | 0.8866 ± 0.0014 (n=3) | 31, 35, 31 | yes |
| link_all | all | context_recall | 0.9560 ± 0.0084 (n=3) | 31, 35, 31 | yes |
| proposed | doc | recall | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 | no |
| proposed | doc | precision | 0.6480 ± 0.0145 (n=3) | 17, 17, 17 | no |
| proposed | doc | mrr | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 | no |
| proposed | doc | ndcg_at_10 | 0.9969 ± 0.0027 (n=3) | 17, 17, 17 | no |
| proposed | doc | linked_gold_recall | TODO(실험 미완료) | 17, 17, 17 | no |
| proposed | doc | special_rule_hit | 0.0000 ± 0.0000 (n=3) | 17, 17, 17 | no |
| proposed | doc | evidence_count | 2.4118 ± 0.0000 (n=3) | 17, 17, 17 | no |
| proposed | doc | linked_evidence_count | 0.0588 ± 0.0000 (n=3) | 17, 17, 17 | no |
| proposed | doc | retrieval_latency_seconds | 1.9054 ± 0.0689 (n=3) | 17, 17, 17 | no |
| proposed | doc | answer_latency_seconds | 4.4123 ± 0.2415 (n=3) | 17, 17, 17 | no |
| proposed | doc | faithfulness | 0.9838 ± 0.0146 (n=3) | 17, 17, 17 | no |
| proposed | doc | answer_relevancy | 0.8264 ± 0.0094 (n=3) | 17, 17, 17 | no |
| proposed | doc | answer_correctness | 0.8449 ± 0.0019 (n=3) | 17, 17, 17 | no |
| proposed | doc | context_precision | 0.9673 ± 0.0057 (n=3) | 17, 17, 17 | no |
| proposed | doc | context_recall | 1.0000 ± 0.0000 (n=3) | 17, 17, 17 | no |
| proposed | graph | recall | 0.8389 ± 0.0459 (n=3) | 20, 20, 20 | no |
| proposed | graph | precision | 0.7419 ± 0.0217 (n=3) | 20, 20, 20 | no |
| proposed | graph | mrr | 0.9750 ± 0.0000 (n=3) | 20, 20, 20 | no |
| proposed | graph | ndcg_at_10 | 0.8430 ± 0.0282 (n=3) | 20, 20, 20 | no |
| proposed | graph | linked_gold_recall | 0.7083 ± 0.0629 (n=3) | 20, 20, 20 | no |
| proposed | graph | special_rule_hit | 1.0000 ± 0.0000 (n=3) | 20, 20, 20 | no |
| proposed | graph | evidence_count | 3.0000 ± 0.1732 (n=3) | 20, 20, 20 | no |
| proposed | graph | linked_evidence_count | 0.9500 ± 0.0500 (n=3) | 20, 20, 20 | no |
| proposed | graph | retrieval_latency_seconds | 2.6778 ± 0.0387 (n=3) | 20, 20, 20 | no |
| proposed | graph | answer_latency_seconds | 7.5991 ± 0.3951 (n=3) | 20, 20, 20 | no |
| proposed | graph | faithfulness | 0.9850 ± 0.0016 (n=3) | 20, 20, 20 | no |
| proposed | graph | answer_relevancy | 0.8422 ± 0.0104 (n=3) | 20, 20, 20 | no |
| proposed | graph | answer_correctness | 0.7558 ± 0.0120 (n=3) | 20, 20, 20 | no |
| proposed | graph | context_precision | 0.9233 ± 0.0334 (n=3) | 20, 20, 20 | no |
| proposed | graph | context_recall | 0.9163 ± 0.0109 (n=3) | 20, 20, 20 | no |
| proposed | all | recall | 0.9129 ± 0.0248 (n=3) | 37, 37, 37 | no |
| proposed | all | precision | 0.6988 ± 0.0088 (n=3) | 37, 37, 37 | no |
| proposed | all | mrr | 0.9865 ± 0.0000 (n=3) | 37, 37, 37 | no |
| proposed | all | ndcg_at_10 | 0.9137 ± 0.0156 (n=3) | 37, 37, 37 | no |
| proposed | all | linked_gold_recall | 0.7083 ± 0.0629 (n=3) | 37, 37, 37 | no |
| proposed | all | special_rule_hit | 0.6667 ± 0.0000 (n=3) | 37, 37, 37 | no |
| proposed | all | evidence_count | 2.7297 ± 0.0936 (n=3) | 37, 37, 37 | no |
| proposed | all | linked_evidence_count | 0.5405 ± 0.0270 (n=3) | 37, 37, 37 | no |
| proposed | all | retrieval_latency_seconds | 2.3229 ± 0.0296 (n=3) | 37, 37, 37 | no |
| proposed | all | answer_latency_seconds | 6.1349 ± 0.1863 (n=3) | 37, 37, 37 | no |
| proposed | all | faithfulness | 0.9845 ± 0.0076 (n=3) | 37, 37, 37 | no |
| proposed | all | answer_relevancy | 0.8349 ± 0.0035 (n=3) | 37, 37, 37 | no |
| proposed | all | answer_correctness | 0.7967 ± 0.0068 (n=3) | 37, 37, 37 | no |
| proposed | all | context_precision | 0.9435 ± 0.0188 (n=3) | 37, 37, 37 | no |
| proposed | all | context_recall | 0.9547 ± 0.0059 (n=3) | 37, 37, 37 | no |

## Paired case-level comparisons

For each case, scores are averaged across available repeats before pairing by case name. Differences are proposed minus comparator; p-values use a two-sided exact Wilcoxon signed-rank test with zero differences omitted. `n` is the number of paired cases (the test uses nonzero pairs).

| Comparison | Category | Metric | Mean difference | p-value | n paired (nonzero) | Coverage |
|---|---|---|---:|---:|---:|---|
| proposed - link_all | doc | precision | 0.0085 | 0.8750 | 15 (7) | partial |
| proposed - link_all | doc | recall | 0.0000 | 1.0000 | 15 (0) | partial |
| proposed - link_all | doc | mrr | 0.0667 | 0.5000 | 15 (2) | partial |
| proposed - link_all | doc | ndcg_at_10 | 0.0461 | 0.5000 | 15 (3) | partial |
| proposed - link_all | doc | faithfulness | 0.0047 | 1.0000 | 15 (7) | partial |
| proposed - link_all | doc | answer_relevancy | 0.0032 | 0.5614 | 15 (15) | partial |
| proposed - link_all | doc | answer_correctness | 0.0084 | 0.8040 | 15 (15) | partial |
| proposed - link_all | doc | context_precision | 0.0569 | 0.0625 | 15 (6) | partial |
| proposed - link_all | doc | context_recall | 0.0117 | 1.0000 | 15 (1) | partial |
| proposed - link_all | graph | precision | 0.0183 | 0.8496 | 20 (11) | partial |
| proposed - link_all | graph | recall | -0.0194 | 0.5000 | 20 (5) | partial |
| proposed - link_all | graph | mrr | 0.0083 | 1.0000 | 20 (3) | partial |
| proposed - link_all | graph | ndcg_at_10 | -0.0182 | 0.7822 | 20 (11) | partial |
| proposed - link_all | graph | faithfulness | 0.0031 | 0.2031 | 20 (9) | partial |
| proposed - link_all | graph | answer_relevancy | 0.0152 | 0.0362 | 20 (20) | partial |
| proposed - link_all | graph | answer_correctness | -0.0041 | 0.4980 | 20 (20) | partial |
| proposed - link_all | graph | context_precision | 0.0444 | 0.0673 | 20 (14) | partial |
| proposed - link_all | graph | context_recall | -0.0220 | 0.3828 | 20 (8) | partial |
| proposed - link_all | all | precision | 0.0141 | 0.7096 | 35 (18) | partial |
| proposed - link_all | all | recall | -0.0111 | 0.5000 | 35 (5) | partial |
| proposed - link_all | all | mrr | 0.0333 | 0.3750 | 35 (5) | partial |
| proposed - link_all | all | ndcg_at_10 | 0.0094 | 0.7269 | 35 (14) | partial |
| proposed - link_all | all | faithfulness | 0.0038 | 0.4407 | 35 (16) | partial |
| proposed - link_all | all | answer_relevancy | 0.0100 | 0.0625 | 35 (35) | partial |
| proposed - link_all | all | answer_correctness | 0.0013 | 0.9549 | 35 (35) | partial |
| proposed - link_all | all | context_precision | 0.0497 | 0.0047 | 35 (20) | partial |
| proposed - link_all | all | context_recall | -0.0075 | 0.6523 | 35 (9) | partial |
| proposed - hybrid_rerank | doc | precision | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | recall | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | mrr | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | ndcg_at_10 | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | faithfulness | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | answer_relevancy | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | answer_correctness | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | context_precision | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | doc | context_recall | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | precision | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | recall | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | mrr | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | ndcg_at_10 | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | faithfulness | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | answer_relevancy | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | answer_correctness | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | context_precision | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | graph | context_recall | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | precision | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | recall | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | mrr | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | ndcg_at_10 | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | faithfulness | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | answer_relevancy | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | answer_correctness | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | context_precision | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
| proposed - hybrid_rerank | all | context_recall | TODO(실험 미완료) | TODO(실험 미완료) | 0 | not run |
