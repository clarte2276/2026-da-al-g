# Round 2 cached re-analysis

All values below are recomputed from `paper_jev/experiments/cache/`; the script imports no API client and makes no network calls. Jev pair, LLM pair, and cascade share the candidate-level yes/no event and are compared on probability/ranking metrics. Jev choice and LLM list use their native selected edges and are reported as discrete selection outputs; their one-of-N or multi-label scores are not compared with pair-level ECE.
P/R/F1 and false-positive counts measure agreement with the current approved graph; an unapproved candidate is not independently confirmed irrelevant.

## Evaluation units and denominators

| Quantity | Count / mapping |
|---|---:|
| Approved link records | 36 |
| Record/article targets (existing gold edges) | 96 |
| Selected positive pages | 80 |
| Positive selection-page/article edges | 209 |
| Negative slide draws / unique source slides | 80 / 77 |
| Sampled duplicate negative draws | 3 |
| Slide-article edge | Each page inside an approved selection crossed with every target article in that record; each sampled unlinked page contributes its retrieved slide/article candidates as negatives. A target omitted from that page's K candidates is retained as a zero-score false negative. |
| Link-record level | Each approved record is collapsed to record/article targets; when a record spans pages, the cached probability is the maximum over its selected pages. The 80 negative slide draws remain separate negative candidate groups. |
| Candidate-missing gold | Included as p=0 for recall and ECE, and always retained as a false negative; it is never threshold-predictable. PR-AUC ranks candidate-scored edges only but uses all gold positives in its recall denominator, matching the existing experiment implementation. |
| False positives from negative controls | Counted at p≥0.5 on all candidate edges from the 80 negative draws, including the three duplicate draws. |

The 36 link records and 77 unique negative slides are resampled as separate cluster strata. A sampled negative cluster carries all of its original draw copies, preserving the observed duplicate weighting. Each bootstrap uses 2,000 resamples and seed 20261018. The interval is a percentile 95% cluster-bootstrap interval for the mean metric over available API repeats; the `±` term is the sample SD across repeats and is not a confidence interval.

## Candidate coverage

| K | Target link/article edges covered | Candidate recall | Target page/article edges covered | Page-edge recall |
|---:|---:|---:|---:|---:|
| 10 | 26/96 | 0.271 | 42/209 | 0.201 |
| 50 | 49/96 | 0.510 | 103/209 | 0.493 |

## Pair-level yes/no results with sample uncertainty

The primary unit is the slide-article edge: each page in an approved selection is crossed with each target article, and each negative-slide draw contributes candidate edges. Each cell is `mean ± repeat SD; [95% cluster-bootstrap CI]`, over 3 repeats. Candidate-missing gold is p=0 in end-to-end metrics; candidate-covered metrics exclude only those missing gold edges. PR-AUC ranks candidate-scored edges with all gold positives in the recall denominator. ECE is 10-bin equal-width and only compares pair-level yes/no probabilities. Values measure agreement with the approved graph, not verified relevance accuracy.

### Slide-article edge unit

| K | Judge | P@0.5 | R@0.5 | F1@0.5 | PR-AUC | ECE |
|---:|---|---|---|---|---|---|
| 10 | jev_pair | 0.203 ± 0.007; [0.073, 0.363] | 0.078 ± 0.003; [0.027, 0.142] | 0.113 ± 0.004; [0.040, 0.203] | 0.050 ± 0.001; [0.015, 0.119] | 0.121 ± 0.001; [0.090, 0.152] |
| 10 | llm_pair | 0.175 ± 0.009; [0.098, 0.271] | 0.152 ± 0.007; [0.084, 0.231] | 0.162 ± 0.008; [0.091, 0.244] | 0.044 ± 0.001; [0.012, 0.111] | 0.172 ± 0.003; [0.143, 0.201] |
| 10 | cascade | 0.235 ± 0.054; [0.120, 0.369] | 0.159 ± 0.007; [0.077, 0.261] | 0.188 ± 0.013; [0.093, 0.296] | 0.043 ± 0.013; [0.012, 0.104] | 0.140 ± 0.024; [0.109, 0.172] |
| 50 | jev_pair | 0.199 ± 0.001; [0.119, 0.308] | 0.179 ± 0.003; [0.115, 0.244] | 0.188 ± 0.001; [0.118, 0.265] | 0.086 ± 0.000; [0.039, 0.165] | 0.064 ± 0.000; [0.056, 0.073] |
| 50 | cascade | 0.153 ± 0.040; [0.101, 0.221] | 0.244 ± 0.068; [0.171, 0.319] | 0.188 ± 0.050; [0.129, 0.256] | 0.066 ± 0.025; [0.031, 0.124] | 0.068 ± 0.003; [0.059, 0.077] |

