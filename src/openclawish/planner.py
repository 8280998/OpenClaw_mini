from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    OpenAI = None


PLANNER_PROMPT = """You are a local coding agent planner.
Turn the user's goal into a short shell plan for a trusted operator.
Constraints:
- Reply as JSON with keys summary and commands.
- The summary should be written in Simplified Chinese by default.
- commands must be an array of plain shell commands.
- Use at most {max_steps} commands.
- Prefer read-only inspection commands unless the user explicitly asks for edits.
- If the user explicitly asks to create an artifact, such as a screenshot, output the direct command that creates it instead of repository inspection commands.
- A screenshot request is an explicit write request. Prefer a concrete macOS screencapture command that saves into ./artifacts or another user-requested relative path.
- Do not use sudo.
- Do not use destructive commands.
"""


@dataclass(slots=True)
class Plan:
    summary: str
    commands: list[str]
    raw_text: str


class Planner(Protocol):
    def create_plan(self, goal: str) -> Plan: ...
    def describe_backend(self) -> str: ...


OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "commands": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["summary", "commands"],
}


def _normalize_plan_payload(text: str, max_steps: int) -> Plan:
    data = json.loads(text)
    commands = data.get("commands", [])
    if not isinstance(commands, list):
        raise ValueError("Planner returned invalid commands payload")
    normalized = [str(command).strip() for command in commands if str(command).strip()]
    return Plan(
        summary=str(data.get("summary", "")).strip(),
        commands=normalized[: max_steps],
        raw_text=text,
    )


def _extract_json_payload(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Planner did not return JSON content")
    return stripped[start : end + 1]


class OpenAIPlanner:
    def __init__(self, api_key: str, model: str, max_steps: int) -> None:
        if OpenAI is None:
            raise RuntimeError("openai package is not installed")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_steps = max_steps

    def create_plan(self, goal: str) -> Plan:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": PLANNER_PROMPT.format(max_steps=self.max_steps)},
                {"role": "user", "content": goal},
            ],
        )
        text = getattr(response, "output_text", "") or ""
        return _normalize_plan_payload(text, self.max_steps)

    def describe_backend(self) -> str:
        return f"api_key / {self.model}"


class CodexAuthPlanner:
    def __init__(
        self,
        workspace: Path,
        model: str,
        max_steps: int,
        *,
        codex_bin: str = "codex",
        timeout_seconds: int = 180,
    ) -> None:
        self.workspace = workspace
        self.model = model
        self.max_steps = max_steps
        self.codex_bin = codex_bin
        self.timeout_seconds = timeout_seconds

    def create_plan(self, goal: str) -> Plan:
        if not shutil.which(self.codex_bin):
            raise RuntimeError(f"{self.codex_bin} CLI is not installed or not on PATH")

        status = subprocess.run(
            [self.codex_bin, "login", "status"],
            cwd=str(self.workspace),
            capture_output=True,
            text=True,
            timeout=20,
        )
        if status.returncode != 0:
            stderr = (status.stderr or status.stdout).strip()
            raise RuntimeError(f"{self.codex_bin} login status failed: {stderr or status.returncode}")

        prompt = "\n\n".join(
            [
                PLANNER_PROMPT.format(max_steps=self.max_steps),
                f"User goal:\n{goal}",
                "Return only valid JSON that matches the required schema.",
            ]
        )

        with tempfile.TemporaryDirectory(prefix="openclawish-codex-") as temp_dir:
            temp_path = Path(temp_dir)
            schema_path = temp_path / "plan.schema.json"
            output_path = temp_path / "last-message.txt"
            schema_path.write_text(json.dumps(OUTPUT_SCHEMA), encoding="utf-8")

            cmd = [
                self.codex_bin,
                "exec",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                "-C",
                str(self.workspace),
            ]
            if self.model:
                cmd.extend(["-m", self.model])
            cmd.append("-")

            result = subprocess.run(
                cmd,
                input=prompt,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if result.returncode != 0:
                stderr = (result.stderr or result.stdout).strip()
                raise RuntimeError(f"{self.codex_bin} exec failed: {stderr or result.returncode}")
            text = output_path.read_text(encoding="utf-8").strip()
            return _normalize_plan_payload(text, self.max_steps)

    def describe_backend(self) -> str:
        return f"codex_auth / {self.model} via {self.codex_bin}"


class GeminiAuthPlanner:
    def __init__(
        self,
        workspace: Path,
        model: str,
        max_steps: int,
        *,
        gemini_bin: str = "gemini",
        timeout_seconds: int = 180,
    ) -> None:
        self.workspace = workspace
        self.model = model
        self.max_steps = max_steps
        self.gemini_bin = gemini_bin
        self.timeout_seconds = timeout_seconds

    def create_plan(self, goal: str) -> Plan:
        if not shutil.which(self.gemini_bin):
            raise RuntimeError(f"{self.gemini_bin} CLI is not installed or not on PATH")

        prompt = "\n\n".join(
            [
                PLANNER_PROMPT.format(max_steps=self.max_steps),
                f"User goal:\n{goal}",
                "Return only valid JSON with keys summary and commands. Do not include markdown fences.",
            ]
        )

        cmd = [self.gemini_bin, "-p", prompt]
        if self.model:
            cmd.extend(["-m", self.model])

        result = subprocess.run(
            cmd,
            cwd=str(self.workspace),
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        if result.returncode != 0:
            stderr = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"{self.gemini_bin} failed: {stderr or result.returncode}")
        text = _extract_json_payload(result.stdout or "")
        return _normalize_plan_payload(text, self.max_steps)

    def describe_backend(self) -> str:
        return f"gemini_auth / {self.model or 'default'} via {self.gemini_bin}"


class FallbackPlanner:
    def __init__(self, max_steps: int) -> None:
        self.max_steps = max_steps

    def create_plan(self, goal: str) -> Plan:
        commands = [
            "pwd",
            "find . -maxdepth 2 -type f | sort | head -100",
        ][: self.max_steps]
        text = json.dumps({"summary": f"Fallback plan for goal: {goal}", "commands": commands})
        return _normalize_plan_payload(text, self.max_steps)

    def describe_backend(self) -> str:
        return "fallback"
