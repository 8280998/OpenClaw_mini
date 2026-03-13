# OpenClaw_mini

OpenClaw_mini 是一套部署在 Mac mini 上、以 OpenClaw 为参考目标构建的本地 Agent 系统。它通过 Telegram 接收指令，在本地完成规划或执行任务，把任务、日志和状态写入 SQLite，并且可以通过本机已登录的 Codex CLI 或 OpenAI Responses API 获得任务规划能力。

当前 Python 包名和命令行入口仍然是 `openclawish`，但公开仓库名称可以使用 `OpenClaw_mini`。

This repository also keeps the original English documentation. See [README.md](./README.md).

## 当前项目目标

这个仓库目前实现的是一个务实的第一阶段版本：

- Telegram 机器人从受信任聊天中接收命令
- 服务端记录任务并执行安全检查
- 在受控工作目录中执行本地 shell 命令
- 可以调用本机已登录的 Codex CLI，或者调用 OpenAI 模型，把自然语言目标转换成命令计划
- 将结果、状态和执行日志保存下来，方便审计和追踪

## 仓库包含内容

- 可部署在 Mac mini 或常驻机器上的 Python 服务
- 基于 Telegram long polling 的远程控制入口
- 使用 SQLite 存储任务、事件和命令执行历史
- 带有基础 allowlist / denylist 思路的 shell 执行层
- 支持 `codex_auth`、`gemini_auth`、`api_key` 和 `fallback` 的规划后端
- 覆盖架构、部署、运维和安全的完整文档

## 当前能力范围

这是一个偏向 OpenClaw 风格控制面的 MVP，而不是完整桌面自治系统。当前已经支持：

- 远程提交任务
- 本地 shell 执行
- 任务持久化与审计日志
- OpenAI 辅助规划
- 对高风险命令进行基础拦截

当前还不包含：

- 原生 macOS GUI 自动化
- 浏览器自动控制
- 多 Agent 拆解
- 桌面截图流
- 超出 Telegram 指令流之外的人机审批界面

## 快速开始

1. 在 Mac mini 上安装 Codex CLI 并完成登录。
2. 如果你想使用 `gemini_auth`，也安装 Gemini CLI。
3. 使用 BotFather 创建 Telegram 机器人并获得 token。
4. 运行安装脚本：

```bash
bash ./scripts/install_mac_mini_zh.sh
```

如果你更喜欢英文提示，也可以使用：

```bash
bash ./scripts/install_mac_mini.sh
```

安装脚本会自动检查并安装缺失的 Codex CLI 或 Gemini CLI，写入 `config/openclawish.env`，尝试检测 Telegram `chat.id`，并在你选择 `codex_auth` 或 `gemini_auth` 时询问是否立刻执行对应登录流程。

5. 确认本机登录态可用：

```bash
codex login status
codex exec --help
gemini --help
```

6. 获取 Telegram `chat.id`，并填写 `TELEGRAM_ALLOWED_CHAT_IDS`

先在 Telegram 里给你的 bot 发送 `/start`，然后执行：

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

在返回结果里找到：

```json
message.chat.id
```

例如：

```json
"chat":{"id":xxx,"first_name":"xxx","xxx":"xxx","type":"private"}
```

那么你就应该填写：

```bash
TELEGRAM_ALLOWED_CHAT_IDS="xxxx"
```

7. 创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

8. 启动服务：

```bash
bash ./scripts/start_bot.sh
```

9. 在 Telegram 中发送命令：

```text
/help
/status
/permissions
/permissions system
/models
/models gemini
/run ls
/goal 检查仓库并总结测试结构
检查仓库并总结测试结构
```

## 执行模式

OpenClaw_mini 现在支持两种执行模式：

- `workspace`：阻止命令通过绝对路径或父目录跳转离开设定工作区。
- `system`：保留相同的默认工作目录，但允许命令面向更广泛的 macOS 系统路径和资源。

可以通过环境变量设置启动默认模式：

```bash
export OPENCLAWISH_EXECUTION_MODE="workspace"
```

运行过程中也可以在 Telegram 里用 `/mode workspace` 或 `/mode system` 实时切换。

## 规划后端

OpenClaw_mini 支持四种规划后端：

