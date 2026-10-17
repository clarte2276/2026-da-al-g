# Experiment notes

## Dataset and units

The source DB contains 36 approved REFERENCES selections, 96 target article ranges, and 80 positive guide slide pages. We draw 80 unlinked-slide samples from 77 unique unlinked slides using seed 20261017; sampling uses replacement when the negative pool is smaller. There are 96 unique source-selection/article target edges. Metrics score each approved selection/article pair by the maximum probability across slides in that selection; slide-level API judgments remain the same for every judge.

Gold is incomplete: only human-approved links are positive labels. An edge absent from the approved set may still be valid, so precision and false positives measure agreement with current approvals, not objective relevance.

## Candidate generation

Stored slide and article embeddings are reused with production weights (0.6 cosine and 0.4 BM25); no embedding API is called. Judges receive the identical top-10 candidate list per slide; candidate recall is also measured at K=100 and is their upper bound. The corpus contains 354 reconstructed regulation article units.

## Metrics and tuning

Threshold-0.5 metrics use probabilities; score_only uses the raw hybrid score. Best-F1 thresholds are tuned post hoc on this same labeled candidate set and are optimistic in-sample values, not held-out estimates. PR-AUC is stepwise average precision. ECE uses ten equal-width bins; missed gold edges receive probability zero. ECE is not applicable to raw hybrid ranking scores. Determinism is the fraction of candidate edges with identical >=0.5 decisions across three repeats; the score baseline is fixed by construction.

Jev choice emits one article or none per slide and uses per-option probabilities. LLM list returns zero or more ids with p(yes). Cascade sends Jev probabilities in the inclusive 0.2-0.8 band to the same LLM pair prompt.

## Cost and runtime

OpenAI price: input USD 0.20/M, cached input USD 0.02/M, output USD 1.20/M for gpt-5.6-luna; source: https://developers.openai.com/api/docs/models/gpt-5.6-luna. Jev price: input USD 0.042/M, output free; source: https://docs.typesafe.ai/llms.txt. Downstream text-embedding-3-small input is USD 0.02/M; source: https://developers.openai.com/api/docs/models/text-embedding-3-small. Full RAGAS uses text-embedding-3-large at USD 0.13/M input; source: https://developers.openai.com/api/docs/models/text-embedding-3-large. Costs use API usage fields and cached-input counts when returned. The runner guards cumulative OpenAI spend at USD 15 and Jev at USD 5.

Recorded judge spend: OpenAI USD 2.096150; Jev USD 0.357760. The optional gpt-4o-mini point was not run. Full RAGAS was run once on 20 graph cases for gold, best Jev (`jev_choice`), and best LLM (`llm_pair`). Retrieval-only results cover all 37 evaluation cases.

## Error analysis

false_positives.csv lists up to 20 false-positive source-selection/article edges per judge at threshold 0.5. Categories use a reproducible heuristic: generic for low-specificity slide text; related-but-unapproved for lexical overlap with another approved target article; wrong article otherwise. These are audit labels, not human adjudications.

## Reproduction

See ../README.md. API responses, usage, and request latency are cached under cache/; aggregate performs no API calls.





## Follow-up experiments

Candidate settings use the stored 0.6 cosine / 0.4 BM25 rank at K=10, 20, 50, and 100. Rule candidates parse explicit article-number and clause references, plus appendix references, then map them to article units; a regulation filename mention maps to all articles in that document. Union settings preserve hybrid order and append rule-only article units. No embedding API was called. Candidate counts and recall are reported by setting.

Conditional precision, recall, F1, PR-AUC, and ECE use only gold edges covered by that setting; end-to-end tables continue to count candidate-missing gold as false negatives. Jev pair K=50/K=100 reuse the previous K's pair scores because each pair question is independent. Jev choice K=100 uses two 50-candidate requests per slide after the full request exceeded Jev's context limit. Three repeats were requested; K=50 completed all three. Cascade uses the inclusive 0.20-0.80 band.

LLM pair K=100: projected (partial; insufficient_quota); full one-repeat cost is USD 2.420706, projected from K=10 per-pair API usage at USD 2.420706; partial calls 302, 4265280 input tokens, USD 0.969278. See README.md for exact commands.

Cumulative spend after follow-up: OpenAI USD 3.638244 / 15.00; Jev USD 2.116928 / 5.00. API response cache entries are under cache/followup/.

K=100 Jev-derived results have one complete repeat: the next Jev request returned HTTP 402 billing_error (no organization credits available), so the remaining repeats were not run. The best-link downstream choice uses a complete three-repeat K=50 result. No further Jev requests after the billing error were attempted.
K=100 LLM pair stopped after 302/800 batches because OpenAI returned HTTP 429 insufficient_quota (no credits remaining); no retry was made.
Downstream status: best_jev: first embedding request returned HTTP 429 insufficient_quota (no credits remaining); best_cascade: skipped after best_jev returned HTTP 429 insufficient_quota.
