"""Align local document folders and SQLite paths with the current data layout."""

import argparse
import re
import sqlite3
from pathlib import Path

RULES = "서울교통공사 사규"
MANUAL = "6호선 매뉴얼"
OTHER = "기타 문서"
RULE_FOLDER = "규정"
GUIDE_FOLDER = "길라잡이"
GUIDE_WITH = "연결 규정_유"
GUIDE_WITHOUT = "연결 규정_무"
MOVED_FOLDERS = ("근무계획표", "길라잡이_png_with links")
ROOT_NAMES = ("data_raw", "data_pdf")
SEPARATOR = r"(?:\\{1,2}/?|\\?/)"
PATH_SEGMENT = re.compile(
    r"(?<!\w)(?P<root>data_raw|data_pdf)(?P<separator>" + SEPARATOR + r")"
    r"(?P<name>규정|길라잡이_png_with links|근무계획표|길라잡이)"
    r"(?:(?P<child_separator>" + SEPARATOR + r")(?:"
    r"(?P<child>연결 규정_무|연결 규정_유)))?"
    r"(?=$|" + SEPARATOR + r")"
)
PATH_REFERENCE = re.compile(
    r"(?<!\w)(?P<root>data_raw|data_pdf)(?:" + SEPARATOR + r")"
    r"(?P<relative>[^\"'\r\n]*)"
)


def replace_path_segments(value: str | None) -> str | None:
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        root, separator, name = match.group("root", "separator", "name")
        child = match.group("child")
        if name == RULE_FOLDER:
            return f"{root}{separator}{RULES}"
        if child == GUIDE_WITH:
            if root == "data_raw":
                return match.group(0)
            return f"{root}{separator}{OTHER}{match.group('child_separator')}{child}"
        if name == GUIDE_FOLDER:
            return f"{root}{separator}{MANUAL}"
        if name in MOVED_FOLDERS:
            return f"{root}{separator}{OTHER}{separator}{name}"
        return f"{root}{separator}{MANUAL}"

    return PATH_SEGMENT.sub(replace, value)


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _path_predicate(column: str) -> str:
    roots = " OR ".join(f"instr({column}, '{root}') > 0" for root in ROOT_NAMES)
    names = (RULE_FOLDER, GUIDE_FOLDER, *MOVED_FOLDERS, GUIDE_WITH, GUIDE_WITHOUT)
    candidates = " OR ".join(f"instr({column}, '{name}') > 0" for name in names)
    return f"typeof({column}) = 'text' AND ({roots}) AND ({candidates})"


def database_changes(connection: sqlite3.Connection) -> list[tuple[str, str, int]]:
    connection.create_function("rename_doc_path", 1, replace_path_segments)
    changes = []
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    for (table,) in tables:
        for _, column, *_ in connection.execute(f"PRAGMA table_info({_quote(table)})"):
            quoted_column = _quote(column)
            where = _path_predicate(quoted_column)
            count = connection.execute(
                f"SELECT COUNT(*) FROM {_quote(table)} WHERE {where} "
                f"AND rename_doc_path({quoted_column}) != {quoted_column}"
            ).fetchone()[0]
            if count:
                changes.append((table, column, count))
    return changes


