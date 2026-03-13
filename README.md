# OpenClaw_mini

OpenClaw_mini is a Mac mini-hosted local agent system inspired by OpenClaw. It accepts commands from Telegram, plans or executes work locally, records every task in SQLite, and can use either the locally authenticated Codex CLI or the OpenAI Responses API for planning.

The Python package and CLI command remain `openclawish` for now, but the public repository name can be `OpenClaw_mini`.

中文版说明请见 [README.zh-CN.md](./README.zh-CN.md).

The project is designed around a practical first milestone:

- Telegram bot receives a command from an approved chat.
- The service stores the task, applies safety checks, and executes shell work in a controlled workspace.
- The service can ask the locally logged-in Codex CLI or an OpenAI model to turn a natural-language goal into an execution plan.
- Results, logs, and status are persisted for auditability.

## What this repository includes

- A Python service that runs on a Mac mini or any always-on machine.
- Telegram long-polling integration for remote control.
- SQLite-backed task, event, and run history.
- A shell execution sandbox with allowlist and confirmation policy hooks.
- A planner backend that supports `codex_auth`, `gemini_auth`, `api_key`, or `fallback`.
- End-to-end documentation covering setup, architecture, operating flow, and security posture.

## Project status

This is an MVP foundation aimed at the "OpenClaw-like" control plane rather than a full desktop-control stack. It supports:

- Remote task submission
- Local shell execution
- Task persistence and audit logs
- OpenAI-assisted planning
- Approval gates for risky commands

It does not yet ship:

- Native macOS GUI automation
- Browser control
- Multi-agent decomposition
- Streaming desktop screenshots
- Human approval UI beyond Telegram command flows

## Quick start

1. Install Codex CLI on the Mac mini and log in.
2. Install Gemini CLI too if you want `gemini_auth`.
3. Create a Telegram bot with BotFather and capture the token.
4. Use the installer:

```bash
bash ./scripts/install_mac_mini.sh
```

If you prefer Chinese prompts:

```bash
bash ./scripts/install_mac_mini_zh.sh
```

The installer can install missing Codex CLI and Gemini CLI, write `config/openclawish.env`, detect Telegram `chat.id`, and offer to run `codex login` or `gemini` when you choose those auth backends.

5. Verify the local auth state:

```bash
codex login status
codex exec --help
gemini --help
```

6. Get your Telegram `chat.id` and set `TELEGRAM_ALLOWED_CHAT_IDS`.

Send `/start` to your bot in Telegram, then run:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

Look for:

```json
message.chat.id
```

Example:

```json
"chat":{"id":435779584,"first_name":"waves","username":"qq_waves","type":"private"}
```

Then set:

```bash
TELEGRAM_ALLOWED_CHAT_IDS="435779584"
```

7. Create the local data directory and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

8. Start the service:

```bash
bash ./scripts/start_bot.sh
```

9. Message the bot:

```text
/help
/status
/permissions
/permissions system
/models
/models gemini
/run ls
/goal Inspect the repo and summarize the test layout
Inspect the repo and summarize the test layout
```

## Execution modes

OpenClaw_mini supports two execution modes:

- `workspace`: blocks commands that leave the configured workspace via absolute paths or parent traversal.
- `system`: keeps the same working directory, but allows commands that target the wider macOS system.

Set the startup default with:

```bash
export OPENCLAWISH_EXECUTION_MODE="workspace"
```

You can also switch modes at runtime from Telegram with `/mode workspace` or `/mode system`.

## Planner backends

OpenClaw_mini supports four planner backends:

- `codex_auth`: default. Calls the locally logged-in `codex` CLI in non-interactive mode.
- `gemini_auth`: calls the locally logged-in `gemini` CLI in non-interactive mode.
- `api_key`: uses `OPENAI_API_KEY` with the OpenAI SDK.
- `fallback`: no external model call. Uses a tiny static inspection plan.

Set the backend with:

```bash
export OPENCLAWISH_MODEL_BACKEND="codex_auth"
```

`codex_auth` uses the local `codex` CLI login on the Mac mini. The Codex desktop app is not required for this project. In this mode, the project now defaults to `gpt-5.1-codex`, which is the safer choice for ChatGPT-account-based Codex CLI access.

`gemini_auth` uses the local `gemini` CLI login. You can switch at runtime from Telegram with `/backend gemini` and switch back with `/backend openai`.
You can also use the user-facing aliases `/models gemini` and `/models openai`.

## Built-in skills

OpenClaw_mini now includes an app-level skill system for extending behavior with local presets.

- `/skills` lists installed skills
- `/skill repo_audit inspect the repository and summarize risks`
- `/skill system_ops inspect launch agents and recent system state`
- `/skill screenshot capture the current screen and save it under ./artifacts`

Skills are loaded from [`./skills/`](./skills/). Each skill is a JSON file with:

- `name`
- `description`
- `prompt_prefix`
- optional `suggested_mode`

This is separate from Codex session skills. It is a runtime extension mechanism for this Telegram-controlled agent service.

## Deployment helpers

Before starting the bot, you can run:

```bash
openclawish check
```

To generate a LaunchAgent plist:

```bash
openclawish print-launchagent --label com.openclawish.bot > ~/Library/LaunchAgents/com.openclawish.bot.plist
```

For a one-command Mac mini bootstrap, use:

```bash
bash ./scripts/install_mac_mini.sh
```

The installer now runs interactively. It checks whether `codex` and `gemini` CLIs are installed, installs missing ones automatically, and then prompts you for:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_CHAT_IDS`
- default backend and model settings
- execution permissions and workspace

After you enter the bot token, the installer reminds you to send `/start` to the bot once, and then attempts to fetch the latest Telegram `chat.id` automatically after you confirm.

For day-to-day startup on the Mac mini, use:

```bash
bash ./scripts/start_bot.sh
```

`start_bot.sh` already activates `.venv`, loads `config/openclawish.env`, runs `openclawish check`, and then starts the bot.
It also creates runtime directories, blocks placeholder config values, and automatically restarts the bot if an older `openclawish run-bot` process is already running.

The default config template is [`./config/openclawish.env.example`](./config/openclawish.env.example).
Relative paths in that file are resolved from the repository root.

## First publish checklist

- Review [`docs/first-commit-checklist.md`](./docs/first-commit-checklist.md) before pushing the repository public.

## Core docs

- [System overview](./docs/architecture.md)
- [Setup guide](./docs/setup.md)
- [Operations guide](./docs/operations.md)
- [Security model](./docs/security.md)
- [Product workflow](./docs/workflows.md)
- [Skill development](./docs/skills.md)

## Chinese docs

- [系统概览](./docs/architecture.zh-CN.md)
- [部署指南](./docs/setup.zh-CN.md)
- [运维说明](./docs/operations.zh-CN.md)
- [安全模型](./docs/security.zh-CN.md)
- [工作流示例](./docs/workflows.zh-CN.md)
- [Skill 开发](./docs/skills.zh-CN.md)

## OpenAI references

The planner is built around the OpenAI Responses API and is intended for coding-oriented agent tasks. Official references:

- [Responses API overview](https://developers.openai.com/api)
- [GPT-5-Codex model](https://developers.openai.com/api/docs/models/gpt-5-codex)
- [computer-use-preview model](https://developers.openai.com/api/docs/models/computer-use-preview)
