# Round 2 artifact reproducibility

The Round 2 metrics and manuscript tables were recomputed locally from the saved response cache. This re-analysis made no API requests.

## Pinned code and inputs

| Artifact | Revision / SHA-256 |
|---|---|
| Git revision present at the start of cache analysis | `2b1803fd27b771a7c83058c17d74c84f36d52e16` |
| Offline re-analysis code, `paper_jev/experiments/reanalysis.py` | `3d43f12adebd12097626c7364610ffdc964abf26ecc72f7eb2e121264079f1ba` |
| Candidate and approved-link snapshot, `paper_jev/experiments/data/experiment_data.json` | `fe996b10c723b69fd1bdc5823b6db9d15f35e052571efd1ef0f4fc35b5674f4` |
| Downstream evaluation set, `paper_jev/experiments/data/eval_set_v3.json` | `dfdf59adf6ef69951d3e6592c17f382b137de6f4a17c6dc3855fd66dbf448399` |

The experiment-data file pins the candidate rankings, approved-link labels, article mapping, and source sampling used in the cache analysis. The evaluation file pins the downstream cases. The original SQLite database and its historical approved-link snapshot hash were not preserved in this worktree, so database-level reconstruction is unavailable; current results are reproducible from the pinned JSON inputs and saved responses.

## Cache provenance and rerun

The cache records requested Jev model `jev-latest` (returned `jev-1.13.0`) and OpenAI model `gpt-5.6-luna`, with calls timestamped 2026-10-17 02:01:52–05:10:40 UTC. Prompt SHA-256 values and request settings are listed in `round2_tables.md`. The updated `reanalysis.py` reads only these files and writes `round2_tables.md` plus `pending_credit.md`; it does not call either API or rewrite the human-review checklist.

Run from the repository root with NumPy available:

```powershell
python paper_jev/experiments/reanalysis.py
```

`round2_tables.md` records the resulting analysis definitions, repeat SD, cluster-bootstrap intervals, candidate-covered metrics, native selection metrics, and cache-derived cost rollups.