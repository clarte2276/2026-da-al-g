import os
import re
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "daalgi-knowledge-api"
    database_url: str = "sqlite:///./runtime/daalgi.db"
    storage_root: Path = Path("./runtime/storage")
    pptx_pdf_converter: str | None = None
    allow_approximate_pdf_fallback: bool = False
    embedding_provider: str = "auto"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 64
    openai_api_key: str | None = None
    llm_model: str = "gpt-5.6-luna"
    max_upload_bytes: int = 524_288_000
    default_graph_hops: int = 2
    local_document_roots: str = ""
    local_scan_limit: int = 10_000
    enable_registration: bool = True
    enable_test_account: bool = True
    auth_session_hours: int = 24
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_display_name: str = "관리자"
    cors_origins: str = "*"

    # Load the backend-local file first, then the repository-root file. This
    # lets `cd back; uv run ...` use the root `.env` without copying secrets.
    model_config = SettingsConfigDict(
        env_file=(".env", PROJECT_ROOT_ENV), env_prefix="", extra="ignore"
    )

    def prepare_directories(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def document_roots(self) -> list[Path]:
        """Return configured local roots, split with the host OS path separator."""
        if not self.local_document_roots.strip():
            return []

        configured_roots = self.local_document_roots.strip()
        # A Windows drive letter contains ':' and would otherwise be split as
        # a POSIX path-list separator when the backend runs under WSL.
        if os.pathsep == ":" and re.fullmatch(r"[A-Za-z]:[\\/].*", configured_roots):
            raw_roots = [configured_roots]
        else:
            raw_roots = configured_roots.split(os.pathsep)

        roots: list[Path] = []
        for raw_root in raw_roots:
            raw_root = raw_root.strip()
            if raw_root:
                windows_path = re.fullmatch(r"([A-Za-z]):[\\/](.*)", raw_root)
                if windows_path and os.name != "nt":
                    drive = windows_path.group(1).lower()
                    rest = windows_path.group(2).replace("\\", "/")
                    raw_root = f"/mnt/{drive}/{rest}"
                roots.append(Path(raw_root).expanduser().resolve())
        return roots


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.prepare_directories()
    return settings
