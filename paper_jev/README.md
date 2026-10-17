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
