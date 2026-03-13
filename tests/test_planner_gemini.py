import os
from pathlib import Path

from openclawish.planner import GeminiAuthPlanner


def test_gemini_auth_planner_uses_cli(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "gemini"
    script.write_text(
        """#!/bin/sh
printf '%s' '{"summary":"gemini计划","commands":["pwd","ls"]}'
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
    try:
        planner = GeminiAuthPlanner(
            workspace=tmp_path,
            model="gemini-2.5-pro",
            max_steps=2,
        )
        plan = planner.create_plan("inspect the repo")
    finally:
        os.environ["PATH"] = old_path

    assert plan.summary == "gemini计划"
    assert plan.commands == ["pwd", "ls"]
