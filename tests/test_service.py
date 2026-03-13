import asyncio
from pathlib import Path

from openclawish.executor import ShellExecutor
from openclawish.planner import FallbackPlanner, Plan
from openclawish.service import AgentService
from openclawish.skills import SkillRegistry
from openclawish.storage import Store


class StaticPlanner:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan

    def create_plan(self, goal: str) -> Plan:
        return self.plan


def test_run_command(tmp_path: Path) -> None:
    store = Store(tmp_path / "test.db")
    executor = ShellExecutor(workspace=tmp_path, timeout_seconds=10)
    service = AgentService(
        store=store,
        executor=executor,
        planner=FallbackPlanner(max_steps=2),
        planner_factory=lambda backend: FallbackPlanner(max_steps=2),
        workspace=tmp_path,
        execution_mode="workspace",
        model_backend="fallback",
        skills=SkillRegistry(tmp_path / "skills"),
        max_steps=2,
    )
    result = asyncio.run(service.handle_run_command("pwd"))
    assert result.status == "completed"
    assert "退出码=0" in result.message


def test_goal_uses_fallback_planner(tmp_path: Path) -> None:
    store = Store(tmp_path / "test.db")
    executor = ShellExecutor(workspace=tmp_path, timeout_seconds=10)
    service = AgentService(
        store=store,
        executor=executor,
        planner=FallbackPlanner(max_steps=2),
        planner_factory=lambda backend: FallbackPlanner(max_steps=2),
        workspace=tmp_path,
        execution_mode="workspace",
        model_backend="fallback",
        skills=SkillRegistry(tmp_path / "skills"),
        max_steps=2,
    )
    result = asyncio.run(service.handle_goal("inspect files"))
    assert result.status == "completed"
    assert "计划：" in result.message


def test_service_mode_switch(tmp_path: Path) -> None:
    store = Store(tmp_path / "test.db")
    executor = ShellExecutor(workspace=tmp_path, timeout_seconds=10)
    service = AgentService(
        store=store,
        executor=executor,
        planner=FallbackPlanner(max_steps=2),
        planner_factory=lambda backend: FallbackPlanner(max_steps=2),
        workspace=tmp_path,
        execution_mode="workspace",
        model_backend="fallback",
        skills=SkillRegistry(tmp_path / "skills"),
        max_steps=2,
    )
    message = service.set_execution_mode("system")
    assert service.execution_mode == "system"
    assert "system" in message


def test_service_backend_switch(tmp_path: Path) -> None:
    store = Store(tmp_path / "test.db")
    executor = ShellExecutor(workspace=tmp_path, timeout_seconds=10)
    service = AgentService(
        store=store,
        executor=executor,
        planner=FallbackPlanner(max_steps=2),
        planner_factory=lambda backend: FallbackPlanner(max_steps=2),
        workspace=tmp_path,
        execution_mode="workspace",
        model_backend="fallback",
        skills=SkillRegistry(tmp_path / "skills"),
        max_steps=2,
    )
    message = service.set_model_backend("gemini")
    assert service.model_backend == "gemini_auth"
    assert "gemini_auth" in message


def test_screenshot_skill_collects_artifacts(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "screenshot.json").write_text(
        '{"name":"screenshot","description":"desc","prompt_prefix":"prefix","suggested_mode":"system"}',
        encoding="utf-8",
    )
    plan = Plan(
        summary="截图",
        commands=["mkdir -p artifacts && touch artifacts/screen.png"],
        raw_text='{"summary":"截图","commands":["mkdir -p artifacts && touch artifacts/screen.png"]}',
    )
    store = Store(tmp_path / "test.db")
    executor = ShellExecutor(workspace=tmp_path, timeout_seconds=10)
    service = AgentService(
        store=store,
        executor=executor,
        planner=StaticPlanner(plan),
        planner_factory=lambda backend: StaticPlanner(plan),
        workspace=tmp_path,
        execution_mode="system",
        model_backend="fallback",
        skills=SkillRegistry(skills_dir),
        max_steps=2,
    )
    result = asyncio.run(service.handle_skill_goal("screenshot", "截图"))
    assert result.status == "completed"
    assert result.artifact_paths
    assert result.artifact_paths[0].name == "screen.png"


def test_goal_screenshot_collects_artifacts(tmp_path: Path) -> None:
    plan = Plan(
        summary="截图",
        commands=["mkdir -p artifacts && touch artifacts/goal-screen.png"],
        raw_text='{"summary":"截图","commands":["mkdir -p artifacts && touch artifacts/goal-screen.png"]}',
    )
    store = Store(tmp_path / "test.db")
    executor = ShellExecutor(workspace=tmp_path, timeout_seconds=10)
    service = AgentService(
        store=store,
        executor=executor,
        planner=StaticPlanner(plan),
        planner_factory=lambda backend: StaticPlanner(plan),
        workspace=tmp_path,
        execution_mode="system",
        model_backend="fallback",
        skills=SkillRegistry(tmp_path / "skills"),
        max_steps=2,
    )
    result = asyncio.run(service.handle_goal("截图并发送给我"))
    assert result.status == "completed"
    assert result.artifact_paths
    assert result.artifact_paths[0].name == "goal-screen.png"
