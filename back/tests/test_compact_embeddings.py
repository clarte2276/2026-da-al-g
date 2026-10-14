import sqlite3
import struct

from scripts.compact_embeddings import compact_embeddings


def test_compact_embeddings_converts_and_is_idempotent(tmp_path) -> None:
    database_path = tmp_path / "vectors.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE fragments (id TEXT PRIMARY KEY, embedding_vector, embedding_json)"
        )
        connection.executemany(
            "INSERT INTO fragments VALUES (?, ?, ?)",
            [
                ("vector-json", "[1,2.5]", "[9,9]"),
                ("json-fallback", None, "[3,4]"),
                ("no-vector", "null", "null"),
                ("already-compact", struct.pack("<2f", 5, 6), None),
            ],
        )

    _, after_first, changed = compact_embeddings(database_path)
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT id, embedding_vector, embedding_json FROM fragments ORDER BY id"
        ).fetchall()
    assert changed == 3
    assert all(row[2] is None for row in rows)
    assert rows[0][1] == struct.pack("<2f", 5, 6)
    assert rows[1][1] == struct.pack("<2f", 3, 4)
    assert rows[2][1] == b""
    assert rows[3][1] == struct.pack("<2f", 1, 2.5)

    _, after_second, changed = compact_embeddings(database_path)
    assert changed == 0
    assert after_second == after_first
