from __future__ import annotations

import argparse
import sys

from .config import Settings
from .deploy import format_check_report, render_launchagent, run_startup_checks
from .executor import ShellExecutor
from .planner import CodexAuthPlanner, FallbackPlanner, GeminiAuthPlanner, OpenAIPlanner, Planner
from .service import AgentService
from .skills import SkillRegistry
from .storage import Store


def build_planner(settings: Settings, backend: str) -> Planner:
    if backend == "codex_auth":
        model_name = settings.openai_model or "gpt-5.1-codex"
        return CodexAuthPlanner(
            workspace=settings.workspace,
            model=model_name,
            max_steps=settings.max_steps,
            codex_bin=settings.codex_bin,
            timeout_seconds=settings.command_timeout,
        )
    if backend == "gemini_auth":
        return GeminiAuthPlanner(
            workspace=settings.workspace,
            model=settings.gemini_model,
            max_steps=settings.max_steps,
            gemini_bin=settings.gemini_bin,
            timeout_seconds=settings.command_timeout,
        )
    if backend == "api_key":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when OPENCLAWISH_MODEL_BACKEND=api_key")
        model_name = settings.openai_model or "gpt-5.3-codex"
        return OpenAIPlanner(settings.openai_api_key, model_name, settings.max_steps)
    if backend == "fallback":
        return FallbackPlanner(settings.max_steps)
    raise RuntimeError("OPENCLAWISH_MODEL_BACKEND must be codex_auth, gemini_auth, api_key, or fallback")


def build_service(settings: Settings) -> AgentService:
    store = Store(settings.db_path)
    executor = ShellExecutor(
        workspace=settings.workspace,
        timeout_seconds=settings.command_timeout,
    )
    skills = SkillRegistry(settings.skills_dir)
    planner = build_planner(settings, settings.model_backend)
    return AgentService(
        store=store,
        executor=executor,
        planner=planner,
        planner_factory=lambda backend: build_planner(settings, backend),
        workspace=settings.workspace,
        execution_mode=settings.execution_mode,
        model_backend=settings.model_backend,
        skills=skills,
        max_steps=settings.max_steps,
    )


def _run_bot() -> None:
    settings = Settings.from_env()
    results = run_startup_checks(settings)
    failed = [item for item in results if not item.ok]
    if failed:
        raise RuntimeError(f"startup checks failed:\n{format_check_report(results)}")
    service = build_service(settings)
    from .telegram_bot import TelegramBotApp

    app = TelegramBotApp(
        token=settings.telegram_bot_token,
        allowed_chat_ids=settings.telegram_allowed_chat_ids,
        service=service,
    )
    app.run()


def _check() -> None:
    settings = Settings.from_env()
    print(format_check_report(run_startup_checks(settings)))


def _print_launchagent(label: str) -> None:
    settings = Settings.from_env()
    print(
        render_launchagent(
            settings,
            python_bin=sys.executable,
            app_bin=str(settings.workspace / ".venv" / "bin" / "openclawish"),
            label=label,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="openclawish")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run-bot")
    launchagent_parser = subparsers.add_parser("print-launchagent")
    launchagent_parser.add_argument("--label", default="com.openclawish.bot")
    subparsers.add_parser("check")
    args = parser.parse_args()

    if args.command == "run-bot":
        _run_bot()
    elif args.command == "check":
        _check()
    elif args.command == "print-launchagent":
        _print_launchagent(args.label)


if __name__ == "__main__":
    main()
