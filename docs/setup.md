# Setup Guide

## Prerequisites

- macOS on a resident machine such as a Mac mini
- Python 3.11 or later
- Codex CLI installed on the Mac mini
- Gemini CLI installed on the Mac mini if you want `gemini_auth`
- A Telegram bot token from BotFather
- A logged-in local `codex` CLI for the default `codex_auth` planner backend
- An OpenAI API key only if you choose the `api_key` backend

## Install Codex CLI on the Mac mini

This project uses the local `codex` CLI login for the default `codex_auth` backend. You do not need the Codex desktop app for this deployment.

1. Install the Codex CLI on the Mac mini.
   
   Official install command:

```bash
npm install -g @openai/codex
```

2. Log in locally:

```bash
codex login
```

3. Confirm the login is usable:

```bash
codex login status
codex exec --help
```

If both commands succeed, the Mac mini is ready to use `codex_auth`.

To upgrade later:

```bash
codex --upgrade
```

## Install Gemini CLI on the Mac mini

If you want to use `gemini_auth`, install the official Gemini CLI:

```bash
npm install -g @google/gemini-cli
```

Then start the login flow:

```bash
gemini
```

And verify the CLI is available:

```bash
gemini --help
```

## Install this project

```bash
cd /path/to/OpenClaw_mini
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## One-command installer

For a fresh Mac mini setup, you can run:

```bash
bash ./scripts/install_mac_mini.sh
```

For a Chinese-language interactive installer, use:

```bash
bash ./scripts/install_mac_mini_zh.sh
```

The script:

- checks for macOS
- installs Node.js with Homebrew if `npm` is missing
- installs missing `@openai/codex`
- installs missing `@google/gemini-cli`
- creates `.venv`
- installs project dependencies
- creates `data`, `logs`, and `skills` directories
- interactively asks for Telegram bot token and chat IDs
- reminds you to message the bot once; after you confirm, the script enters a short wait window so you can send `/start` at that moment and it can fetch the latest Telegram `chat.id`
- warns you if a bot process is already running, because that process may consume Telegram updates before the installer can detect `chat.id`
- offers to run `codex login` automatically if you choose `codex_auth`
- offers to run `gemini` automatically if you choose `gemini_auth`; to avoid blocking the installer, it tries to open that login flow in a new Terminal window
- writes key settings to `config/openclawish.env` immediately after you enter them, so partial progress is not lost if you pause during setup
- writes the answers into `config/openclawish.env`

## Environment variables

Required:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_ALLOWED_CHAT_IDS="123456789,987654321"
```

Optional:

```bash
export OPENCLAWISH_MODEL_BACKEND="codex_auth"
export OPENAI_MODEL="gpt-5.1-codex"
export OPENCLAWISH_CODEX_BIN="codex"
export GEMINI_MODEL=""
export OPENCLAWISH_GEMINI_BIN="gemini"
export OPENCLAWISH_DB_PATH="./data/openclawish.db"
export OPENCLAWISH_WORKSPACE="."
export OPENCLAWISH_SKILLS_DIR="./skills"
export OPENCLAWISH_EXECUTION_MODE="workspace"
export OPENCLAWISH_MAX_STEPS="5"
export OPENCLAWISH_COMMAND_TIMEOUT="120"
```

## Config file

Instead of exporting variables manually every time, use the provided config file:

```bash
cp ./config/openclawish.env.example ./config/openclawish.env
```

Edit `./config/openclawish.env`, then load it:

```bash
source ./scripts/load_env.sh
```

Relative paths such as `./data/openclawish.db`, `.` and `./skills` are resolved from the repository root.

For normal startup, you usually do not need to run that command manually because `./scripts/start_bot.sh` already loads the config file for you.

You can also point to a custom file:

```bash
OPENCLAWISH_ENV_FILE=/path/to/your.env source ./scripts/load_env.sh
```

## How to get `TELEGRAM_ALLOWED_CHAT_IDS`

1. Create the bot in BotFather and save the bot token.
2. Open Telegram and send `/start` to that bot.
3. Run:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

4. Find:

```json
message.chat.id
```

Example:

```json
"chat":{"id":xxxx,"first_name":"xxxx","username":"xxxx","type":"private"}
```

5. Put that value into your config file:

```bash
TELEGRAM_ALLOWED_CHAT_IDS="xxxx"
```

Notes:

- For a private chat, the ID is usually a positive integer.
- For groups or supergroups, the ID may be negative and can look like `-100...`.
- If `getUpdates` returns an empty array, send a new message to the bot and try again.

If you prefer the API-key backend instead of the local Codex login:

```bash
export OPENCLAWISH_MODEL_BACKEND="api_key"
export OPENAI_MODEL="gpt-5.3-codex"
export OPENAI_API_KEY="..."
```

## First launch

```bash
mkdir -p data
bash ./scripts/start_bot.sh
```

Or use the bundled startup script:

```bash
bash ./scripts/start_bot.sh
```

The startup script also:

- creates `data`, `logs`, `artifacts`, and `tmp` if missing
- stops startup when the config file still contains placeholder values
- restarts the bot automatically if another `openclawish run-bot` process is already running

## Telegram commands

- `/help`
- `/status`
- `/models`
- `/models <openai|gemini|codex_auth|gemini_auth|api_key|fallback>`
- `/backend`
- `/backend <openai|gemini|codex_auth|gemini_auth|api_key|fallback>`
- `/permissions`
- `/permissions <workspace|system>`
- `/mode`
- `/mode <workspace|system>`
- `/skills`
- `/skill <name> <task description>`
- `/run <shell command>`
- `/goal <natural language task>`
- `/task <task_id>`
- Plain text messages, which are treated as `/goal <message>`

## Mode behavior

- `workspace` mode is safer and intended for repository-bounded operations.
- `system` mode allows commands that target the broader Mac host.

Even in `system` mode, the service still starts commands from `OPENCLAWISH_WORKSPACE`; the difference is in policy scope, not the initial working directory.

## Planner backend behavior

- `codex_auth` runs `codex login status` and then `codex exec` in non-interactive mode. This project defaults to `gpt-5.1-codex` in that mode because it is the safer ChatGPT-account-compatible option.
- `gemini_auth` runs the local `gemini` CLI in non-interactive mode and is intended for a locally authenticated Gemini CLI session.
- `api_key` uses the Python OpenAI SDK.
- `fallback` skips external model access entirely.

## Running as a LaunchAgent

Generate a user LaunchAgent template:

```bash
openclawish print-launchagent --label com.openclawish.bot > ~/Library/LaunchAgents/com.openclawish.bot.plist
```

Then load it:

```bash
launchctl unload ~/Library/LaunchAgents/com.openclawish.bot.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.openclawish.bot.plist
```

Keep the working directory pointed at the repository root or your chosen host workspace so SQLite paths and logs stay stable.

## Minimal deployment checklist

1. `codex login status` works on the Mac mini.
2. `openclawish check` reports all `OK`.
3. The Telegram bot can answer `/status`.
4. `/backend` shows `codex_auth`.
