import os
from pathlib import Path

from openclawish.planner import CodexAuthPlanner


def test_codex_auth_planner_uses_cli(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "codex"
    script.write_text(
        """#!/bin/sh
if [ "$1" = "login" ] && [ "$2" = "status" ]; then
  echo "logged in"
  exit 0
fi
if [ "$1" = "exec" ]; then
  while [ "$#" -gt 0 ]; do
    if [ "$1" = "--output-last-message" ]; then
      shift
      out="$1"
    fi
    shift
  done
  printf '%s' '{"summary":"cli plan","commands":["pwd","ls"]}' > "$out"
  exit 0
fi
exit 1
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
    try:
        planner = CodexAuthPlanner(
            workspace=tmp_path,
            model="codex-mini-latest",
            max_steps=2,
        )
        plan = planner.create_plan("inspect the repo")
    finally:
        os.environ["PATH"] = old_path

    assert plan.summary == "cli plan"
    assert plan.commands == ["pwd", "ls"]
