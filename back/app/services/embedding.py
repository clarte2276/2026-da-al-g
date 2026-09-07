from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from typing import Protocol

from ..config import Settings


class EmbeddingProvider(Protocol):
    name: str
    model: str
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbeddingProvider:
    """Deterministic offline embedding used for local smoke tests."""

    name = "hash"

    def __init__(self, dimensions: int = 1536, model: str = "hash-v1") -> None:
        self.dimensions = dimensions
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[가-힣A-Za-z0-9_]+", text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[index] += sign
        norm = sum(value * value for value in vector) ** 0.5
        return [value / norm for value in vector] if norm else vector


class OpenAIEmbeddingProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    requested = settings.embedding_provider.lower()
    if requested in {"openai", "auto"} and settings.openai_api_key:
        try:
            return OpenAIEmbeddingProvider(
                api_key=settings.openai_api_key,
                model=settings.embedding_model,
                dimensions=settings.embedding_dimensions,
            )
        except ImportError:
            if requested == "openai":
                raise
    if requested == "openai" and not settings.openai_api_key:
        raise RuntimeError("EMBEDDING_PROVIDER=openai requires OPENAI_API_KEY")
    return HashEmbeddingProvider(dimensions=settings.embedding_dimensions)


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    if not left_values or not right_values or len(left_values) != len(right_values):
        return 0.0
    dot = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = sum(value * value for value in left_values) ** 0.5
    right_norm = sum(value * value for value in right_values) ** 0.5
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)

