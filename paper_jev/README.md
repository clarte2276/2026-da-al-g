# Jev vs LLM link construction

This project measures whether Jev or a chat model can reconstruct approved
cross-document links from railway guide slides to regulation articles.

The experiment code, prompts, response cache, and paper-ready summaries are in
[experiments/](experiments/README.md). The runtime directory holds disposable
SQLite copies and is ignored by Git; source databases and API keys stay outside
this worktree.

Only the 36 currently approved links are labeled positive. Missing approval is
not proof that an edge is irrelevant, so reported precision and false positives
measure agreement with the current curated graph.

The K=50/100 candidate-recall and judge-quality follow-up, its exact commands,
cost accounting, and downstream evaluation status are documented in
[experiments/README.md](experiments/README.md).

The K=100 LLM pair run stopped at 302/800 batches after OpenAI reported no
credits, so its full-run cost is projected and its partial usage is reported.
K=100 Jev results have one complete repeat. The best Jev downstream run failed
on its first OpenAI embedding request with HTTP 429; cascade was skipped after
that failure.
