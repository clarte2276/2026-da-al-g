# Aggregated experiment results

Each cell is the mean of repeat-level case means ± sample SD across repeats. `n` is the number of repeats with that metric; `—` means the SD is undefined for one repeat. Partial runs remain in the summary and are identified below. Unavailable metrics are omitted; all reported p-values are unadjusted exploratory results.

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
| bm25 | doc | special_rule_hit | 0.0000 ± — (n=1) | 17 | no |
| bm25 | doc | evidence_count | 5.0000 ± — (n=1) | 17 | no |
| bm25 | doc | linked_evidence_count | 0.0000 ± — (n=1) | 17 | no |
| bm25 | doc | retrieval_latency_seconds | 0.2929 ± — (n=1) | 17 | no |
| bm25 | graph | recall | 0.5750 ± — (n=1) | 20 | no |
| bm25 | graph | precision | 0.2500 ± — (n=1) | 20 | no |
| bm25 | graph | mrr | 0.8167 ± — (n=1) | 20 | no |
| bm25 | graph | ndcg_at_10 | 0.6031 ± — (n=1) | 20 | no |
| bm25 | graph | linked_gold_recall | 0.2750 ± — (n=1) | 20 | no |
| bm25 | graph | special_rule_hit | 0.0000 ± — (n=1) | 20 | no |
| bm25 | graph | evidence_count | 5.0000 ± — (n=1) | 20 | no |
| bm25 | graph | linked_evidence_count | 0.0000 ± — (n=1) | 20 | no |
| bm25 | graph | retrieval_latency_seconds | 0.1521 ± — (n=1) | 20 | no |
| bm25 | all | recall | 0.6892 ± — (n=1) | 37 | no |
| bm25 | all | precision | 0.2162 ± — (n=1) | 37 | no |
| bm25 | all | mrr | 0.7860 ± — (n=1) | 37 | no |
| bm25 | all | ndcg_at_10 | 0.6757 ± — (n=1) | 37 | no |
| bm25 | all | linked_gold_recall | 0.2750 ± — (n=1) | 37 | no |
| bm25 | all | special_rule_hit | 0.0000 ± — (n=1) | 37 | no |
| bm25 | all | evidence_count | 5.0000 ± — (n=1) | 37 | no |
| bm25 | all | linked_evidence_count | 0.0000 ± — (n=1) | 37 | no |
| bm25 | all | retrieval_latency_seconds | 0.2168 ± — (n=1) | 37 | no |
| link_all | doc | recall | 1.0000 ± 0.0000 (n=3) | 12, 15, 12 | yes |
| link_all | doc | precision | 0.6119 ± 0.0148 (n=3) | 12, 15, 12 | yes |
| link_all | doc | mrr | 0.9204 ± 0.0305 (n=3) | 12, 15, 12 | yes |
| link_all | doc | ndcg_at_10 | 0.9411 ± 0.0176 (n=3) | 12, 15, 12 | yes |
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

## Source-separated graph metrics

`existing_v2` is development data; `llm_drafted` is the 20-case new set, whose labels remain unreviewed. Metrics are averaged within each repeat and then across repeats.

