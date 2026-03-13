from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Settings


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_startup_checks(settings: Settings) -> list[CheckResult]:
    results = [
        CheckResult(
            "workspace",
            settings.workspace.exists(),
            f"workspace={settings.workspace}",
        ),
    ]
    settings.skills_dir.mkdir(parents=True, exist_ok=True)
    results.append(
        CheckResult(
            "skills_dir",
            settings.skills_dir.exists(),
            f"skills_dir={settings.skills_dir}",
        )
    )

    db_parent = settings.db_path.parent
    db_parent.mkdir(parents=True, exist_ok=True)
    results.append(CheckResult("db_path", db_parent.exists(), f"db_parent={db_parent}"))

    if settings.model_backend == "codex_auth":
        codex_path = shutil.which(settings.codex_bin)
        results.append(
            CheckResult(
                "codex_bin",
                bool(codex_path),
                codex_path or f"{settings.codex_bin} not found on PATH",
            )
        )
        if codex_path:
            status = subprocess.run(
                [settings.codex_bin, "login", "status"],
                cwd=str(settings.workspace),
                capture_output=True,
                text=True,
                timeout=20,
            )
            detail = (status.stdout or status.stderr).strip() or f"exit={status.returncode}"
            results.append(CheckResult("codex_login", status.returncode == 0, detail))

    if settings.model_backend == "gemini_auth":
        gemini_path = shutil.which(settings.gemini_bin)
        results.append(
            CheckResult(
                "gemini_bin",
                bool(gemini_path),
                gemini_path or f"{settings.gemini_bin} not found on PATH",
            )
        )

    if settings.model_backend == "api_key":
        results.append(
            CheckResult(
                "openai_api_key",
                bool(settings.openai_api_key),
                "present" if settings.openai_api_key else "OPENAI_API_KEY is missing",
            )
        )

    return results


def format_check_report(results: list[CheckResult]) -> str:
    lines = []
    for item in results:
        marker = "OK" if item.ok else "FAIL"
        lines.append(f"[{marker}] {item.name}: {item.detail}")
    return "\n".join(lines)


def render_launchagent(settings: Settings, *, python_bin: str, app_bin: str, label: str) -> str:
    envs = {
        "TELEGRAM_BOT_TOKEN": settings.telegram_bot_token,
        "TELEGRAM_ALLOWED_CHAT_IDS": ",".join(str(item) for item in sorted(settings.telegram_allowed_chat_ids)),
        "OPENCLAWISH_MODEL_BACKEND": settings.model_backend,
        "OPENCLAWISH_CODEX_BIN": settings.codex_bin,
        "OPENCLAWISH_GEMINI_BIN": settings.gemini_bin,
        "OPENCLAWISH_DB_PATH": str(settings.db_path),
        "OPENCLAWISH_WORKSPACE": str(settings.workspace),
        "OPENCLAWISH_SKILLS_DIR": str(settings.skills_dir),
        "OPENCLAWISH_EXECUTION_MODE": settings.execution_mode,
        "OPENCLAWISH_MAX_STEPS": str(settings.max_steps),
        "OPENCLAWISH_COMMAND_TIMEOUT": str(settings.command_timeout),
    }
    if settings.openai_model:
        envs["OPENAI_MODEL"] = settings.openai_model
    if settings.gemini_model:
        envs["GEMINI_MODEL"] = settings.gemini_model
    if settings.openai_api_key:
        envs["OPENAI_API_KEY"] = settings.openai_api_key

    env_blocks = "\n".join(
        f"""    <key>{key}</key>\n    <string>{value}</string>""" for key, value in envs.items()
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_bin}</string>
    <string>{app_bin}</string>
    <string>run-bot</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{settings.workspace}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
{env_blocks}
  </dict>
  <key>StandardOutPath</key>
  <string>{settings.workspace}/logs/openclawish.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>{settings.workspace}/logs/openclawish.stderr.log</string>
</dict>
</plist>
"""