### Link-record unit

| K | Judge | P@0.5 | R@0.5 | F1@0.5 | PR-AUC | ECE |
|---:|---|---|---|---|---|---|
| 10 | jev_pair | 0.123 ± 0.009; [0.046, 0.230] | 0.087 ± 0.006; [0.033, 0.154] | 0.102 ± 0.007; [0.038, 0.181] | 0.060 ± 0.001; [0.021, 0.132] | 0.079 ± 0.001; [0.054, 0.104] |
| 10 | llm_pair | 0.146 ± 0.010; [0.088, 0.221] | 0.222 ± 0.006; [0.130, 0.337] | 0.176 ± 0.009; [0.107, 0.260] | 0.043 ± 0.002; [0.016, 0.103] | 0.122 ± 0.005; [0.096, 0.148] |
| 10 | cascade | 0.177 ± 0.047; [0.103, 0.268] | 0.205 ± 0.012; [0.109, 0.322] | 0.187 ± 0.023; [0.106, 0.283] | 0.043 ± 0.016; [0.015, 0.098] | 0.096 ± 0.026; [0.071, 0.122] |
| 50 | jev_pair | 0.133 ± 0.004; [0.081, 0.203] | 0.215 ± 0.006; [0.137, 0.298] | 0.164 ± 0.004; [0.103, 0.235] | 0.083 ± 0.001; [0.040, 0.164] | 0.077 ± 0.000; [0.069, 0.085] |
| 50 | cascade | 0.106 ± 0.025; [0.074, 0.146] | 0.295 ± 0.071; [0.218, 0.380] | 0.156 ± 0.037; [0.112, 0.207] | 0.059 ± 0.021; [0.031, 0.111] | 0.080 ± 0.002; [0.072, 0.089] |

Candidate-covered metrics below use the same slide-article unit and available pair-level yes/no judges:

| K | Judge | Covered P@0.5 | Covered R@0.5 | Covered F1@0.5 | Covered PR-AUC |
|---:|---|---|---|---|---|
| 10 | jev_pair | 0.203 ± 0.007; [0.073, 0.363] | 0.389 ± 0.014; [0.191, 0.552] | 0.266 ± 0.009; [0.106, 0.419] | 0.248 ± 0.006; [0.112, 0.425] |
| 10 | llm_pair | 0.175 ± 0.009; [0.098, 0.271] | 0.754 ± 0.036; [0.621, 0.881] | 0.284 ± 0.014; [0.172, 0.402] | 0.218 ± 0.007; [0.097, 0.387] |
| 10 | cascade | 0.235 ± 0.054; [0.120, 0.369] | 0.794 ± 0.036; [0.600, 0.917] | 0.360 ± 0.061; [0.201, 0.513] | 0.213 ± 0.067; [0.096, 0.357] |
| 50 | jev_pair | 0.199 ± 0.001; [0.119, 0.308] | 0.362 ± 0.006; [0.276, 0.444] | 0.257 ± 0.001; [0.169, 0.347] | 0.175 ± 0.001; [0.098, 0.284] |
| 50 | cascade | 0.153 ± 0.040; [0.101, 0.221] | 0.495 ± 0.138; [0.402, 0.581] | 0.233 ± 0.062; [0.164, 0.310] | 0.135 ± 0.052; [0.077, 0.219] |

K=50 LLM pair has no complete cached run and is omitted; incomplete K=100 runs have no performance estimates.

## Native selection outputs

Selection precision/recall/F1 and FP counts use the same slide-article edge labels as the pair-level table. Top-1 accuracy is the fraction of 80 positive source pages whose Jev choice or highest-confidence selected LLM-list item matches any approved target article; an empty output is incorrect. No selection ECE is calculated.

