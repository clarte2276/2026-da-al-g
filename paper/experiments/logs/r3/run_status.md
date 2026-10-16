# Repeat r3 status

## Completed

- proposed_r3: full evaluation completed with 37 dataset cases, 5 general cases, and 10 out-of-scope cases; ragas_skipped=false.
- Graph category means (20/20): retrieval Recall 0.8417, Precision 0.7658; RAGAS Context Precision 0.9153, Faithfulness 0.9832, Answer Correctness 0.7525.
- Wall time: 2686.7 seconds (44m 46.7s). Final result: paper/experiments/results/proposed_r3.json.
- The proposed log includes an initial dependency setup failure, then a successful full run via --resume (no earlier checkpoint existed, so it ran fresh); the key was scrubbed from all output before writing logs.

## Partial and blocked

- link_all_r3: 31/37 dataset cases completed (12 doc, 19/20 graph). Completed graph means: Recall 0.8596, Precision 0.7509; Context Precision 0.8939, Faithfulness 0.9776, Answer Correctness 0.7862.
- Wall time: 2224.1 seconds (37m 04.1s). It failed on OpenAI 429 insufficient_quota / credit_balance_exhausted before writing a final result JSON.
- Missing cases: graph_front_safety_brake_rescue, wind_threshold_report, fog_station_duties, earthquake_warning_threshold, earthquake_control_initial_stop, and earthquake_driver_speed.
- Resume checkpoint: paper/experiments/logs/r3/checkpoints/link_all_r3.json. Once API credits are restored, copy it to paper/experiments/results/checkpoints/link_all_r3.json before using --resume.
- The coordinator confirmed that credits are exhausted and directed this worker to make no more OpenAI calls. hybrid_rerank_r3, hybrid_r3, dense_r3, and bm25_r3 were not started.

## Commands to resume

Run from back/ after restoring the checkpoint and API quota. Load the .env file without copying it; set the database and storage overrides from the task specification in the command process.

~~~powershell
$env:DATABASE_URL = 'sqlite:///D:/Codes/Dongguk_University/2026-da-al-g/data/data_graph/daalgi.db'
$env:STORAGE_ROOT = 'D:/Codes/Dongguk_University/2026-da-al-g/back/runtime/storage'
$env:PYTHONPATH = '.'
$env:PYTHONIOENCODING = 'utf-8'
$dotenv = 'D:/Codes/Dongguk_University/2026-da-al-g/back/.env'

uv run --env-file $dotenv --extra dev --extra hwp --extra eval python scripts/ragas_eval.py --dataset ../paper/data/eval_set_v3.json --variant link_all --repeat-tag r3 --run-id link_all_r3 --output-dir ../paper/experiments/results --resume
uv run --env-file $dotenv --extra dev --extra hwp --extra eval python scripts/ragas_eval.py --dataset ../paper/data/eval_set_v3.json --variant hybrid_rerank --repeat-tag r3 --run-id hybrid_rerank_r3 --output-dir ../paper/experiments/results
uv run --env-file $dotenv --extra dev --extra hwp --extra eval python scripts/ragas_eval.py --dataset ../paper/data/eval_set_v3.json --variant hybrid --repeat-tag r3 --run-id hybrid_r3 --output-dir ../paper/experiments/results
uv run --env-file $dotenv --extra dev --extra hwp --extra eval python scripts/ragas_eval.py --dataset ../paper/data/eval_set_v3.json --variant dense --repeat-tag r3 --run-id dense_r3 --output-dir ../paper/experiments/results
uv run --env-file $dotenv --extra dev --extra hwp --extra eval python scripts/ragas_eval.py --dataset ../paper/data/eval_set_v3.json --variant bm25 --repeat-tag r3 --run-id bm25_r3 --output-dir ../paper/experiments/results
~~~

For proposed_r3, the full dataset, general cases, and out-of-scope cases were explicitly selected. Results and checkpoints were normalized under paper/experiments/results/ and paper/experiments/logs/r3/checkpoints/ respectively; logs were checked for the exact API key and common sk- key patterns, with no matches.

