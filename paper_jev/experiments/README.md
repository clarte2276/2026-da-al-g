# Reproduce the link construction experiment

Run commands from `ROOT/back/`, the source checkout. Set `ROOT` to the read-only source checkout and `PAPER_JEV` to this worktree's `paper_jev/` directory; all experiment outputs and database copies stay under `PAPER_JEV`.

```powershell
$env:ROOT = "D:/Codes/Dongguk_University/2026-da-al-g"
$env:PAPER_JEV = "C:/Users/colin_laptop/orca/workspaces/2026-da-al-g/jev-followup/paper_jev"
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" prepare --db "$env:ROOT/data/data_graph/daalgi.db" --eval-set "$env:ROOT/paper/data/eval_set_v3.json"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" judge --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" aggregate --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
```

The source `.env` files are read only by the runner; keys are neither printed nor copied. API responses, usage, and latency are cached under `cache/`; rerunning `judge` reuses completed calls. `aggregate` makes no API calls.

Preparation uses seed `20261017`, all 80 positive guide slide pages, and 80 negative draws. The 77 unlinked pages are all included once, then three are drawn again to balance the sample. Candidates use stored embeddings and BM25 with the production 0.6 cosine / 0.4 BM25 blend. Every judge sees the same top 10 candidates per slide; top 20 is also measured for recall. There are 36 approved source selections with 96 target article ranges; edge metrics score each source-selection/article target, and aggregate slide probabilities by maximum within the selected pages. Only the human-approved targets are positive, so gold is incomplete.

## Rebuild tables from the response cache

From `ROOT/back/`:

```powershell
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" aggregate
```

## Downstream retrieval

This creates six disposable copies of the source DB under ignored `paper_jev/runtime/` and replaces `document_links` in those copies. `jev_choice` is used for the full-RAGAS comparison; the five retrieval-only runs below match the main table. The original DB is never modified. The copied evaluator and usage tracker keep results and all downstream chat/embedding usage under `experiments/runs/`.

```powershell
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" build-dbs --db "$env:ROOT/data/data_graph/daalgi.db"
$variants = @("gold", "none", "jev_pair", "llm_pair", "cascade")
foreach ($variant in $variants) {
    $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\', '/'
    $env:DATABASE_URL = "sqlite:///$dbPath"
    $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/downstream/$variant/openai_usage.jsonl"
    uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --variant proposed --repeat-tag r1 --run-id "downstream_${variant}_r1" --skip-ragas --resume --output-dir "$env:PAPER_JEV/experiments/runs/downstream/$variant"
}
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" aggregate
```

The evaluator copy is the source checkout's `ragas_eval.py`; `back/scripts/ragas_eval.py` is not edited.

## Full RAGAS on graph cases

The edge results select `jev_choice` as the best-F1 Jev judge and `llm_pair` as the best-F1 LLM judge. The optional full-RAGAS run evaluates those link sets and gold on the 20 graph cases, one repeat each. The tracker includes asynchronous chat and embedding calls in the USD 15 OpenAI cap.

```powershell
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
$variants = @("gold", "jev_choice", "llm_pair")
foreach ($variant in $variants) {
    $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\', '/'
    $env:DATABASE_URL = "sqlite:///$dbPath"
    $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/full_ragas/$variant/openai_usage.jsonl"
    uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --cases graph --variant proposed --repeat-tag r1 --run-id "full_ragas_${variant}_r1" --resume --output-dir "$env:PAPER_JEV/experiments/runs/full_ragas/$variant"
}
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" aggregate
```

The optional gpt-4o-mini comparison is not run.

## Prices and caps

GPT-5.6 Luna pricing is USD 0.20/M input, USD 0.02/M cached input, and USD 1.20/M output ([official model pricing](https://developers.openai.com/api/docs/models/gpt-5.6-luna)). Jev input is USD 0.042/M and output is free ([TypeSafe API documentation](https://docs.typesafe.ai/llms.txt)). Downstream `text-embedding-3-small` input is USD 0.02/M ([official model pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small)); full RAGAS `text-embedding-3-large` input is USD 0.13/M ([official model pricing](https://developers.openai.com/api/docs/models/text-embedding-3-large)). The runner and downstream tracker stop at cumulative caps of USD 15 OpenAI and USD 5 Jev.

## Follow-up: candidate recall and judge-only quality

The follow-up extends the same fixed 160-slide sample and stored embeddings with hybrid K=50/100 candidates, regex-extracted explicit article/appendix references, and the union of those rules with hybrid K. A mentioned regulation filename maps to its article units. `summary/main_table.md` keeps the original tables and adds candidate recall/counts by setting, judge metrics restricted to covered gold edges, K=50/100 Jev and cascade metrics/costs, and large-K downstream evaluation status. `main_table.csv` contains the same rows by section.

Jev pair questions are split into ten-candidate requests because one 50-candidate request exceeded Jev's input limit. K=50 and K=100 Jev pair runs reuse cached scores from the previous smaller K; independent pair questions preserve the same probabilities. Jev choice at K=100 is split into two 50-candidate choices per slide after a full K=100 choice exceeded the input limit; returned per-option probabilities are keyed back to candidate article IDs. Three repeats were requested for Jev and cascade; K=50 completed all three, while K=100 has one complete repeat because the API returned HTTP 402 (no organization credits) before repeat two. K=100 incomplete rows are marked and excluded from best-link selection. Cascade uses the same inclusive 0.20-0.80 Jev uncertainty band. The K=100 `llm_pair` attempt stopped after 302/800 batches when OpenAI returned HTTP 429 `insufficient_quota`; the table reports its projected full-run cost and actual partial usage, with no measured K=100 metric. The best Jev downstream attempt failed on its first OpenAI embedding request with HTTP 429; the cascade run was skipped. The completed K=50 Jev judge and cascade results determine the best link sets.

The K=100 `llm_pair` run uses 20-pair request batches and a one-token-per-serialized-character pre-call estimate. The original K=10 calls measured 0.554 input tokens per serialized character; the larger guard rate and 25% projected-cost margin keep the request stream inside the cumulative OpenAI cap.

Run from `ROOT/back/`; source database, evaluation set, and env files remain read-only. The following writes only under this worktree's `paper_jev/`:

```powershell
$env:ROOT = "D:/Codes/Dongguk_University/2026-da-al-g"
$env:PAPER_JEV = "C:/Users/colin_laptop/orca/workspaces/2026-da-al-g/jev-followup/paper_jev"
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" prepare --db "$env:ROOT/data/data_graph/daalgi.db" --eval-set "$env:ROOT/paper/data/eval_set_v3.json"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_experiment.py" aggregate
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" candidate-stats
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" judge --settings hybrid_50 hybrid_100 --judges jev_pair jev_choice cascade --repeats r1 r2 r3 --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" judge --settings hybrid_100 --judges llm_pair --repeats r1 --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" aggregate
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" build-dbs --db "$env:ROOT/data/data_graph/daalgi.db"
$variants = @("best_jev", "best_cascade")
foreach ($variant in $variants) {
    $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\', '/'
    $env:DATABASE_URL = "sqlite:///$dbPath"
    $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/downstream/$variant/openai_usage.jsonl"
    uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --variant proposed --skip-ragas --repeat-tag r1 --run-id "downstream_${variant}_r1" --resume --output-dir "$env:PAPER_JEV/experiments/runs/downstream/$variant"
}
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" aggregate
```

The OpenAI and Jev budget guards include the original experiment spend, and OpenAI also includes prior downstream/RAGAS usage logs. Follow-up response caches are under `cache/followup/`; offline aggregation makes no API calls.