| K | Judge | End-to-end P/R/F1 | Candidate-covered P/R/F1 | FP edges | Positive-page top-1 accuracy |
|---:|---|---|---|---:|---:|
| 10 | jev_choice | 0.343 ± 0.004; [0.139, 0.535] / 0.073 ± 0.003; [0.025, 0.132] / 0.121 ± 0.004; [0.042, 0.210] | 0.343 ± 0.004; [0.139, 0.535] / 0.365 ± 0.014; [0.193, 0.490] / 0.354 ± 0.009; [0.165, 0.493] | 29.3 ± 0.6 | 0.192 ± 0.007 |
| 10 | llm_list | 0.137 ± 0.009; [0.071, 0.221] / 0.081 ± 0.005; [0.044, 0.125] / 0.102 ± 0.006; [0.054, 0.156] | 0.137 ± 0.009; [0.071, 0.221] / 0.405 ± 0.024; [0.288, 0.567] / 0.205 ± 0.013; [0.118, 0.295] | 107.0 ± 6.1 | 0.150 ± 0.022 |
| 50 | jev_choice | 0.440 ± 0.009; [0.254, 0.618] / 0.105 ± 0.000; [0.055, 0.161] / 0.170 ± 0.001; [0.091, 0.253] | 0.440 ± 0.009; [0.254, 0.618] / 0.214 ± 0.000; [0.132, 0.288] / 0.288 ± 0.002; [0.176, 0.384] | 28.0 ± 1.0 | 0.275 ± 0.000 |
At p≥0.5, false positives are split between wrong candidate articles on positive pages and candidate links from unlinked negative-slide draws:

| K | Judge | FP on positive pages (mean ± repeat SD) | FP from negative draws (mean ± repeat SD) | Total FP |
|---:|---|---:|---:|---:|
| 10 | jev_pair | 46.7 ± 1.5 | 17.7 ± 1.5 | 64.3 |
| 10 | jev_choice | 15.3 ± 0.6 | 14.0 ± 0.0 | 29.3 |
| 10 | llm_pair | 108.0 ± 8.9 | 41.7 ± 10.8 | 149.7 |
| 10 | llm_list | 75.0 ± 4.6 | 32.0 ± 4.4 | 107.0 |
| 10 | cascade | 90.3 ± 19.2 | 24.3 ± 21.5 | 114.7 |
| 50 | jev_pair | 111.0 ± 4.0 | 39.3 ± 2.5 | 150.3 |
| 50 | jev_choice | 17.0 ± 0.0 | 11.0 ± 1.0 | 28.0 |
| 50 | cascade | 198.0 ± 26.2 | 84.7 ± 16.0 | 282.7 |

## Paired cluster-bootstrap differences

Delta is first method minus second, paired on the same resampled link and negative-slide clusters and averaged over repeats. ECE differences are limited to the shared pair-level yes/no event.

