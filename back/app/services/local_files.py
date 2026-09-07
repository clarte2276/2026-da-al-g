from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..config import Settings

SUPPORTED_SUFFIXES = {".docx", ".hwp", ".hwpx", ".pptx", ".pdf"}


@dataclass(frozen=True, slots=True)
class LocalRoot:
    id: str
    path: Path


@dataclass(frozen=True, slots=True)
class LocalFile:
    root: LocalRoot
    path: Path

    @property
    def relative_path(self) -> str:
        return self.path.relative_to(self.root.path).as_posix()

    @property
    def suffix(self) -> str:
        return self.path.suffix.lower()

    @property
    def modified_at(self) -> datetime:
        return datetime.fromtimestamp(self.path.stat().st_mtime, tz=UTC)


class LocalFileService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def roots(self) -> list[LocalRoot]:
        return [LocalRoot(id=f"root-{index}", path=path) for index, path in enumerate(self.settings.document_roots())]

    def root(self, root_id: str) -> LocalRoot:
        for root in self.roots():
            if root.id == root_id:
                return root
        raise ValueError(f"Unknown local document root: {root_id}")

    def resolve(self, root_id: str, relative_path: str) -> LocalFile:
        root = self.root(root_id)
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise ValueError("A local document path must be relative to its configured root")
        path = (root.path / candidate).resolve()
        try:
            path.relative_to(root.path)
        except ValueError as exc:
            raise ValueError("The requested path is outside the configured document root") from exc
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise FileNotFoundError(path)
        return LocalFile(root=root, path=path)

    def list_files(
        self,
        root_id: str | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> list[LocalFile]:
        roots = [self.root(root_id)] if root_id else self.roots()
        normalized_query = (query or "").strip().casefold()
        results: list[LocalFile] = []
        for root in roots:
            if not root.path.is_dir():
                continue
            for path in root.path.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                    continue
                relative_path = path.relative_to(root.path).as_posix()
                if normalized_query and normalized_query not in relative_path.casefold():
                    continue
                results.append(LocalFile(root=root, path=path))
        results.sort(key=lambda item: (item.root.id, item.relative_path.casefold()))
        return results[: limit or self.settings.local_scan_limit]
