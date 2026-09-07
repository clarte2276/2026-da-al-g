from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args=_connect_args(settings.database_url),
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    from . import models  # noqa: F401

    if engine.dialect.name == "postgresql":
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "PostgreSQL requires the pgvector extension. "
                "Run migrations/001_pgvector.sql with a database administrator."
            ) from exc
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_compat_columns()


def _ensure_sqlite_compat_columns() -> None:
    """Keep local development databases usable after additive model changes."""
    if engine.dialect.name != "sqlite":
        return
    additions = {
        "fragments": {"embedding_vector": "JSON"},
        "knowledge_edges": {
            "source_anchor_json": "JSON",
            "target_anchor_json": "JSON",
        },
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in additions.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.exec_driver_sql(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
