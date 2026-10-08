import json
import sqlite3
from pathlib import Path

from scripts.rename_doc_folders import run


def test_apply_moves_folders_rewrites_only_path_segments_and_is_idempotent(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    for base_name in ("data_raw", "data_pdf"):
        base = data_root / base_name
        for folder, filename in (
            ("규정", "rule.txt"),
            ("길라잡이", "guide.pptx"),
            ("근무계획표", "plan.xlsx"),
            ("길라잡이_png_with links", "linked.pptx"),
        ):
            (base / folder).mkdir(parents=True)
            (base / folder / filename).write_text(filename, encoding="utf-8")

    database_path = tmp_path / "paths.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            "CREATE TABLE records (path TEXT, content TEXT, payload JSON);"
            "CREATE TABLE other (note TEXT);"
        )
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            (
                r"D:\repo\data\data_raw\규정\rule.hwp",
                "본문에서 규정과 길라잡이를 언급한다.",
                json.dumps({"source": r"data_pdf\길라잡이\guide.pptx"}, ensure_ascii=False),
            ),
        )
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            (
                "data_raw/근무계획표/plan.xlsx",
                "",
                r'{"source":"data_pdf\/길라잡이_png_with links\/linked.pptx"}',
            ),
        )
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?)",
            ("data_raw/archive/규정/rule.txt", "data_raw/규정집", None),
        )
        connection.execute("INSERT INTO other VALUES (?)", ("data_pdf/규정/other.hwpx",))

    first = run(data_root, database_path, apply=True)

    assert first["moved"] == 8
    assert first["updated"] > 0
    assert not (data_root / "data_raw" / "규정").exists()
    assert (data_root / "data_raw" / "서울교통공사 사규" / "rule.txt").is_file()
    assert (data_root / "data_raw" / "6호선 매뉴얼" / "guide.pptx").is_file()
    assert (data_root / "data_raw" / "기타 문서" / "근무계획표" / "plan.xlsx").is_file()
    assert (data_root / "data_pdf" / "6호선 매뉴얼" / "guide.pptx").is_file()
    assert (data_root / "data_pdf" / "기타 문서" / "길라잡이_png_with links" / "linked.pptx").is_file()

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute("SELECT path, content, payload FROM records ORDER BY rowid").fetchall()
        other_note = connection.execute("SELECT note FROM other").fetchone()[0]
    assert rows[0][0] == r"D:\repo\data\data_raw\서울교통공사 사규\rule.hwp"
    assert rows[0][1] == "본문에서 규정과 길라잡이를 언급한다."
    assert json.loads(rows[0][2])["source"] == r"data_pdf\6호선 매뉴얼\guide.pptx"
    assert rows[1][0] == "data_raw/기타 문서/근무계획표/plan.xlsx"
    assert json.loads(rows[1][2])["source"] == "data_pdf/기타 문서/길라잡이_png_with links/linked.pptx"
    assert rows[2][0] == "data_raw/archive/규정/rule.txt"
    assert rows[2][1] == "data_raw/규정집"
    assert other_note == "data_pdf/서울교통공사 사규/other.hwpx"

    second = run(data_root, database_path, apply=True)

    assert second == {"moved": 0, "updated": 0}