| Source | Variant | Metric | Mean ± SD | Cases per repeat | Partial |
|---|---|---|---:|---|:---:|
| existing_v2 (graph) | bm25 | precision | 0.2000 ± — (n=1) | 5 | no |
| existing_v2 (graph) | bm25 | recall | 0.3000 ± — (n=1) | 5 | no |
| existing_v2 (graph) | bm25 | mrr | 0.4667 ± — (n=1) | 5 | no |
| existing_v2 (graph) | bm25 | retrieval_latency_seconds | 0.1490 ± — (n=1) | 5 | no |
| existing_v2 (graph) | link_all | precision | 0.6190 ± 0.0545 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | link_all | recall | 0.6667 ± 0.0000 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | link_all | mrr | 0.8667 ± 0.0577 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | link_all | context_precision | 0.6811 ± 0.0647 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | link_all | context_recall | 0.8845 ± 0.0211 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | link_all | answer_correctness | 0.7418 ± 0.0202 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | link_all | retrieval_latency_seconds | 1.7409 ± 0.1461 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | proposed | precision | 0.5689 ± 0.0385 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | proposed | recall | 0.6889 ± 0.0385 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | proposed | mrr | 1.0000 ± 0.0000 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | proposed | context_precision | 0.7896 ± 0.0737 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | proposed | context_recall | 0.8335 ± 0.0189 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | proposed | answer_correctness | 0.7392 ± 0.0259 (n=3) | 5, 5, 5 | no |
| existing_v2 (graph) | proposed | retrieval_latency_seconds | 2.7981 ± 0.1380 (n=3) | 5, 5, 5 | no |
| llm_drafted (graph) | bm25 | precision | 0.2667 ± — (n=1) | 15 | no |
| llm_drafted (graph) | bm25 | recall | 0.6667 ± — (n=1) | 15 | no |
| llm_drafted (graph) | bm25 | mrr | 0.9333 ± — (n=1) | 15 | no |
| llm_drafted (graph) | bm25 | retrieval_latency_seconds | 0.1531 ± — (n=1) | 15 | no |
| llm_drafted (graph) | link_all | precision | 0.7793 ± 0.0372 (n=3) | 14, 15, 14 | yes |
| llm_drafted (graph) | link_all | recall | 0.9183 ± 0.0221 (n=3) | 14, 15, 14 | yes |
| llm_drafted (graph) | link_all | mrr | 1.0000 ± 0.0000 (n=3) | 14, 15, 14 | yes |
| llm_drafted (graph) | link_all | context_precision | 0.9545 ± 0.0357 (n=3) | 14, 15, 14 | yes |
| llm_drafted (graph) | link_all | context_recall | 0.9539 ± 0.0139 (n=3) | 14, 15, 14 | yes |
| llm_drafted (graph) | link_all | answer_correctness | 0.7668 ± 0.0327 (n=3) | 14, 15, 14 | yes |
| llm_drafted (graph) | link_all | retrieval_latency_seconds | 1.6891 ± 0.0298 (n=3) | 14, 15, 14 | yes |
| llm_drafted (graph) | proposed | precision | 0.7996 ± 0.0172 (n=3) | 15, 15, 15 | no |
| llm_drafted (graph) | proposed | recall | 0.8889 ± 0.0509 (n=3) | 15, 15, 15 | no |
| llm_drafted (graph) | proposed | mrr | 0.9667 ± 0.0000 (n=3) | 15, 15, 15 | no |
| llm_drafted (graph) | proposed | context_precision | 0.9679 ± 0.0204 (n=3) | 15, 15, 15 | no |
| llm_drafted (graph) | proposed | context_recall | 0.9438 ± 0.0205 (n=3) | 15, 15, 15 | no |
| llm_drafted (graph) | proposed | answer_correctness | 0.7613 ± 0.0096 (n=3) | 15, 15, 15 | no |
| llm_drafted (graph) | proposed | retrieval_latency_seconds | 2.6378 ± 0.0305 (n=3) | 15, 15, 15 | no |

## Paired case-level comparisons

Comparisons use graph cases separated by `label_source`; mixed document/graph and development/new-set tests are omitted. Each case is averaged over available repeats before pairing by case name. Differences are proposed minus comparator; p-values use a two-sided exact Wilcoxon signed-rank test with zero differences omitted and are unadjusted exploratory values. The per-repeat counts expose uneven coverage; `n` is the number of paired cases (the test uses nonzero pairs).

| Source group | Comparison | Metric | Mean difference | p-value | n paired (nonzero) | Proposed cases/repeat | Comparator cases/repeat | Coverage |
|---|---|---|---:|---:|---:|---|---|---|
| existing_v2 (graph) | proposed - link_all | precision | -0.0502 | 0.1250 | 5 (4) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | recall | 0.0222 | 1.0000 | 5 (1) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | mrr | 0.1333 | 0.5000 | 5 (2) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | ndcg_at_10 | 0.0526 | 0.3125 | 5 (5) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | faithfulness | -0.0039 | 0.5000 | 5 (2) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | answer_relevancy | 0.0067 | 0.4375 | 5 (5) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | answer_correctness | -0.0026 | 0.8125 | 5 (5) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | context_precision | 0.1085 | 0.3125 | 5 (5) | 5, 5, 5 | 5, 5, 5 | available |
| existing_v2 (graph) | proposed - link_all | context_recall | -0.0510 | 0.1250 | 5 (4) | 5, 5, 5 | 5, 5, 5 | available |
| llm_drafted (graph) | proposed - link_all | precision | 0.0411 | 0.6250 | 15 (7) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | recall | -0.0333 | 0.5000 | 15 (4) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | mrr | -0.0333 | 1.0000 | 15 (1) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | ndcg_at_10 | -0.0418 | 0.2500 | 15 (6) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | faithfulness | 0.0055 | 0.0312 | 15 (7) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | answer_relevancy | 0.0180 | 0.0554 | 15 (15) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | answer_correctness | -0.0046 | 0.5614 | 15 (15) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | context_precision | 0.0231 | 0.1289 | 15 (9) | 15, 15, 15 | 14, 15, 14 | partial |
| llm_drafted (graph) | proposed - link_all | context_recall | -0.0123 | 1.0000 | 15 (4) | 15, 15, 15 | 14, 15, 14 | partial |
