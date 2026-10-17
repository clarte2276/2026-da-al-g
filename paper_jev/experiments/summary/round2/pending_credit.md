# Work pending new API credits

No API was called to prepare this appendix. Costs below are planning estimates from the recorded cache usage and price rates in `README.md`; actual calls vary with cache hits, response size, and provider pricing. K=100 estimates use its one completed repeat; K=50 downstream estimates use K=10 downstream calls as a proxy.

| Pending work | Projected additional OpenAI cost | Projected additional Jev cost | Basis |
|---|---:|---:|---|
| K=10 downstream retrieval repeats r2/r3 for gold, none, jev_pair, llm_pair, cascade | $0.164374 | $0.000000 | 2 × sum of cached r1 costs |
| K=10 full RAGAS graph repeats r2/r3 for gold, jev_choice, llm_pair | $1.755157 | $0.000000 | 2 × cached full-RAGAS cost |
| K=50 best_jev and best_cascade downstream, three repeats each | $0.051079 | $0.000000 | 3 × K=10 Jev pair and cascade retrieval costs, proxy only |
| K=100 Jev pair/choice and cascade repeats r2/r3 | $0.355504 | $1.097983 | 2 × observed K=100 per-repeat incremental costs by provider |
| K=100 LLM pair: finish partial r1 and run r2/r3 | $6.292839 | $0.000000 | 3 × projected full-repeat cost minus USD 0.969278 already spent on partial r1 |
| **Total estimated new credit** | **$8.618952** | **$1.097983** | Does not include local runtime or downstream K=50 uncertainty |

## Exact commands

Run from `ROOT/back/` after credits are available. The commands deliberately use new repeat tags and output directories so r1 cache/results remain auditable.

### K=10 retrieval-only downstream r2/r3

```powershell
$env:ROOT = "D:/Codes/Dongguk_University/2026-da-al-g"
$env:PAPER_JEV = "C:/Users/colin_laptop/orca/workspaces/2026-da-al-g/jev-r2an/paper_jev"
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
$variants = @("gold", "none", "jev_pair", "llm_pair", "cascade")
foreach ($repeat in @("r2", "r3")) {
    foreach ($variant in $variants) {
        $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\', '/'
        $env:DATABASE_URL = "sqlite:///$dbPath"
        $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat/openai_usage.jsonl"
        uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --variant proposed --skip-ragas --repeat-tag $repeat --run-id "downstream_${variant}_${repeat}" --resume --output-dir "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat"
    }
}
```

### K=10 full RAGAS graph repeats r2/r3

```powershell
$variants = @("gold", "jev_choice", "llm_pair")
foreach ($repeat in @("r2", "r3")) {
    foreach ($variant in $variants) {
        $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\', '/'
        $env:DATABASE_URL = "sqlite:///$dbPath"
        $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/full_ragas/$variant/$repeat/openai_usage.jsonl"
        uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --cases graph --variant proposed --repeat-tag $repeat --run-id "full_ragas_${variant}_${repeat}" --resume --output-dir "$env:PAPER_JEV/experiments/runs/full_ragas/$variant/$repeat"
    }
}
```

### K=50 best-link downstream r1/r2/r3

```powershell
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" build-dbs --db "$env:ROOT/data/data_graph/daalgi.db"
$variants = @("best_jev", "best_cascade")
foreach ($repeat in @("r1", "r2", "r3")) {
    foreach ($variant in $variants) {
        $dbPath = (Resolve-Path "$env:PAPER_JEV/runtime/links_$variant.sqlite").Path -replace '\\', '/'
        $env:DATABASE_URL = "sqlite:///$dbPath"
        $env:PAPER_JEV_USAGE_LOG = "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat/openai_usage.jsonl"
        uv run --locked --extra eval --env-file "$env:ROOT/back/.env" python "$env:PAPER_JEV/experiments/run_ragas_eval.py" --dataset "$env:PAPER_JEV/experiments/data/eval_set_v3.json" --variant proposed --skip-ragas --repeat-tag $repeat --run-id "downstream_${variant}_${repeat}" --resume --output-dir "$env:PAPER_JEV/experiments/runs/downstream/$variant/$repeat"
    }
}
```

### Finish K=100 Jev/cascade repeats and K=100 LLM pair

```powershell
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" judge --settings hybrid_100 --judges jev_pair jev_choice cascade --repeats r2 r3 --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" judge --settings hybrid_100 --judges llm_pair --repeats r1 r2 r3 --openai-env "$env:ROOT/back/.env" --jev-env "$env:ROOT/paper_jev/.env"
uv run --locked --extra eval python "$env:PAPER_JEV/experiments/run_followup.py" aggregate
```

The LLM projection assumes completing all three K=100 repeats; r1 is currently partial (302/800 calls). The K=100 Jev and cascade projection is incremental over cached lower-K scores. The K=50 downstream projection is the least certain because its link set was never evaluated downstream.
