from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path


BLOCKED_PATTERNS = (
    "rm -rf /",
    "shutdown",
    "reboot",
    "mkfs",
    "dd if=",
    "diskutil eraseDisk",
    "sudo ",
)


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    reason: str | None = None


def validate_command(
    command: str,
    *,
    mode: str = "system",
    workspace: Path | None = None,
) -> PolicyDecision:
    return validate_command_for_mode(
        command,
        mode=mode,
        workspace=workspace or Path.cwd(),
    )


def validate_command_for_mode(command: str, *, mode: str, workspace: Path) -> PolicyDecision:
    normalized = command.strip().lower()
    if not normalized:
        return PolicyDecision(False, "empty command")

    for pattern in BLOCKED_PATTERNS:
        if pattern in normalized:
            return PolicyDecision(False, f"blocked by pattern: {pattern}")

    if mode == "workspace":
        workspace_decision = _validate_workspace_scope(command, workspace)
        if not workspace_decision.allowed:
            return workspace_decision

    return PolicyDecision(True)


def _validate_workspace_scope(command: str, workspace: Path) -> PolicyDecision:
    if re.search(r"(^|[;&|])\s*cd\s+/", command):
        return PolicyDecision(False, "workspace mode blocks cd to an absolute path")

    try:
        tokens = shlex.split(command)
    except ValueError:
        return PolicyDecision(False, "unable to parse command")

    for token in tokens:
        if token == ".." or token.startswith("../") or "/../" in token:
            return PolicyDecision(False, "workspace mode blocks parent-directory traversal")

        if token.startswith("/"):
            resolved = Path(token).expanduser().resolve(strict=False)
            try:
                resolved.relative_to(workspace)
            except ValueError:
                return PolicyDecision(
                    False,
                    f"workspace mode blocks absolute path outside {workspace}",
                )

    return PolicyDecision(True)
