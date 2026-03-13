# Skill 开发

## 这个项目里的 skill 是什么

OpenClawish 的 skill 是运行时由应用加载的本地 JSON 预设，它和 Codex 桌面应用里的会话级 skill 不是同一个概念。

## Skill 文件格式

放在配置好的 skills 目录中的每个文件，可以像这样：

```json
{
  "name": "repo_audit",
  "description": "检查仓库并总结风险。",
  "prompt_prefix": "优先使用只读的仓库检查命令。",
  "suggested_mode": "workspace"
}
```

## 字段说明

- `name`：在 `/skill <name> ...` 中使用的名称
- `description`：会显示在 `/skills`
- `prompt_prefix`：在规划前拼接到用户目标前面的提示词
- `suggested_mode`：可选，给操作者的模式建议

## 当前行为

- skill 会在启动时从 `OPENCLAWISH_SKILLS_DIR` 加载
- `/skills` 用于列出已安装的 skill
- `/skill <name> <goal>` 会带着 skill 前缀去执行规划

## 适合的 skill 类型

- 仓库审计
- 测试排查
- macOS 系统巡检
- 截图与视觉采集
- 部署检查清单
- 故障响应排查

## 内置 screenshot skill

这个仓库现在已经默认附带一个 `screenshot` skill，文件位于 [`./skills/screenshot.json`](../skills/screenshot.json)。

使用示例：

```text
/skill screenshot 截取当前屏幕并保存到 ./artifacts
```

这个 skill 面向 macOS，默认会引导规划器优先使用系统自带的 `screencapture` 命令。