def _move_path(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    if destination.exists():
        if not source.is_dir() or not destination.is_dir():
            raise FileExistsError(f"Cannot move {source}: {destination} already exists")
        for child in source.iterdir():
            _move_path(child, destination / child.name)
        source.rmdir()
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
    return True


def _guide_moves(base: Path, data_pdf: bool) -> list[tuple[Path, Path]]:
    guide = base / GUIDE_FOLDER
    if not guide.is_dir():
        return []
    manual = base / MANUAL
    other = base / OTHER
    categories = {GUIDE_WITHOUT, GUIDE_WITH}
    if not any((guide / name).is_dir() for name in categories):
        return [(guide, manual)]

    moves = []
    for child in guide.iterdir():
        if child.name == GUIDE_WITHOUT and child.is_dir():
            moves.append((child, manual))
        elif child.name == GUIDE_WITH and child.is_dir() and data_pdf:
            moves.append((child, other / GUIDE_WITH))
        elif child.name != GUIDE_WITH:
            moves.append((child, manual / child.name))
    return moves


def folder_moves(data_root: Path) -> list[tuple[Path, Path]]:
    moves = []
    for root_name in ROOT_NAMES:
        base = data_root / root_name
        rules = base / RULE_FOLDER
        if rules.exists():
            moves.append((rules, base / RULES))
        moves.extend(_guide_moves(base, data_pdf=root_name == "data_pdf"))
        for name in MOVED_FOLDERS:
            source = base / name
            if source.exists():
                moves.append((source, base / OTHER / name))
    return moves


def _database_identity(table: str, values: dict[str, object], document_names: dict[object, str]) -> str:
    if table == "documents":
        return f"document id={values.get('id')} filename={values.get('filename')}"
    if table == "document_versions":
        document_id = values.get("document_id")
        filename = document_names.get(document_id, "unknown")
        return f"document id={document_id} filename={filename} version id={values.get('id')}"
    identity = values.get("id", values.get("document_id", "unknown"))
    filename = values.get("filename")
    return f"id={identity}" + (f" filename={filename}" if filename is not None else "")


def _path_references(value: str) -> list[tuple[str, str]]:
    references = []
    for match in PATH_REFERENCE.finditer(value):
        relative = match.group("relative").rstrip(" \t,}]")
        relative = relative.replace("\\/", "/").replace("\\\\", "\\")
        if relative:
            references.append((match.group("root"), relative))
    return references


def _path_exists_after_moves(
    data_root: Path, root: str, relative: str, moves: list[tuple[Path, Path]]
) -> bool:
    relative_path = Path(relative.replace("\\", "/"))
    target = data_root / root / relative_path
    if target.exists():
        return True
    for source, destination in moves:
        try:
            remainder = target.relative_to(destination)
        except ValueError:
            continue
        if (source / remainder).exists():
            return True
    return False


def missing_database_paths(
    connection: sqlite3.Connection, data_root: Path, moves: list[tuple[Path, Path]]
) -> list[tuple[str, str, str, str, bool]]:
    document_names = dict(connection.execute("SELECT id, filename FROM documents")) if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'"
    ).fetchone() else {}
    missing = []
    for (table,) in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ):
        columns = [row[1] for row in connection.execute(f"PRAGMA table_info({_quote(table)})")]
        for column in columns:
            quoted_column = _quote(column)
            identity_columns = [name for name in ("id", "document_id", "filename") if name in columns]
            selected = ", ".join([quoted_column, *(_quote(name) for name in identity_columns)])
            predicate = " OR ".join(f"instr({quoted_column}, '{root}') > 0" for root in ROOT_NAMES)
            rows = connection.execute(
                f"SELECT {selected} FROM {_quote(table)} "
                f"WHERE typeof({quoted_column}) = 'text' AND ({predicate})"
            )
            for row in rows:
                value = row[0]
                values = dict(zip(identity_columns, row[1:]))
                identity = _database_identity(table, values, document_names)
                for root, relative in _path_references(replace_path_segments(value)):
                    if not _path_exists_after_moves(data_root, root, relative, moves):
                        raw_guide_yu = root == "data_raw" and relative.replace("\\", "/").startswith(
                            f"{GUIDE_FOLDER}/{GUIDE_WITH}/"
                        )
                        display = root + "/" + relative.replace("\\", "/")
                        missing.append((table, column, identity, display, raw_guide_yu))
    return missing


