from __future__ import annotations

import json
import os
import time
from pathlib import Path

INPUT_PRICE, CACHED_INPUT_PRICE, OUTPUT_PRICE = 0.20, 0.02, 1.20
CAP = 15.0
EMBEDDING_PRICES = {"text-embedding-3-small": 0.02, "text-embedding-3-large": 0.13}
EXPERIMENT_ROOT = Path(__file__).resolve().parent


def entry_cost(entry: dict) -> float:
    usage = entry.get("usage") or {}
    prompt = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
    completion = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
    detail = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    cached = min(prompt, int(detail.get("cached_tokens", detail.get("cached_input_tokens", 0)) or 0))
    model = str(entry.get("model", ""))
    input_price = EMBEDDING_PRICES.get(model, INPUT_PRICE) if entry.get("endpoint") == "embeddings" else INPUT_PRICE
    return ((prompt - cached) * input_price + cached * CACHED_INPUT_PRICE + completion * OUTPUT_PRICE) / 1_000_000


def spend_so_far() -> float:
    total = 0.0
    cache = EXPERIMENT_ROOT / "cache"
    if cache.exists():
        for path in cache.rglob("*.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(row, dict) and row.get("_api_call") and row.get("provider") == "openai":
                total += float(row.get("cost_usd", 0))
    runs = EXPERIMENT_ROOT / "runs"
    if runs.exists():
        for path in runs.rglob("openai_usage.jsonl"):
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    total += entry_cost(json.loads(line))
                except (ValueError, TypeError):
                    continue
    return total


def install() -> None:
    import asyncio
    from openai.resources.chat.completions import AsyncCompletions, Completions
    from openai.resources.embeddings import AsyncEmbeddings, Embeddings

    reserved = 0.0
    lock = asyncio.Lock()

    def request_info(args, kwargs, embedding):
        request = kwargs.get("input" if embedding else "messages", args[0] if args else "")
        chars = len(json.dumps(request, ensure_ascii=False))
        model = str(kwargs.get("model", ""))
        input_price = EMBEDDING_PRICES.get(model, INPUT_PRICE) if embedding else INPUT_PRICE
        output_limit = 0 if embedding else int(kwargs.get("max_completion_tokens", kwargs.get("max_tokens", 8192)) or 8192)
        estimate = (chars * 2 * input_price + output_limit * OUTPUT_PRICE) / 1_000_000
        return {
            "log_path": os.environ.get("PAPER_JEV_USAGE_LOG"), "model": model,
            "endpoint": "embeddings" if embedding else "chat.completions",
            "chars": chars, "estimate": estimate,
        }

    def save_usage(info, response, started):
        usage = response.usage.model_dump() if response.usage else {}
        row = {
            "endpoint": info["endpoint"], "model": info["model"], "usage": usage,
            "latency_seconds": time.perf_counter() - started, "request_chars": info["chars"],
        }
        if info["log_path"]:
            path = Path(info["log_path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
        if spend_so_far() > CAP:
            raise RuntimeError("OpenAI reached the USD 15 cap; stopped after recording the request.")
        return response

    def tracked_sync(original, embedding=False):
        def create(self, *args, **kwargs):
            info = request_info(args, kwargs, embedding)
            if spend_so_far() + info["estimate"] + reserved > CAP:
                raise RuntimeError("OpenAI budget guard stopped before a downstream request.")
            started = time.perf_counter()
            response = original(self, *args, **kwargs)
            return save_usage(info, response, started)
        return create

    def tracked_async(original, embedding=False):
        async def create(self, *args, **kwargs):
            nonlocal reserved
            info = request_info(args, kwargs, embedding)
            async with lock:
                if spend_so_far() + reserved + info["estimate"] > CAP:
                    raise RuntimeError("OpenAI budget guard stopped before a downstream request.")
                reserved += info["estimate"]
            started = time.perf_counter()
            try:
                response = await original(self, *args, **kwargs)
                return save_usage(info, response, started)
            finally:
                async with lock:
                    reserved -= info["estimate"]
        return create

    Completions.create = tracked_sync(Completions.create)
    Embeddings.create = tracked_sync(Embeddings.create, embedding=True)
    AsyncCompletions.create = tracked_async(AsyncCompletions.create)
    AsyncEmbeddings.create = tracked_async(AsyncEmbeddings.create, embedding=True)