| Unit | Comparison | Metric | Mean Δ ± repeat SD | 95% paired cluster-bootstrap CI |
|---|---|---|---:|---:|
| slide_edge | jev_pair − llm_pair (K=10) | precision | 0.028 ± 0.005 | [-0.050, 0.124] |
| slide_edge | jev_pair − llm_pair (K=10) | recall | -0.073 ± 0.006 | [-0.115, -0.034] |
| slide_edge | jev_pair − llm_pair (K=10) | f1 | -0.049 ± 0.006 | [-0.092, -0.008] |
| slide_edge | jev_pair − llm_pair (K=10) | pr_auc | 0.006 ± 0.000 | [-0.009, 0.028] |
| slide_edge | jev_pair − llm_pair (K=10) | ece | -0.051 ± 0.003 | [-0.067, -0.035] |
| slide_edge | cascade − llm_pair (K=10) | precision | 0.061 ± 0.061 | [0.012, 0.115] |
| slide_edge | cascade − llm_pair (K=10) | recall | 0.008 ± 0.003 | [-0.028, 0.046] |
| slide_edge | cascade − llm_pair (K=10) | f1 | 0.026 ± 0.020 | [-0.013, 0.067] |
| slide_edge | cascade − llm_pair (K=10) | pr_auc | -0.001 ± 0.015 | [-0.020, 0.015] |
| slide_edge | cascade − llm_pair (K=10) | ece | -0.031 ± 0.025 | [-0.043, -0.019] |
| slide_edge | cascade − jev_pair (K=10) | precision | 0.033 ± 0.061 | [-0.057, 0.103] |
| slide_edge | cascade − jev_pair (K=10) | recall | 0.081 ± 0.005 | [0.033, 0.139] |
| slide_edge | cascade − jev_pair (K=10) | f1 | 0.075 ± 0.017 | [0.026, 0.129] |
| slide_edge | cascade − jev_pair (K=10) | pr_auc | -0.007 ± 0.015 | [-0.030, 0.007] |
| slide_edge | cascade − jev_pair (K=10) | ece | 0.020 ± 0.025 | [0.009, 0.031] |
| slide_edge | jev_pair − jev_pair K=10 (K=50) | precision | -0.004 ± 0.007 | [-0.094, 0.090] |
| slide_edge | jev_pair − jev_pair K=10 (K=50) | recall | 0.100 ± 0.005 | [0.054, 0.147] |
| slide_edge | jev_pair − jev_pair K=10 (K=50) | f1 | 0.075 ± 0.005 | [0.022, 0.132] |
| slide_edge | jev_pair − jev_pair K=10 (K=50) | pr_auc | 0.036 ± 0.001 | [0.007, 0.077] |
| slide_edge | jev_pair − jev_pair K=10 (K=50) | ece | -0.057 ± 0.001 | [-0.086, -0.029] |
| link_record | jev_pair − llm_pair (K=10) | precision | -0.023 ± 0.016 | [-0.084, 0.053] |
| link_record | jev_pair − llm_pair (K=10) | recall | -0.135 ± 0.010 | [-0.221, -0.063] |
| link_record | jev_pair − llm_pair (K=10) | f1 | -0.074 ± 0.014 | [-0.133, -0.016] |
| link_record | jev_pair − llm_pair (K=10) | pr_auc | 0.016 ± 0.002 | [-0.005, 0.046] |
| link_record | jev_pair − llm_pair (K=10) | ece | -0.043 ± 0.005 | [-0.058, -0.029] |
| link_record | cascade − llm_pair (K=10) | precision | 0.031 ± 0.044 | [-0.007, 0.072] |
| link_record | cascade − llm_pair (K=10) | recall | -0.017 ± 0.016 | [-0.079, 0.042] |
| link_record | cascade − llm_pair (K=10) | f1 | 0.011 ± 0.023 | [-0.033, 0.054] |
| link_record | cascade − llm_pair (K=10) | pr_auc | -0.000 ± 0.017 | [-0.025, 0.024] |
| link_record | cascade − llm_pair (K=10) | ece | -0.026 ± 0.023 | [-0.038, -0.014] |
| link_record | cascade − jev_pair (K=10) | precision | 0.054 ± 0.055 | [-0.012, 0.112] |
| link_record | cascade − jev_pair (K=10) | recall | 0.118 ± 0.006 | [0.055, 0.203] |
| link_record | cascade − jev_pair (K=10) | f1 | 0.085 ± 0.030 | [0.033, 0.146] |
| link_record | cascade − jev_pair (K=10) | pr_auc | -0.016 ± 0.016 | [-0.050, 0.008] |
| link_record | cascade − jev_pair (K=10) | ece | 0.017 ± 0.027 | [0.007, 0.027] |
| link_record | jev_pair − jev_pair K=10 (K=50) | precision | 0.011 ± 0.006 | [-0.059, 0.072] |
| link_record | jev_pair − jev_pair K=10 (K=50) | recall | 0.128 ± 0.006 | [0.063, 0.200] |
| link_record | jev_pair − jev_pair K=10 (K=50) | f1 | 0.063 ± 0.004 | [0.006, 0.120] |
| link_record | jev_pair − jev_pair K=10 (K=50) | pr_auc | 0.024 ± 0.002 | [-0.008, 0.067] |
| link_record | jev_pair − jev_pair K=10 (K=50) | ece | -0.002 ± 0.001 | [-0.024, 0.018] |

