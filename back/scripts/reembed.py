"""Rebuild stored text embeddings without creating duplicate document versions."""

from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Fragment
from app.services.embedding import OpenAIEmbeddingProvider
from app.services.ingestion import _fragment_content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re-embed existing text fragments in place")
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--dimensions", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings(
        database_url=args.database_url or os.getenv("DATABASE_URL", "sqlite:///../data/data_graph/daalgi.db"),
        embedding_model=args.model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_dimensions=args.dimensions or int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
        embedding_batch_size=args.batch_size or int(os.getenv("EMBEDDING_BATCH_SIZE", "64")),
    )
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY가 필요합니다")

    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False}
                           if settings.database_url.startswith("sqlite") else {})
    with Session(engine) as db:
        source_fragments = list(db.scalars(
            select(Fragment)
            .where(Fragment.text.is_not(None))
            .order_by(Fragment.id)
        ))
        pairs = [
            (fragment, text)
            for fragment in source_fragments
            if (text := _fragment_content(fragment)).strip()
        ]
        fragments = [fragment for fragment, _ in pairs]
        texts = [text for _, text in pairs]
        print(f"Fragments: {len(fragments)} | Model: {settings.embedding_model} | Dimensions: {settings.embedding_dimensions}")
        if args.dry_run:
            return

        provider = OpenAIEmbeddingProvider(
            settings.openai_api_key,
            settings.embedding_model,
            settings.embedding_dimensions,
        )
        batch_size = max(settings.embedding_batch_size, 1)
        for start in range(0, len(fragments), batch_size):
            batch = fragments[start:start + batch_size]
            vectors = provider.embed(texts[start:start + batch_size])
            if len(vectors) != len(batch) or any(len(vector) != settings.embedding_dimensions for vector in vectors):
                raise RuntimeError("embedding 응답의 개수 또는 차원이 맞지 않습니다")
            for fragment, vector in zip(batch, vectors, strict=True):
                fragment.embedding_json = vector
                fragment.embedding_vector = vector
                fragment.embedding_model = f"{provider.name}:{provider.model}"
            db.flush()
            print(f"Updated: {min(start + batch_size, len(fragments))}/{len(fragments)}")
        db.commit()


if __name__ == "__main__":
    main()
