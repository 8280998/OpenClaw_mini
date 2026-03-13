# 首次提交清单

- 确认 `config/openclawish.env` 没有被纳入版本控制。
- 确认 `.venv/`、`data/`、`logs/`、`artifacts/`、`tmp/`、`tmp_smoke/` 都已被忽略。
- 如果本地测试用过真实 Telegram bot token，在公开仓库前先轮换一次。
- 用 `git diff --cached` 检查暂存区，确认没有本机绝对路径或敏感信息。
- 确认 README 中的链接都使用相对路径，并且在 GitHub 上可正常打开。
- 执行 `python3 -m compileall src tests`。
- 如果本地开发环境完整，建议再执行一次 `pytest`。
- 在 GitHub 上创建名为 `OpenClaw_mini` 的仓库。
- 完成首次干净提交后，再推送默认分支。