## ECE denominator alignment

Only pair-level yes/no judges are reported. Each row gives 3-repeat mean ± SD; end-to-end includes missed gold at p=0 and candidate-covered excludes only target edges absent from that unit's candidate set. Equal-mass ECE uses 10 probability-rank bins, splitting tied-score mass fractionally at bin boundaries.

| K | Unit | Judge | End-to-end n | Covered n | ECE equal-width, end-to-end | ECE equal-mass, end-to-end | ECE equal-width, covered | ECE equal-mass, covered |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 10 | slide_edge | jev_pair | 1767 | 1600 | 0.121 ± 0.001 | 0.182 ± 0.000 | 0.097 ± 0.000 | 0.097 ± 0.000 |
| 10 | slide_edge | llm_pair | 1767 | 1600 | 0.172 ± 0.003 | 0.177 ± 0.005 | 0.088 ± 0.002 | 0.090 ± 0.005 |
| 10 | slide_edge | cascade | 1767 | 1600 | 0.140 ± 0.024 | 0.200 ± 0.024 | 0.115 ± 0.028 | 0.117 ± 0.026 |
| 50 | slide_edge | jev_pair | 8106 | 8000 | 0.064 ± 0.000 | 0.085 ± 0.000 | 0.078 ± 0.000 | 0.078 ± 0.000 |
| 50 | slide_edge | cascade | 8106 | 8000 | 0.068 ± 0.003 | 0.094 ± 0.003 | 0.082 ± 0.003 | 0.083 ± 0.001 |
| 10 | link_record | jev_pair | 1477 | 1407 | 0.079 ± 0.001 | 0.142 ± 0.000 | 0.103 ± 0.000 | 0.103 ± 0.000 |
| 10 | link_record | llm_pair | 1477 | 1407 | 0.122 ± 0.005 | 0.132 ± 0.005 | 0.087 ± 0.004 | 0.088 ± 0.005 |
| 10 | link_record | cascade | 1477 | 1407 | 0.096 ± 0.026 | 0.159 ± 0.026 | 0.116 ± 0.029 | 0.119 ± 0.026 |
| 50 | link_record | jev_pair | 6711 | 6664 | 0.077 ± 0.000 | 0.085 ± 0.000 | 0.084 ± 0.000 | 0.084 ± 0.000 |
| 50 | link_record | cascade | 6711 | 6664 | 0.080 ± 0.002 | 0.091 ± 0.002 | 0.088 ± 0.002 | 0.088 ± 0.002 |

## Threshold selection

Fixed 0.5 is the pre-specified operating point for pair-level probabilities in the cached experiment. Best-F1 uses the same labels and is post-hoc descriptive. The 5-fold threshold CV groups all pages/articles in a link record and keeps duplicate negative draws from the same unique slide in one fold; thresholds are selected on four folds and scored on the held-out fold. CV rows are link-record-level and pooled out-of-fold predictions, with API repeat SD separate.

| K | Judge | Fixed P/R/F1@0.5 (mean) | Post-hoc best F1 (mean) | Post-hoc threshold (mean ± SD) | CV threshold median [min,max] | CV OOF P | CV OOF R | CV OOF F1 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 10 | jev_pair | 0.123 ± 0.009 / 0.087 ± 0.006 / 0.102 ± 0.007 | 0.180 | 0.260 ± 0.010 | 0.260 [0.250, 0.270] | 0.123 ± 0.009 | 0.087 ± 0.006 | 0.102 ± 0.007 |
| 10 | llm_pair | 0.146 ± 0.010 / 0.222 ± 0.006 / 0.176 ± 0.009 | 0.179 | 0.287 ± 0.427 | 0.050 [0.030, 0.850] | 0.144 ± 0.007 | 0.219 ± 0.000 | 0.174 ± 0.005 |
| 10 | cascade | 0.177 ± 0.047 / 0.205 ± 0.012 / 0.187 ± 0.023 | 0.191 | 0.830 ± 0.026 | 0.840 [0.800, 0.980] | 0.181 ± 0.060 | 0.191 ± 0.012 | 0.183 ± 0.038 |
| 50 | jev_pair | 0.133 ± 0.004 / 0.215 ± 0.006 / 0.164 ± 0.004 | 0.178 | 0.700 ± 0.030 | 0.670 [0.440, 0.770] | 0.138 ± 0.011 | 0.132 ± 0.006 | 0.135 ± 0.005 |
| 50 | cascade | 0.106 ± 0.025 / 0.295 ± 0.071 / 0.156 ± 0.037 | 0.168 | 0.777 ± 0.197 | 0.880 [0.550, 0.990] | 0.110 ± 0.022 | 0.236 ± 0.074 | 0.150 ± 0.035 |

