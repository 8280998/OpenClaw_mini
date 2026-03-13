from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import CommandRun, TaskRecord, utc_now


SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    input_text TEXT NOT NULL,
    status TEXT NOT NULL,
    planner_output TEXT,
    result_summary TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS command_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    command TEXT NOT NULL,
    exit_code INTEGER,
    stdout TEXT NOT NULL,
    stderr TEXT NOT NULL,
    blocked_reason TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""


class Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_task(self, kind: str, input_text: str) -> int:
        now = utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (kind, input_text, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (kind, input_text, "pending", now, now),
            )
            task_id = int(cur.lastrowid)
            conn.execute(
                """
                INSERT INTO task_events (task_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, "task.created", input_text, now),
            )
            return task_id

    def set_task_status(
        self,
        task_id: int,
        status: str,
        *,
        planner_output: str | None = None,
        result_summary: str | None = None,
    ) -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, planner_output = COALESCE(?, planner_output),
                    result_summary = COALESCE(?, result_summary), updated_at = ?
                WHERE id = ?
                """,
                (status, planner_output, result_summary, now, task_id),
            )
            conn.execute(
                """
                INSERT INTO task_events (task_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, "task.status", status, now),
            )

    def add_event(self, task_id: int, event_type: str, payload: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO task_events (task_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, event_type, payload, utc_now()),
            )

    def add_command_run(self, task_id: int, run: CommandRun) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO command_runs (
                    task_id, command, exit_code, stdout, stderr, blocked_reason, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    run.command,
                    run.exit_code,
                    run.stdout,
                    run.stderr,
                    run.blocked_reason,
                    run.started_at,
                    run.finished_at,
                ),
            )

    def get_task(self, task_id: int) -> TaskRecord | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return TaskRecord(
                id=row["id"],
                kind=row["kind"],
                input_text=row["input_text"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                planner_output=row["planner_output"],
                result_summary=row["result_summary"],
            )

    def list_command_runs(self, task_id: int) -> list[CommandRun]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT command, exit_code, stdout, stderr, blocked_reason, started_at, finished_at
                FROM command_runs
                WHERE task_id = ?
                ORDER BY id ASC
                """,
                (task_id,),
            ).fetchall()

        return [
            CommandRun(
                command=row["command"],
                exit_code=row["exit_code"],
                stdout=row["stdout"],
                stderr=row["stderr"],
                blocked_reason=row["blocked_reason"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
            )
            for row in rows
        ]
