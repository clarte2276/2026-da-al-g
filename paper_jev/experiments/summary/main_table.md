# Main results

Gold: 36 approved DB records, 96 target article ranges, and 96 unique source-selection/article edges across 80 positive slides. The negative set has 80 draws from 77 unique unlinked slides.

## Candidate recall

A target edge is covered when any slide in its approved source selection retrieves that article.

| K | Gold edges recalled | Edge recall | Link records with every target covered | Record recall |
|---:|---:|---:|---:|---:|
| 10 | 26/96 | 0.271 | 6/36 | 0.167 |
| 20 | 35/96 | 0.365 | 9/36 | 0.250 |

## Edge metrics

Metrics are over 96 approved source-selection/article targets, with each group score equal to the maximum probability among its selected slides. Threshold 0.5 uses judge probability (raw hybrid score for score_only). Best F1 and its threshold are tuned post hoc on this same labeled set; they are optimistic descriptive upper bounds, not held-out estimates.

| Judge | P@0.5 | R@0.5 | F1@0.5 | Best F1 (threshold) | PR-AUC | ECE | Determinism |
|---|---:|---:|---:|---:|---:|---:|---:|
| score_only | 0.000 | 0.000 | 0.000 | 0.047 (0.340) | 0.006 | n/a | 1.000 |
| jev_pair | 0.123 +/- 0.009 | 0.087 +/- 0.006 | 0.102 +/- 0.007 | 0.180 +/- 0.005 (0.260 +/- 0.010) | 0.060 +/- 0.001 | 0.079 +/- 0.001 | 0.991 |
| jev_choice | 0.247 +/- 0.015 | 0.062 +/- 0.000 | 0.100 +/- 0.001 | 0.187 +/- 0.004 (0.153 +/- 0.012) | 0.080 +/- 0.001 | 0.064 +/- 0.001 | 0.996 |
| llm_pair | 0.146 +/- 0.010 | 0.222 +/- 0.006 | 0.176 +/- 0.009 | 0.179 +/- 0.006 (0.287 +/- 0.427) | 0.043 +/- 0.002 | 0.122 +/- 0.005 | 0.945 |
| llm_list | 0.126 +/- 0.012 | 0.160 +/- 0.006 | 0.140 +/- 0.010 | 0.167 +/- 0.010 (0.173 +/- 0.110) | 0.042 +/- 0.003 | 0.101 +/- 0.006 | 0.963 |
| cascade | 0.177 +/- 0.047 | 0.205 +/- 0.012 | 0.187 +/- 0.023 | 0.191 +/- 0.026 (0.830 +/- 0.026) | 0.043 +/- 0.016 | 0.096 +/- 0.026 | 0.936 |

Each probabilistic metric is mean +/- sample standard deviation over three repeats; score_only is fixed. PR-AUC is stepwise average precision. ECE uses ten equal-width bins and includes any missed gold edges at probability zero; raw hybrid scores have no ECE. Per-repeat reliability counts are in reliability_bins.csv.

## Judge cost and latency

Costs use reported API usage and the prices in notes.md. p50/p95 are per call; total wall time sums sequential API-call latencies and excludes local cache/parsing overhead.

| Judge | Calls | Input tokens | Output tokens | Cost USD | p50 s/call | p95 s/call | Total wall seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| score_only | 0 | 0 | 0 | 0.000000 | n/a | n/a | 0.00 |
| jev_pair | 480 | 5625972 | 93120 | 0.236291 | 0.30 | 0.39 | 148.94 |
| jev_choice | 480 | 2892135 | 108781 | 0.121470 | 0.26 | 0.32 | 129.75 |
| llm_pair | 74 | 5808287 | 115835 | 0.726212 | 7.37 | 16.98 | 668.05 |
| llm_list | 61 | 2430530 | 43190 | 0.254104 | 4.58 | 5.28 | 284.13 |
| cascade | 12 | 708994 | 11892 | 0.156069 | 7.42 | 8.00 | 72.55 |
| cascade pipeline (Jev + LLM) | 492 | 6334966 | 105012 | 0.392360 | 0.31 | 0.41 | 221.49 |

## Downstream retrieval (proposed, skip RAGAS)

Means over all 37 cases; linked-gold recall averages cases where via_link gold is defined. Graph-only means are in downstream_summary.json.

| Link set | Cases | Recall | MRR | nDCG@10 | Linked-gold recall |
|---|---:|---:|---:|---:|---:|
| gold | 37 | 0.912 | 0.982 | 0.919 | 0.750 |
| none | 37 | 0.773 | 0.986 | 0.815 | 0.200 |
| jev_pair | 37 | 0.818 | 0.986 | 0.851 | 0.350 |
| llm_pair | 37 | 0.813 | 0.968 | 0.840 | 0.400 |
| cascade | 37 | 0.840 | 0.986 | 0.869 | 0.450 |

Downstream reranker cost and latency:

| Link set | Calls | Input tokens | Output tokens | Cost USD | p50 s/call | p95 s/call | Call seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| gold | 93 | 251783 | 421 | 0.050485 | 0.86 | 1.21 | 65.60 |
| none | 74 | 238794 | 310 | 0.005168 | 0.23 | 1.22 | 42.74 |
| jev_pair | 85 | 249558 | 396 | 0.007424 | 0.79 | 1.24 | 53.54 |
| llm_pair | 89 | 259749 | 434 | 0.009508 | 0.85 | 1.35 | 61.46 |
| cascade | 91 | 261403 | 451 | 0.009602 | 0.84 | 1.25 | 59.44 |

## Full RAGAS on graph cases (one repeat)

Runs use the best-F1 Jev judge (`jev_choice`) and LLM judge (`llm_pair`) selected on the same edge set.

| Link set | Cases | Faithfulness | Answer relevancy | Answer correctness | Context precision | Context recall | Retrieval recall | Retrieval MRR | Retrieval nDCG@10 | Linked-gold recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gold | 20 | 0.976 | 0.836 | 0.764 | 0.960 | 0.918 | 0.817 | 0.975 | 0.827 | 0.650 |
| jev_choice | 20 | 0.979 | 0.824 | 0.734 | 0.975 | 0.821 | 0.650 | 0.975 | 0.715 | 0.375 |
| llm_pair | 20 | 0.969 | 0.826 | 0.736 | 0.933 | 0.828 | 0.708 | 0.950 | 0.735 | 0.450 |

Full RAGAS API cost and latency:

| Link set | Calls | Input tokens | Output tokens | Cost USD | p50 s/call | p95 s/call | Call seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| gold | 538 | 1031398 | 132800 | 0.322238 | 1.44 | 7.43 | 1235.02 |
| jev_choice | 505 | 936320 | 130971 | 0.262826 | 1.51 | 7.25 | 1187.23 |
| llm_pair | 542 | 1074933 | 145376 | 0.292515 | 1.53 | 8.18 | 1315.15 |

See notes.md, edge_metrics.json, threshold_curve.csv, reliability_bins.csv, false_positives.csv, and cache/ for full details.