## False-positive review sample

A false positive here means an unapproved candidate selected at p≥0.5. Since gold is incomplete, these are disagreement cases, not confirmed irrelevant links. Up to 40 candidates with max p≥0.80 were stratified by dominant judge and confidence band; two reviewer columns are left blank in `paper_jev/data/fp_review_checklist.md` and `.csv`.

Checklist rows: 40.

## Reproducibility and cost appendix

| API family | Requested model id | Returned model id(s) in response cache |
|---|---|---|
| Jev System One | `jev-latest` | `jev-1.13.0` |
| OpenAI chat | `gpt-5.6-luna` | `gpt-5.6-luna` |

Prompt file SHA-256:

| File | SHA-256 |
|---|---|
| `paper_jev/experiments/prompts/common.md` | `a2e3e839ecb915e1588040c6c77d65937bdcc8088f2991393ca2a1c40bbf78d9` |
| `paper_jev/experiments/prompts/jev_pair.md` | `5c98f90dac422f12b72fce95fc66b4f94e2f32c651200068dde60518162bc382` |
| `paper_jev/experiments/prompts/jev_choice.md` | `4ce6a41d9d525e9113c51b4339e0921e8425e5a85110e87f647f11a485fbc30d` |
| `paper_jev/experiments/prompts/llm_pair.json` | `919ee4310a2fd4fdbeac246d3cfd2e10e41a3ec6bc3d992cda0d321fc90a3b02` |
| `paper_jev/experiments/prompts/llm_list.json` | `55c9d99f8203b2069bc7396e0e4f23f5410e024564858685b8978c4458e51883` |
| `paper_jev/experiments/prompts/cascade.md` | `0f37d4be87574a9b18959703ba742cd96ded724860529e6b5367b855682ace16` |

| Reproduction setting | Value |
|---|---|
| Data/negative draw seed | 20261017; 80 negative draws from 77 unique slides, with replacement when needed |
| Cached API call timestamps | 2026-10-17T02:01:52.622879+00:00 to 2026-10-17T05:10:40.057551+00:00 UTC |
| OpenAI request settings | JSON object response, temperature 0, reasoning effort none, max_completion_tokens 4096 (from the cached runner code) |
| Jev request types | Pair questions use `noul`; per-slide single choice uses `choice`; response probabilities are preserved from cache. |
| Bootstrap | 2000 cluster resamples; seed 20261018; 36 approved-record clusters and 77 negative-slide clusters |
| Grouped threshold CV | 5 folds; seed 20261019; grouped by approved link id and unique negative slide id |
| FP checklist stratification | seed 20261020; max p≥0.80; up to 4 per dominant-judge/confidence stratum |
| Hybrid candidates | K=10 and K=50 from stored 0.6 cosine / 0.4 BM25 rankings; 160 source draws (80 positive pages, 80 negative draws) |
| K=50 reuse | Jev pair imports K=10 pair scores and calls only for newly added candidates; cascade reuses these pair scores. |
| Unavailable K=50 judge | LLM pair has no complete cached K=50 run. |

Recomputed cached-call costs use `usage` tokens, not the cache's `cost_usd`: OpenAI gpt-5.6-luna input USD 0.20/M, cached input USD 0.02/M, output USD 1.20/M; Jev input USD 0.042/M and output free. Price sources: [OpenAI gpt-5.6-luna pricing](https://developers.openai.com/api/docs/models/gpt-5.6-luna) and [TypeSafe System One API documentation](https://docs.typesafe.ai/llms.txt). Latency is the sum of cached per-call `latency_seconds` for sequential requests; it excludes local parsing, candidate generation, and downstream calls.

