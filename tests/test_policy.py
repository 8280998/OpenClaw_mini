from pathlib import Path

from openclawish.policy import validate_command


def test_blocks_sudo() -> None:
    decision = validate_command("sudo ls")
    assert not decision.allowed
    assert "sudo" in (decision.reason or "")


def test_allows_safe_command() -> None:
    decision = validate_command("git status")
    assert decision.allowed


def test_workspace_mode_blocks_absolute_paths_outside_workspace() -> None:
    decision = validate_command("cat /etc/hosts", mode="workspace", workspace=Path("/tmp/workspace"))
    assert not decision.allowed
    assert "workspace mode" in (decision.reason or "")


def test_system_mode_allows_absolute_paths() -> None:
    decision = validate_command("cat /etc/hosts", mode="system", workspace=Path("/tmp/workspace"))
    assert decision.allowed
