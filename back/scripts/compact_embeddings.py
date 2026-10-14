from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import struct
from pathlib import Path

from sqlalchemy.engine import make_url

from app.config import Settings

BATCH_SIZE = 500


def _float32_blob(value: bytes | bytearray | memoryview | str) -> tuple[bytes, bool]:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        try:
            vector = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            if len(raw) % 4:
                raise ValueError("Vector blob size must be divisible by 4")
            return raw, True
        if vector is None:
            return b"", False
        if not isinstance(vector, list):
            if len(raw) % 4:
                raise ValueError("Embedding must be a JSON array")
            return raw, True
    else:
        vector = json.loads(value)
    if vector is None:
        return b"", False
    if not isinstance(vector, list):
        raise ValueError("Embedding must be a JSON array")
    return struct.pack("<" + "f" * len(vector), *(float(item) for item in vector)), False


def compact_embeddings(database_path: Path, dry_run: bool = False) -> tuple[int, int, int]:
    database_path = database_path.expanduser().resolve()
    if not database_path.is_file():
        raise FileNotFoundError(database_path)
    before = database_path.stat().st_size
    if shutil.disk_usage(database_path.parent).free < before:
        raise RuntimeError(f"Need at least {before:,} bytes free for VACUUM")
    print(f"before: {before:,} bytes")

    connection = sqlite3.connect(database_path)
    updates = 0
    try:
        last_rowid = 0
        while rows := connection.execute(
            "SELECT rowid, id, embedding_vector, embedding_json FROM fragments "
            "WHERE rowid > ? AND (embedding_vector IS NOT NULL OR embedding_json IS NOT NULL) "
            "ORDER BY rowid LIMIT ?",
            (last_rowid, BATCH_SIZE),
        ).fetchall():
            for rowid, fragment_id, vector, embedding_json in rows:
                last_rowid = rowid
                source = vector if vector is not None else embedding_json
                blob, already_compact = _float32_blob(source)
                if not blob and embedding_json is not None and vector is not None:
                    blob, already_compact = _float32_blob(embedding_json)
                if already_compact and embedding_json is None:
                    continue
                updates += 1
                if not dry_run:
                    connection.execute(
                        "UPDATE fragments SET embedding_vector = ?, embedding_json = NULL WHERE id = ?",
                        (blob, fragment_id),
                    )
            if not dry_run:
                connection.commit()

        print(f"vectors to update: {updates:,}")
        if dry_run:
            print(f"after (dry-run): {before:,} bytes")
            return before, before, updates

        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()

    after = database_path.stat().st_size
    print(f"after: {after:,} bytes")
    return before, after, updates


def main() -> None:
    parser = argparse.ArgumentParser(description="Store SQLite fragment embeddings as float32 blobs.")
    parser.add_argument("--db", type=Path, help="SQLite database path (defaults to the configured URL)")
    parser.add_argument("--dry-run", action="store_true", help="Count rows without changing the database")
    args = parser.parse_args()

    if args.db:
        database_path = args.db
    else:
        url = make_url(Settings().database_url)
        if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
            parser.error("configured database URL must point to a SQLite file")
        database_path = Path(url.database)
    compact_embeddings(database_path, args.dry_run)


if __name__ == "__main__":
    main()
