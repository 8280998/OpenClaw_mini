from pathlib import Path

from openclawish.config import Settings
from openclawish.deploy import format_check_report, render_launchagent


def test_render_launchagent_contains_label(tmp_path: Path) -> None:
    settings = Settings(
        telegram_bot_token="token",
        telegram_allowed_chat_ids={1},
        openai_api_key=None,
        model_backend="fallback",
        openai_model="codex-mini-latest",
        codex_bin="codex",
        db_path=tmp_path / "data.db",
        workspace=tmp_path,
        skills_dir=tmp_path / "skills",
        execution_mode="workspace",
        max_steps=5,
        command_timeout=120,
    )
    text = render_launchagent(settings, python_bin="/usr/bin/python3", app_bin="/tmp/openclawish", label="com.test.bot")
    assert "com.test.bot" in text
    assert "OPENCLAWISH_MODEL_BACKEND" in text


def test_format_check_report(tmp_path: Path) -> None:
    report = format_check_report([])
    assert report == ""
