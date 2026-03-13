from __future__ import annotations

import html

from telegram import InputFile, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .service import AgentService


HELP_TEXT = """
可用命令：
/help - 显示帮助
/status - 查看服务状态、规划后端和当前模式
/models - 查看当前规划后端
/models <openai|gemini|codex_auth|gemini_auth|api_key|fallback> - 切换规划后端
/backend - 查看当前规划后端
/backend <openai|gemini|codex_auth|gemini_auth|api_key|fallback> - 切换规划后端
/permissions - 查看当前执行权限范围
/permissions <workspace|system> - 切换执行权限范围
/mode - 查看当前执行模式
/mode <workspace|system> - 切换执行模式
/skills - 列出已安装的 skill
/skill <name> <任务描述> - 使用 skill 预设执行目标
/run <shell command> - 直接执行命令
/goal <任务描述> - 让规划器生成执行计划
/task <task_id> - 查看任务详情

普通文本消息会自动按 /goal 处理。
""".strip()


class TelegramBotApp:
    def __init__(
        self,
        token: str,
        allowed_chat_ids: set[int],
        service: AgentService,
    ) -> None:
        self.allowed_chat_ids = allowed_chat_ids
        self.service = service
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("models", self.backend_command))
        self.application.add_handler(CommandHandler("backend", self.backend_command))
        self.application.add_handler(CommandHandler("permissions", self.mode_command))
        self.application.add_handler(CommandHandler("mode", self.mode_command))
        self.application.add_handler(CommandHandler("skills", self.skills_command))
        self.application.add_handler(CommandHandler("skill", self.skill_command))
        self.application.add_handler(CommandHandler("run", self.run_command))
        self.application.add_handler(CommandHandler("goal", self.goal_command))
        self.application.add_handler(CommandHandler("task", self.task_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.natural_language_message)
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        await update.message.reply_text(HELP_TEXT)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        await update.message.reply_text(self.service.get_status_message())

    async def backend_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        backend = " ".join(context.args).strip().lower()
        if not backend:
            await update.message.reply_text(self.service.get_backend_message())
            return
        try:
            message = self.service.set_model_backend(backend)
        except ValueError as exc:
            await update.message.reply_text(str(exc))
            return
        except RuntimeError as exc:
            await update.message.reply_text(f"切换后端失败：{exc}")
            return
        await update.message.reply_text(message)

    async def mode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        mode = " ".join(context.args).strip().lower()
        if not mode:
            await update.message.reply_text(f"当前模式：{self.service.execution_mode}")
            return
        try:
            message = self.service.set_execution_mode(mode)
        except ValueError as exc:
            await update.message.reply_text(str(exc))
            return
        await update.message.reply_text(message)

    async def run_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        command = " ".join(context.args).strip()
        if not command:
            await update.message.reply_text("用法：/run <shell command>")
            return
        result = await self.service.handle_run_command(command)
        await update.message.reply_text(self._escape_message(result.message), parse_mode="HTML")

    async def skills_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        await update.message.reply_text(self.service.get_skills_message())

    async def skill_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        if len(context.args) < 2:
            await update.message.reply_text("用法：/skill <name> <任务描述>")
            return
        skill_name = context.args[0].strip()
        goal = " ".join(context.args[1:]).strip()
        await update.message.reply_text(f"正在执行 skill：{skill_name} ...")
        result = await self.service.handle_skill_goal(skill_name, goal)
        await update.message.reply_text(self._escape_message(result.message), parse_mode="HTML")
        if result.artifact_paths:
            for artifact_path in result.artifact_paths:
                if artifact_path.exists():
                    with artifact_path.open("rb") as handle:
                        await update.message.reply_document(
                            document=InputFile(handle, filename=artifact_path.name),
                            caption=f"截图文件：{artifact_path.name}",
                        )

    async def goal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        goal = " ".join(context.args).strip()
        if not goal:
            await update.message.reply_text("用法：/goal <任务描述>")
            return
        await self._run_goal(update, goal)

    async def natural_language_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        if not await self._ensure_allowed(update):
            return
        if not update.message or not update.message.text:
            return
        goal = update.message.text.strip()
        if not goal:
            return
        await self._run_goal(update, goal)

    async def _run_goal(self, update: Update, goal: str) -> None:
        await update.message.reply_text("正在规划并执行...")
        result = await self.service.handle_goal(goal)
        await update.message.reply_text(self._escape_message(result.message), parse_mode="HTML")
        if result.artifact_paths:
            for artifact_path in result.artifact_paths:
                if artifact_path.exists():
                    with artifact_path.open("rb") as handle:
                        await update.message.reply_document(
                            document=InputFile(handle, filename=artifact_path.name),
                            caption=f"截图文件：{artifact_path.name}",
                        )

    async def task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._ensure_allowed(update):
            return
        raw_task_id = " ".join(context.args).strip()
        if not raw_task_id.isdigit():
            await update.message.reply_text("用法：/task <task_id>")
            return
        message = self.service.get_task_message(int(raw_task_id))
        await update.message.reply_text(self._escape_message(message), parse_mode="HTML")

    def run(self) -> None:
        self.application.run_polling()

    async def _ensure_allowed(self, update: Update) -> bool:
        chat = update.effective_chat
        if not chat or chat.id not in self.allowed_chat_ids:
            if update.message:
                text = f"chat_id {chat.id if chat else 'unknown'} 未被允许访问"
                await update.message.reply_text(text)
            return False
        return True

    @staticmethod
    def _escape_message(text: str) -> str:
        return html.escape(text)
