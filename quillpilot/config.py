from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def default_data_dir() -> Path:
    root = os.getenv("QUILLPILOT_DATA_DIR")
    if root:
        return Path(root).expanduser().resolve()
    return Path.home() / ".quillpilot"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path
    vector_dir: Path
    llm_api_key: str | None
    llm_base_url: str
    llm_model: str
    llm_timeout_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = default_data_dir()
        return cls(
            data_dir=data_dir,
            database_path=Path(os.getenv("QUILLPILOT_DB", data_dir / "quillpilot.sqlite3")).expanduser(),
            vector_dir=Path(os.getenv("QUILLPILOT_VECTOR_DIR", data_dir / "chroma")).expanduser(),
            llm_api_key=os.getenv("QUILLPILOT_API_KEY") or os.getenv("OPENAI_API_KEY"),
            llm_base_url=os.getenv("QUILLPILOT_BASE_URL", "https://api.openai.com/v1"),
            llm_model=os.getenv("QUILLPILOT_MODEL", "gpt-4o-mini"),
            llm_timeout_seconds=float(os.getenv("QUILLPILOT_LLM_TIMEOUT", "45")),
        )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_dir.mkdir(parents=True, exist_ok=True)
