from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class CommandRun:
    command: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    blocked_reason: str | None = None


@dataclass(slots=True)
class TaskRecord:
    id: int
    kind: str
    input_text: str
    status: str
    created_at: str
    updated_at: str
    planner_output: str | None
    result_summary: str | None
