from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .executor import ShellExecutor
from .models import CommandRun
from .planner import Plan, Planner
from .policy import validate_command
from .skills import SkillRegistry
from .storage import Store


def _trim(text: str, limit: int = 1500) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


@dataclass(slots=True)
class ServiceResult:
    task_id: int
    status: str
    message: str
    artifact_paths: list[Path] | None = None


class AgentService:
    def __init__(
        self,
        store: Store,
        executor: ShellExecutor,
        planner: Planner,
        *,
        planner_factory: Callable[[str], Planner],
        workspace: Path,
        execution_mode: str,
        model_backend: str,
        skills: SkillRegistry,
        max_steps: int,
    ) -> None:
        self.store = store
        self.executor = executor
        self.planner = planner
        self.planner_factory = planner_factory
        self.workspace = workspace
        self.execution_mode = execution_mode
        self.model_backend = model_backend
        self.skills = skills
        self.max_steps = max_steps

    async def handle_run_command(self, command: str) -> ServiceResult:
        task_id = self.store.create_task("run", command)
        self.store.set_task_status(task_id, "running")
        decision = validate_command(command, mode=self.execution_mode, workspace=self.workspace)
        if not decision.allowed:
            run = CommandRun(command=command, blocked_reason=decision.reason)
            self.store.add_command_run(task_id, run)
            self.store.set_task_status(task_id, "rejected", result_summary=decision.reason)
            return ServiceResult(task_id, "rejected", f"任务 {task_id} 已拒绝：{decision.reason}")

        run = await self.executor.run(command)
        self.store.add_command_run(task_id, run)
        status = "completed" if run.exit_code == 0 else "failed"
        summary = self._summarize_runs([run], planner_output=None)
        self.store.set_task_status(task_id, status, result_summary=summary)
        return ServiceResult(task_id, status, summary)

    async def handle_goal(self, goal: str) -> ServiceResult:
        return await self._execute_goal(
            goal,
            kind="goal",
            capture_artifacts=self._should_capture_artifacts("goal", goal),
        )

    async def handle_skill_goal(self, skill_name: str, goal: str) -> ServiceResult:
        skill = self.skills.get(skill_name)
        if not skill:
            return ServiceResult(0, "failed", f"未找到 skill：{skill_name}")
        augmented_goal = "\n\n".join(
            [
                f"Skill name: {skill.name}",
                f"Skill description: {skill.description}",
                f"Skill instructions:\n{skill.prompt_prefix}",
                "This skill request explicitly authorizes creating files when needed to complete the task.",
                f"User goal:\n{goal}",
            ]
        )
        return await self._execute_goal(
            augmented_goal,
            kind=f"skill:{skill.name}",
            capture_artifacts=skill.name == "screenshot" or self._should_capture_artifacts(
                f"skill:{skill.name}", goal
            ),
        )

    async def _execute_goal(
        self,
        goal: str,
        *,
        kind: str,
        capture_artifacts: bool = False,
    ) -> ServiceResult:
        task_id = self.store.create_task(kind, goal)
        self.store.set_task_status(task_id, "planning")
        before_artifacts = self._scan_artifact_images() if capture_artifacts else set()
        try:
            plan = self.planner.create_plan(goal)
        except Exception as exc:
            self.store.set_task_status(task_id, "failed", result_summary=str(exc))
            return ServiceResult(task_id, "failed", f"任务 {task_id} 规划失败：{exc}")

        self.store.add_event(task_id, "planner.output", plan.raw_text)
        self.store.set_task_status(task_id, "running", planner_output=plan.raw_text)
        runs: list[CommandRun] = []
        for command in plan.commands[: self.max_steps]:
            decision = validate_command(command, mode=self.execution_mode, workspace=self.workspace)
            if not decision.allowed:
                blocked_run = CommandRun(command=command, blocked_reason=decision.reason)
                self.store.add_command_run(task_id, blocked_run)
                runs.append(blocked_run)
                summary = self._summarize_runs(runs, planner_output=plan)
                self.store.set_task_status(task_id, "rejected", result_summary=summary)
                return ServiceResult(task_id, "rejected", summary, artifact_paths=[])

            run = await self.executor.run(command)
            self.store.add_command_run(task_id, run)
            runs.append(run)
            if run.exit_code != 0:
                summary = self._summarize_runs(runs, planner_output=plan)
                self.store.set_task_status(task_id, "failed", result_summary=summary)
                return ServiceResult(task_id, "failed", summary, artifact_paths=[])

        summary = self._summarize_runs(runs, planner_output=plan)
        self.store.set_task_status(task_id, "completed", result_summary=summary)
        artifact_paths = (
            sorted(self._scan_artifact_images() - before_artifacts)
            if capture_artifacts
            else []
        )
        return ServiceResult(task_id, "completed", summary, artifact_paths=artifact_paths)

    def get_task_message(self, task_id: int) -> str:
        task = self.store.get_task(task_id)
        if not task:
            return f"未找到任务：{task_id}"
        runs = self.store.list_command_runs(task_id)
        lines = [
            f"任务 {task.id}",
            f"类型：{task.kind}",
            f"状态：{task.status}",
            f"输入：{task.input_text}",
        ]
        if task.planner_output:
            lines.append(f"规划输出：{_trim(task.planner_output, 400)}")
        for index, run in enumerate(runs, start=1):
            lines.append(f"执行 {index}：{run.command}")
            if run.blocked_reason:
                lines.append(f"已拦截：{run.blocked_reason}")
            else:
                lines.append(f"退出码：{run.exit_code}")
                if run.stdout:
                    lines.append(f"标准输出：{_trim(run.stdout, 300)}")
                if run.stderr:
                    lines.append(f"错误输出：{_trim(run.stderr, 300)}")
        return "\n".join(lines)

    def get_status_message(self) -> str:
        return (
            "OpenClawish 运行中\n"
            f"规划后端：{self.model_backend}\n"
            f"后端详情：{self.planner.describe_backend()}\n"
            f"执行模式：{self.execution_mode}\n"
            f"工作区：{self.workspace}\n"
            f"Skill 数量：{len(self.skills.list_skills())}\n"
            f"最大步骤数：{self.max_steps}\n"
            f"超时时间：{self.executor.timeout_seconds}s"
        )

    def get_backend_message(self) -> str:
        return f"当前规划后端：{self.model_backend}\n详情：{self.planner.describe_backend()}"

    def get_skills_message(self) -> str:
        skills = self.skills.list_skills()
        if not skills:
            return "当前没有已安装的 skill"
        return "\n".join(
            [f"{skill.name}：{skill.description}" for skill in skills]
        )

    def set_execution_mode(self, mode: str) -> str:
        normalized = mode.strip().lower()
        if normalized not in {"workspace", "system"}:
            raise ValueError("模式只能是 workspace 或 system")
        self.execution_mode = normalized
        return f"执行模式已切换为：{normalized}"

    def set_model_backend(self, backend: str) -> str:
        normalized = backend.strip().lower()
        aliases = {
            "openai": "codex_auth",
            "codex": "codex_auth",
            "gemini": "gemini_auth",
        }
        normalized = aliases.get(normalized, normalized)
        if normalized not in {"codex_auth", "gemini_auth", "api_key", "fallback"}:
            raise ValueError("后端只能是 codex_auth、gemini_auth、api_key、fallback、openai 或 gemini")
        self.planner = self.planner_factory(normalized)
        self.model_backend = normalized
        return f"规划后端已切换为：{normalized}\n详情：{self.planner.describe_backend()}"

    def _summarize_runs(self, runs: list[CommandRun], *, planner_output: Plan | None) -> str:
        lines: list[str] = []
        if planner_output:
            lines.append(f"计划：{planner_output.summary or '无摘要'}")
        for run in runs:
            if run.blocked_reason:
                lines.append(f"{run.command}\n已拦截：{run.blocked_reason}")
                continue
            lines.append(f"{run.command}\n退出码={run.exit_code}")
            if run.stdout:
                lines.append(f"标准输出：\n{_trim(run.stdout, 500)}")
            if run.stderr:
                lines.append(f"错误输出：\n{_trim(run.stderr, 500)}")
        return _trim("\n\n".join(lines), 3500)

    def _scan_artifact_images(self) -> set[Path]:
        suffixes = {".png", ".jpg", ".jpeg", ".webp"}
        roots = [self.workspace, self.workspace / "artifacts", self.workspace / "tmp"]
        files: set[Path] = set()
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in suffixes:
                    files.add(path.resolve())
        return files

    @staticmethod
    def _should_capture_artifacts(kind: str, goal: str) -> bool:
        normalized_kind = kind.lower()
        normalized_goal = goal.lower()
        if normalized_kind == "skill:screenshot":
            return True
        keywords = (
            "screenshot",
            "screen shot",
            "screen capture",
            "screencapture",
            "截图",
            "截屏",
            "螢幕截圖",
            "屏幕截图",
        )
        return any(keyword in normalized_goal for keyword in keywords)