| Setting | Judge/API stage | API calls | Input / cached input / output tokens | Recomputed USD | Cache-recorded USD | Δ USD | Summed call seconds |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline | jev_pair | 480 | 5625972 / 0 / 93120 | 0.236291 | 0.236291 | +0.000000000 | 148.94 |
| baseline | jev_choice | 480 | 2892135 / 0 / 108781 | 0.121470 | 0.121470 | +0.000000000 | 129.75 |
| baseline | llm_pair | 74 | 5808287 / 3191376 / 115835 | 0.726212 | 0.726212 | +0.000000000 | 668.05 |
| baseline | llm_list | 61 | 2430530 / 1576834 / 43190 | 0.254104 | 0.254104 | +0.000000000 | 284.13 |
| baseline | cascade | 12 | 708994 / 0 / 11892 | 0.156069 | 0.156069 | +0.000000000 | 72.55 |
| hybrid_50 | jev_pair | 1920 | 19390008 / 0 / 372480 | 0.814380 | 0.814380 | +0.000000000 | 569.20 |
| hybrid_50 | jev_choice | 480 | 9423714 / 0 / 464708 | 0.395796 | 0.395796 | +0.000000000 | 168.62 |
| hybrid_50 | cascade | 27 | 1776845 / 0 / 33079 | 0.395064 | 0.395064 | +0.000000000 | 201.73 |
| baseline | cascade pipeline = Jev pair + LLM cascade | 492 | 6334966 / 0 / 105012 | 0.392360 | 0.392360 | +0.000000000 | 221.49 |
| hybrid_50 | cascade pipeline = Jev pair + LLM cascade | 1947 | 21166853 / 0 / 405559 | 1.209444 | 1.209444 | +0.000000000 | 770.93 |
| hybrid_50 | Jev pair incl. K=10 reuse | 2400 | 25015980 / 0 / 465600 | 1.050671 | 1.050671 | +0.000000000 | 718.13 |
| hybrid_50 | cascade pipeline incl. K=10 reuse | 2439 | 27501819 / 0 / 510571 | 1.601804 | 1.601804 | +0.000000000 | 992.41 |

Cache completeness by setting:

| K | Judge | Repeat count | Score rows/repeat | Expected slide-candidate rows | Actual API calls in setting cache |
|---:|---|---:|---:|---:|---:|
| 10 | jev_pair | 3 | 1600 | 1600 | 480 |
| 10 | jev_choice | 3 | 1600 | 1600 | 480 |
| 10 | llm_pair | 3 | 1600 | 1600 | 74 |
| 10 | llm_list | 3 | 1600 | 1600 | 61 |
| 10 | cascade | 3 | 1600 | 1600 | 12 |
| 50 | jev_pair | 3 | 8000 | 8000 | 1920 |
| 50 | jev_choice | 3 | 8000 | 8000 | 480 |
| 50 | cascade | 3 | 8000 | 8000 | 27 |

K=10 cache-derived judge total: OpenAI USD 1.136385, Jev USD 0.357760. The pre-existing `summary/cost_latency.json` totals are OpenAI USD 1.136385 and Jev USD 0.357760; the per-judge cache-vs-summary values are reported above. K=50 stage rows are incremental unless marked `incl. K=10 reuse`; the cumulative cascade pipeline is USD 1.601804.

## Credits still required

See [pending_credit.md](pending_credit.md) for estimated costs and exact commands for K=10 downstream repeats, K=50 downstream, and completed K=100 repeats/LLM pair.

## Notes

The slide-edge view distributes every approved record/article target to each page selected by that record; this deliberately differs from the existing record-level max-over-pages score. Negative controls contribute false positives as candidate slide/article predictions, not as confirmed irrelevant edges. The paired intervals are descriptive resampling uncertainty on this one fixed domain and incomplete approved graph; they do not support population-level superiority claims.

K=50 downstream, K=100 downstream-independent repeats, a complete K=100 LLM pair run, and expert adjudication of unapproved predictions remain unavailable without new credits or human review.