def test_flattens_pdf_guides_and_reports_missing_sources_without_moving_raw(tmp_path: Path, capsys) -> None:
    data_root = tmp_path / "data"
    raw = data_root / "data_raw"
    (raw / "6호선 매뉴얼").mkdir(parents=True)
    (raw / "6호선 매뉴얼" / "manual.pptx").write_text("raw", encoding="utf-8")
    (raw / "서울교통공사 사규" / "rules").mkdir(parents=True)
    (raw / "기타 문서").mkdir()

    pdf = data_root / "data_pdf"
    (pdf / "길라잡이" / "연결 규정_무").mkdir(parents=True)
    (pdf / "길라잡이" / "연결 규정_유").mkdir(parents=True)
    (pdf / "길라잡이" / "연결 규정_무" / "manual.pdf").write_text("without", encoding="utf-8")
    (pdf / "길라잡이" / "연결 규정_유" / "linked.pdf").write_text("with", encoding="utf-8")
    (pdf / "근무계획표").mkdir(parents=True)
    (pdf / "근무계획표" / "plan.pdf").write_text("plan", encoding="utf-8")

    database_path = tmp_path / "paths.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            "CREATE TABLE documents (id TEXT, filename TEXT, source_path TEXT);"
            "CREATE TABLE document_versions (id TEXT, document_id TEXT, storage_path TEXT);"
        )
        connection.executemany(
            "INSERT INTO documents VALUES (?, ?, ?)",
            [
                ("raw-manual", "manual.pptx", r"data_raw\길라잡이\연결 규정_무\manual.pptx"),
                ("raw-missing", "removed.pdf", r"data_raw\길라잡이\연결 규정_유\removed.pdf"),
                ("pdf-manual", "manual.pdf", r"data_pdf\길라잡이\연결 규정_무\manual.pdf"),
                ("pdf-linked", "linked.pdf", r"data_pdf\/길라잡이\/연결 규정_유\/linked.pdf"),
                ("pdf-plan", "plan.pdf", r"data_pdf\근무계획표\plan.pdf"),
            ],
        )
        connection.execute(
            "INSERT INTO document_versions VALUES (?, ?, ?)",
            ("version-missing", "raw-missing", r"data_raw\길라잡이\연결 규정_유\removed.pdf"),
        )

    preview = run(data_root, database_path)
    output = capsys.readouterr().out
    assert preview == {"moved": 0, "updated": 0}
    assert "data_raw/" in output and "no source folders to move" in output
    assert "move " + str(pdf / "길라잡이" / "연결 규정_무") + " -> " + str(pdf / "6호선 매뉴얼") in output
    assert "documents.source_path:" in output and "4 rows" in output
    assert "document id=raw-missing filename=removed.pdf" in output
    assert "document id=raw-missing filename=removed.pdf version id=version-missing" in output
    assert (pdf / "길라잡이" / "연결 규정_무" / "manual.pdf").is_file()

    result = run(data_root, database_path, apply=True)

    assert result["moved"] == 3
    assert (raw / "6호선 매뉴얼" / "manual.pptx").read_text(encoding="utf-8") == "raw"
    assert not (raw / "길라잡이").exists()
    assert (pdf / "6호선 매뉴얼" / "manual.pdf").read_text(encoding="utf-8") == "without"
    assert (pdf / "기타 문서" / "연결 규정_유" / "linked.pdf").read_text(encoding="utf-8") == "with"
    assert (pdf / "기타 문서" / "근무계획표" / "plan.pdf").is_file()
    assert not (pdf / "길라잡이").exists()
    assert result["updated"] > 0
    with sqlite3.connect(database_path) as connection:
        raw_manual = connection.execute(
            "SELECT source_path FROM documents WHERE id='raw-manual'"
        ).fetchone()[0]
        raw_missing = connection.execute(
            "SELECT source_path FROM documents WHERE id='raw-missing'"
        ).fetchone()[0]
        pdf_manual = connection.execute(
            "SELECT source_path FROM documents WHERE id='pdf-manual'"
        ).fetchone()[0]
        pdf_linked = connection.execute(
            "SELECT source_path FROM documents WHERE id='pdf-linked'"
        ).fetchone()[0]
    assert raw_manual == r"data_raw\6호선 매뉴얼\manual.pptx"
    assert raw_missing == r"data_raw\길라잡이\연결 규정_유\removed.pdf"
    assert pdf_manual == r"data_pdf\6호선 매뉴얼\manual.pdf"
    assert pdf_linked == r"data_pdf\/기타 문서\/연결 규정_유\/linked.pdf"
