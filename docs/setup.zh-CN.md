# 部署指南

## 前置条件

- 一台常驻运行的 macOS 设备，例如 Mac mini
- Python 3.11 或更高版本
- 在 Mac mini 上安装好的 Codex CLI
- 如果你想用 `gemini_auth`，还需要在 Mac mini 上安装 Gemini CLI
- 通过 BotFather 创建的 Telegram 机器人 token
- 默认的 `codex_auth` 规划后端需要本机已经登录的 `codex` CLI
- 如果你选择 `api_key` 后端，才需要 OpenAI API key

## 在 Mac mini 上安装 Codex CLI

这个项目默认使用本机 `codex` CLI 登录态来驱动 `codex_auth` 后端，所以不需要 Codex 桌面版。

1. 在 Mac mini 上安装 Codex CLI。

   官方安装命令：

```bash
npm install -g @openai/codex
```

2. 在本机完成登录：

```bash
codex login
```

3. 验证登录状态可用：

```bash
codex login status
codex exec --help
```

如果这两条命令都正常返回，就说明这台 Mac mini 已经可以使用 `codex_auth`。

后续升级可以执行：

```bash
codex --upgrade
```

## 在 Mac mini 上安装 Gemini CLI

如果你想使用 `gemini_auth`，可以安装官方 Gemini CLI：

```bash
npm install -g @google/gemini-cli
```

然后启动登录流程：

```bash
gemini
```

再验证 CLI 可用：

```bash
gemini --help
```

## 安装本项目

```bash
cd /path/to/OpenClaw_mini
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 一键安装脚本

如果是在一台新的 Mac mini 上做初始化，可以直接执行：

```bash
bash ./scripts/install_mac_mini.sh
```

如果你希望使用中文交互版安装流程，可以执行：

```bash
bash ./scripts/install_mac_mini_zh.sh
```

这个脚本会：

- 检查当前系统是否为 macOS
- 如果缺少 `npm` 且本机有 Homebrew，则自动安装 Node.js
- 自动安装缺失的 `@openai/codex`
- 自动安装缺失的 `@google/gemini-cli`
- 创建 `.venv`
- 安装项目依赖
- 创建 `data`、`logs` 和 `skills` 目录
- 交互式询问 Telegram bot token 和 chat id
- 在输入 bot token 后，先提醒你给 bot 发一次消息；在你确认后，脚本会进入一个短暂等待窗口，此时再给 bot 发送 `/start`，然后自动尝试提取最新的 Telegram `chat.id`
- 如果已经有 bot 进程在运行，安装脚本会提醒你先停掉它，因为运行中的进程可能会先消费 Telegram updates，导致检测不到 `chat.id`
- 如果你选择 `codex_auth`，安装流程会询问是否立即执行 `codex login`
- 如果你选择 `gemini_auth`，安装流程会询问是否立即执行 `gemini` 启动登录；为避免占用当前安装窗口，它会尽量在新的 Terminal 窗口中打开
- 输入后的关键配置项会立刻写入 `config/openclawish.env`，不需要等整段交互结束
- 把这些输入直接写入 `config/openclawish.env`

## 环境变量

必填：

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_ALLOWED_CHAT_IDS="123456789,987654321"
```

可选：

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

## 配置文件

如果你不想每次都手动 `export`，可以直接使用项目提供的配置文件：

```bash
cp ./config/openclawish.env.example ./config/openclawish.env
```

编辑 `./config/openclawish.env` 后，再加载：

```bash
source ./scripts/load_env.sh
```

像 `./data/openclawish.db`、`.`、`./skills` 这样的相对路径，会按仓库根目录来解析。

但日常启动时通常不需要手动执行这一步，因为 `./scripts/start_bot.sh` 已经会自动加载配置文件。

如果你想指定自定义配置文件，也可以这样：

```bash
OPENCLAWISH_ENV_FILE=/path/to/your.env source ./scripts/load_env.sh
```

## 如何获取 `TELEGRAM_ALLOWED_CHAT_IDS`

1. 先在 BotFather 中创建 bot，并保存 bot token。
2. 在 Telegram 里打开这个 bot，发送 `/start`。
3. 执行：

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

4. 在返回结果中找到：

```json
message.chat.id
```

例如：

```json
"chat":{"id":435779584,"first_name":"waves","username":"qq_waves","type":"private"}
```

5. 把这个值写进配置文件：

```bash
TELEGRAM_ALLOWED_CHAT_IDS="435779584"
```

补充说明：

- 私聊的 chat id 通常是正整数
- 群组或超级群的 chat id 可能是负数，常见形态像 `-100...`
- 如果 `getUpdates` 返回空数组，先重新给 bot 发一条新消息，再查一次

如果你想使用 API key 后端，而不是本机 Codex 登录态：

```bash
export OPENCLAWISH_MODEL_BACKEND="api_key"
export OPENAI_MODEL="gpt-5.3-codex"
export OPENAI_API_KEY="..."
```

## 首次启动

```bash
mkdir -p data
bash ./scripts/start_bot.sh
```

也可以直接使用项目自带的启动脚本：

```bash
bash ./scripts/start_bot.sh
```

这个启动脚本还会：

- 自动创建 `data`、`logs`、`artifacts`、`tmp` 目录
- 如果配置文件里还保留占位值，则拒绝启动
- 如果发现已有一个 `openclawish run-bot` 进程在运行，则会先停止旧进程再自动重启

## Telegram 命令

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
- `/goal <自然语言任务>`
- `/task <task_id>`
- 普通文本消息，会自动按 `/goal <消息内容>` 处理

## 模式行为

- `workspace` 模式更安全，适合围绕指定仓库或工作区执行。
- `system` 模式允许命令面向更广泛的 Mac 主机系统。

即使在 `system` 模式下，命令仍然会从 `OPENCLAWISH_WORKSPACE` 作为初始工作目录启动；真正变化的是策略允许范围，而不是默认起始目录。

## 规划后端行为

- `codex_auth` 会先执行 `codex login status`，再以非交互方式调用 `codex exec`。这个项目在该模式下默认使用 `gpt-5.1-codex`，因为它是当前更稳妥的 ChatGPT 账号兼容选择。
- `gemini_auth` 会通过本机 `gemini` CLI 以非交互方式执行规划，适用于本机已经完成 Gemini 登录的情况。
- `api_key` 使用 Python OpenAI SDK
- `fallback` 完全跳过外部模型调用

## 作为 LaunchAgent 运行

可以先自动生成一个用户级 LaunchAgent 模板：

```bash
openclawish print-launchagent --label com.openclawish.bot > ~/Library/LaunchAgents/com.openclawish.bot.plist
```

然后加载：

```bash
launchctl unload ~/Library/LaunchAgents/com.openclawish.bot.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.openclawish.bot.plist
```

同时让工作目录保持在仓库根目录或你指定的主工作区，这样 SQLite 路径和日志路径会更稳定。

## 最小部署检查清单

1. 在 Mac mini 上执行 `codex login status` 能正常返回。
2. `openclawish check` 显示全部 `OK`。
3. Telegram 机器人能正常响应 `/status`。
4. `/backend` 显示为 `codex_auth`。
