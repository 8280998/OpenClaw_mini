from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import CommandRun


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ShellExecutor:
    workspace: Path
    timeout_seconds: int

    async def run(self, command: str) -> CommandRun:
        started_at = _utc_now()
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(self.workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout_seconds,
            )
            return CommandRun(
                command=command,
                exit_code=proc.returncode,
                stdout=stdout_bytes.decode(errors="replace"),
                stderr=stderr_bytes.decode(errors="replace"),
                started_at=started_at,
                finished_at=_utc_now(),
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return CommandRun(
                command=command,
                exit_code=124,
                stdout="",
                stderr=f"Command timed out after {self.timeout_seconds} seconds",
                started_at=started_at,
                finished_at=_utc_now(),
            )