- `codex_auth`：默认方式。通过非交互模式调用本机已登录的 `codex` CLI。
- `gemini_auth`：通过非交互模式调用本机已登录的 `gemini` CLI。
- `api_key`：通过 `OPENAI_API_KEY` 调用 OpenAI SDK。
- `fallback`：不访问外部模型，只使用一个非常轻量的静态检查计划。

可以通过下面的环境变量指定后端：

```bash
export OPENCLAWISH_MODEL_BACKEND="codex_auth"
```

`codex_auth` 使用的是 Mac mini 本机 `codex` CLI 的登录态，不要求必须安装 Codex 桌面版。在这个模式下，项目现在默认使用 `gpt-5.1-codex`，这是当前更稳妥的 ChatGPT 账号登录兼容选择。

`gemini_auth` 使用的是本机 `gemini` CLI 登录态。你可以在 Telegram 里通过 `/backend gemini` 切过去，再通过 `/backend openai` 切回 OpenAI/Codex 路线。
你也可以使用更直观的别名命令 `/models gemini` 和 `/models openai`。

## 内置 skill 机制

OpenClaw_mini 现在带有一套应用级 skill 机制，可以通过本地预设能力文件扩展行为。

- `/skills` 列出当前已安装的 skill
- `/skill repo_audit 检查仓库并总结风险`
- `/skill system_ops 检查 launch agent 和最近系统状态`
- `/skill screenshot 截取当前屏幕并保存到 ./artifacts`

这些 skill 从 [`./skills/`](./skills/) 目录加载。每个 skill 都是一个 JSON 文件，包含：

- `name`
- `description`
- `prompt_prefix`
- 可选的 `suggested_mode`

这套机制和 Codex 会话级 skill 不是一回事。它是专门给这个 Telegram Agent 服务扩展行为用的运行时能力包机制。

## 部署辅助命令

启动机器人前，可以先执行：

```bash
openclawish check
```

如果要生成 LaunchAgent 配置：

```bash
openclawish print-launchagent --label com.openclawish.bot > ~/Library/LaunchAgents/com.openclawish.bot.plist
```

如果你想在 Mac mini 上一条命令完成基础安装，可以执行：

```bash
bash ./scripts/install_mac_mini.sh
```

这个安装脚本现在是交互式的。它会先检查 `codex` 和 `gemini` CLI 是否已安装，缺失时自动安装，然后依次提示你输入：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_CHAT_IDS`
- 默认后端与模型设置
- 执行权限和工作区

在你输入 bot token 后，安装脚本会先提醒你去 Telegram 给 bot 发送一次 `/start`，然后在你确认后自动尝试提取最新的 `chat.id`。

日常启动机器人时，可以直接执行：

```bash
bash ./scripts/start_bot.sh
```

`start_bot.sh` 已经包含了激活 `.venv`、加载 `config/openclawish.env`、执行 `openclawish check` 和启动机器人的步骤。
它还会自动创建运行目录、拦截占位配置值，并在发现已有旧 bot 进程时自动先停止再重启。

默认配置模板位于 [`./config/openclawish.env.example`](./config/openclawish.env.example)。
该文件中的相对路径会按仓库根目录解析。

## 首次公开前检查

- 在推送到 GitHub 之前，请先检查 [`docs/first-commit-checklist.zh-CN.md`](./docs/first-commit-checklist.zh-CN.md)。

## 文档导航

英文文档：

- [System overview](./docs/architecture.md)
- [Setup guide](./docs/setup.md)
- [Operations guide](./docs/operations.md)
- [Security model](./docs/security.md)
- [Product workflow](./docs/workflows.md)
- [Skill development](./docs/skills.md)

中文文档：

- [系统概览](./docs/architecture.zh-CN.md)
- [部署指南](./docs/setup.zh-CN.md)
- [运维说明](./docs/operations.zh-CN.md)
- [安全模型](./docs/security.zh-CN.md)
- [工作流示例](./docs/workflows.zh-CN.md)
- [Skill 开发](./docs/skills.zh-CN.md)

## OpenAI 参考

当前规划器基于 OpenAI Responses API，目标是支撑以编码和自动化执行为主的 Agent 工作流。官方参考：

- [Responses API 概览](https://developers.openai.com/api)
- [GPT-5-Codex 模型](https://developers.openai.com/api/docs/models/gpt-5-codex)
- [computer-use-preview 模型](https://developers.openai.com/api/docs/models/computer-use-preview)
