from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _resolve_path(raw: str, *, base_dir: Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    telegram_allowed_chat_ids: set[int]
    openai_api_key: str | None
    model_backend: str
    openai_model: str
    codex_bin: str
    gemini_model: str
    gemini_bin: str
    db_path: Path
    workspace: Path
    skills_dir: Path
    execution_mode: str
    max_steps: int
    command_timeout: int

    @classmethod
    def from_env(cls) -> "Settings":
        base_dir = _resolve_path(
            os.getenv("OPENCLAWISH_BASE_DIR", "."),
            base_dir=Path.cwd(),
        )
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

        chat_ids = {
            int(value)
            for value in _split_csv(os.getenv("TELEGRAM_ALLOWED_CHAT_IDS"))
        }
        if not chat_ids:
            raise RuntimeError("TELEGRAM_ALLOWED_CHAT_IDS must include at least one chat id")

        db_path = _resolve_path(
            os.getenv("OPENCLAWISH_DB_PATH", "./data/openclawish.db"),
            base_dir=base_dir,
        )
        workspace = _resolve_path(
            os.getenv("OPENCLAWISH_WORKSPACE", "."),
            base_dir=base_dir,
        )
        skills_dir = _resolve_path(
            os.getenv("OPENCLAWISH_SKILLS_DIR", "./skills"),
            base_dir=base_dir,
        )
        execution_mode = os.getenv("OPENCLAWISH_EXECUTION_MODE", "workspace").strip().lower()
        if execution_mode not in {"workspace", "system"}:
            raise RuntimeError("OPENCLAWISH_EXECUTION_MODE must be 'workspace' or 'system'")
        model_backend = os.getenv("OPENCLAWISH_MODEL_BACKEND", "codex_auth").strip().lower()
        if model_backend not in {"codex_auth", "gemini_auth", "api_key", "fallback"}:
            raise RuntimeError("OPENCLAWISH_MODEL_BACKEND must be codex_auth, gemini_auth, api_key, or fallback")
        return cls(
            telegram_bot_token=token,
            telegram_allowed_chat_ids=chat_ids,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_backend=model_backend,
            openai_model=os.getenv("OPENAI_MODEL", "").strip(),
            codex_bin=os.getenv("OPENCLAWISH_CODEX_BIN", "codex").strip() or "codex",
            gemini_model=os.getenv("GEMINI_MODEL", "").strip(),
            gemini_bin=os.getenv("OPENCLAWISH_GEMINI_BIN", "gemini").strip() or "gemini",
            db_path=db_path,
            workspace=workspace,
            skills_dir=skills_dir,
            execution_mode=execution_mode,
            max_steps=int(os.getenv("OPENCLAWISH_MAX_STEPS", "5")),
            command_timeout=int(os.getenv("OPENCLAWISH_COMMAND_TIMEOUT", "120")),
        )