def _print_plan(
    data_root: Path,
    moves: list[tuple[Path, Path]],
    changes: list[tuple[str, str, int]],
    missing: list[tuple[str, str, str, str, bool]],
) -> None:
    print("Planned folder changes:")
    for root_name in ROOT_NAMES:
        base = data_root / root_name
        print(f"  {base}/: ensure {OTHER}/")
        base_moves = []
        for source, destination in moves:
            try:
                source.relative_to(base)
            except ValueError:
                continue
            base_moves.append((source, destination))
        if base_moves:
            for source, destination in base_moves:
                print(f"  move {source} -> {destination}")
        else:
            print("  no source folders to move")
    print("Planned SQLite replacements:")
    if changes:
        for table, column, count in changes:
            print(f"  {table}.{column}: {count} rows")
    else:
        print("  none")
    print(f"  total: {sum(count for _, _, count in changes)} rows")
    missing_source = [entry for entry in missing if entry[4]]
    other_missing = [entry for entry in missing if not entry[4]]
    print("Missing source (data_raw/길라잡이/연결 규정_유; DB paths left unchanged):")
    if missing_source:
        for table, column, identity, path, _ in missing_source:
            print(f"  {table}.{column}: {identity} -> {path}")
    else:
        print("  none")
    print("Other missing data_raw/data_pdf paths after rewrite:")
    if other_missing:
        for table, column, identity, path, _ in other_missing:
            print(f"  {table}.{column}: {identity} -> {path}")
    else:
        print("  none")


def _apply_database(connection: sqlite3.Connection, changes: list[tuple[str, str, int]]) -> int:
    connection.create_function("rename_doc_path", 1, replace_path_segments)
    updated = 0
    for table, column, _ in changes:
        quoted_column = _quote(column)
        where = _path_predicate(quoted_column)
        cursor = connection.execute(
            f"UPDATE {_quote(table)} SET {quoted_column} = rename_doc_path({quoted_column}) "
            f"WHERE {where} AND rename_doc_path({quoted_column}) != {quoted_column}"
        )
        print(f"  updated {table}.{column}: {cursor.rowcount} rows")
        updated += cursor.rowcount
    return updated


def _remove_empty_old_dirs(data_root: Path) -> None:
    for root_name in ROOT_NAMES:
        old_guide = data_root / root_name / GUIDE_FOLDER
        if old_guide.is_dir():
            try:
                old_guide.rmdir()
            except OSError:
                pass


def run(data_root: Path, database_path: Path, apply: bool = False) -> dict[str, int]:
    moves = folder_moves(data_root)
    mode = "APPLY" if apply else "DRY RUN"
    print(f"Mode: {mode}")
    uri = f"{database_path.resolve().as_uri()}?mode={'rw' if apply else 'ro'}"
    try:
        with sqlite3.connect(uri, uri=True, timeout=1) as connection:
            if apply:
                connection.execute("BEGIN IMMEDIATE")
            changes = database_changes(connection)
            missing = missing_database_paths(connection, data_root, moves)
            _print_plan(data_root, moves, changes, missing)
            moved = 0
            updated = 0
            if apply:
                for source, destination in moves:
                    moved += _move_path(source, destination)
                for root_name in ROOT_NAMES:
                    (data_root / root_name / OTHER).mkdir(parents=True, exist_ok=True)
                _remove_empty_old_dirs(data_root)
                updated = _apply_database(connection, changes)
            print(f"Summary: {moved} folders moved, {updated} database rows updated")
            return {"moved": moved, "updated": updated}
    except sqlite3.OperationalError as exc:
        if "locked" in str(exc).lower() or "busy" in str(exc).lower():
            print(f"Aborted: database is locked; no changes were applied ({exc}).")
            return {"moved": 0, "updated": 0, "aborted": 1}
        raise


def database_path_from_env(repo_root: Path) -> Path:
    env_path = repo_root / "back" / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "DATABASE_URL":
            value = value.strip().strip('"\'')
            if not value.startswith("sqlite:///"):
                raise ValueError(f"Expected a SQLite DATABASE_URL in {env_path}")
            path = Path(value.removeprefix("sqlite:///").split("?", 1)[0])
            return (path if path.is_absolute() else repo_root / "back" / path).resolve()
    raise ValueError(f"DATABASE_URL not found in {env_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="perform the planned folder and database changes")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    result = run(repo_root / "data", database_path_from_env(repo_root), apply=args.apply)
    if result.get("aborted"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
