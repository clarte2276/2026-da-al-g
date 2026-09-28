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
        path = self.path(root_id, relative_path)
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise FileNotFoundError(path)
        return LocalFile(root=root, path=path)

    def path(self, root_id: str, relative_path: str = "") -> Path:
        root = self.root(root_id).path
        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("A document path must stay within its configured root")
        current = root
        for part in candidate.parts:
            current /= part
            if current.is_symlink():
                raise ValueError("Symbolic links cannot be managed")
        path = (root / candidate).resolve()
        if not path.is_relative_to(root):
            raise ValueError("The requested path is outside the configured document root")
        return path

    def folders(self, root_id: str) -> list[str]:
        root = self.root(root_id).path
        if not root.is_dir():
            return []
        return sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_dir() and not path.is_symlink() and path.resolve().is_relative_to(root)
        )

    def create_folder(self, root_id: str, relative_path: str) -> str:
        path = self.path(root_id, relative_path)
        if path == self.root(root_id).path or path.exists():
            raise FileExistsError(path)
        if not path.parent.is_dir():
            raise FileNotFoundError(path.parent)
        path.mkdir()
        return relative_path

    def delete_empty_folder(self, root_id: str, relative_path: str) -> None:
        path = self.path(root_id, relative_path)
        if path == self.root(root_id).path:
            raise ValueError("The document root cannot be deleted")
        path.rmdir()

    def delete_file(self, root_id: str, relative_path: str) -> None:
        self.resolve(root_id, relative_path).path.unlink()

    def move(self, root_id: str, source: str, destination: str) -> tuple[Path, Path]:
        old = self.path(root_id, source)
        new = self.path(root_id, destination)
        root = self.root(root_id).path
        if old == root or new == root or not old.exists():
            raise ValueError("A document or folder must be selected")
        if old.is_symlink() or (not old.is_dir() and old.suffix.lower() not in SUPPORTED_SUFFIXES):
            raise ValueError("Unsupported document path")
        if old.is_file() and new.suffix.lower() != old.suffix.lower():
            raise ValueError("A document's file extension cannot be changed")
        if old.is_dir() and new.is_relative_to(old):
            raise ValueError("A folder cannot be moved into itself")
        if new.exists():
            raise FileExistsError(new)
        if not new.parent.is_dir():
            raise FileNotFoundError(new.parent)
        old.rename(new)
        return old, new

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
                if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                    continue
                relative_path = path.relative_to(root.path).as_posix()
                if normalized_query and normalized_query not in relative_path.casefold():
                    continue
                results.append(LocalFile(root=root, path=path))
        results.sort(key=lambda item: (item.root.id, item.relative_path.casefold()))
        return results[: limit or self.settings.local_scan_limit]
