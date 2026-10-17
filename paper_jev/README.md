# Jev vs LLM link construction

## Final status

- **Done:** cached offline re-analysis, Round 2 response summary, anonymous Korean manuscript, KIISE DOCX and rendered PDF page-count check.
- **Still needed:** credit-blocked experiment runs, human review of 40 high-confidence false-positive candidates, and a final visual check in Microsoft Word.
- Current paper claims are limited to agreement with the 36 approved links and the single railway domain; unapproved edges are not confirmed negatives.

## Folder map

- `data/`: frozen evaluation/candidate inputs and the pending FP review checklist.
- `experiments/cache/`: saved model request/response records used for offline analysis.
- `experiments/prompts/`: versioned prompts for pair, choice, list and cascade runs.
- `experiments/reanalysis.py`: cache-only recalculation; `experiments/summary/`: result tables, costs, pending-credit commands and reproducibility hashes.
- `drafts/`: source DOCX builder and earlier round drafts.
- `reviews/`: Round 1 and Round 2 referee reports and consolidated decisions.
- `final/`: `final_draft.md`, anonymous `final_draft.docx`, and rendered `final_draft.pdf` (3 pages).
- `runtime/`: disposable SQLite copies; ignored by Git.

The experiment code, prompts, response cache, and paper-ready summaries are in [experiments/](experiments/README.md). Source databases and API keys stay outside this worktree.