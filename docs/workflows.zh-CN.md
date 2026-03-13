# 工作流示例

## 工作流 1：直接执行 shell 命令

用户发送：

```text
/run git status
```

系统流程：

1. Telegram 适配层验证 chat ID。
2. 服务在 SQLite 中创建任务。
3. 策略层校验 `git status`。
4. 执行器在配置的工作目录中运行该命令。
5. 结果被保存，并通过 Telegram 返回摘要。

## 工作流 2：自然语言目标

用户发送：

```text
/goal 检查仓库并总结测试配置
```

系统流程：

1. Telegram 适配层记录请求。
2. 规划器向 OpenAI 请求一组简短且受限的 shell 计划。
3. 服务逐条验证命令是否符合策略。
4. 执行器按顺序执行这些命令。
5. 最终摘要返回规划结果和命令执行结果。

## 工作流 3：命令被拒绝

用户发送：

```text
/run sudo shutdown -h now
```

系统流程：

1. 策略层命中阻止规则。
2. 任务被记录为 rejected。
3. Telegram 返回拒绝信息和命中的规则。

## 工作流 4：未来审批流

当前 MVP 会直接拒绝被拦截的命令。更接近 OpenClaw 的系统可以改成：

1. 先保存为待审批任务
2. 在 Telegram 中展示 approve / deny 按钮
3. 只有在人工明确批准后才继续执行

## 工作流 5：切换执行模式

用户发送：

```text
/mode system
```

系统流程：

1. Telegram 适配层验证 chat ID。
2. 服务验证请求的模式是否合法。
3. 运行时执行范围切换为 `system`。
4. 之后的 `/run` 和 `/goal` 都会沿用新模式，直到再次切换或服务重启。

## 工作流 6：通过 skill 驱动目标执行

用户发送：

```text
/skill repo_audit 检查仓库并总结风险
```

系统流程：

1. Telegram 适配层验证 chat ID。
2. 服务从本地 skills 目录中加载 `repo_audit`。
3. skill 指令会被拼接到规划提示词前面。
4. 规划器输出受限 shell 计划。
5. 执行器在当前执行模式下运行这些命令。

## 工作流 7：直接发送自然语言

用户发送：

```text
检查仓库并总结风险
```

系统流程：

1. Telegram 适配层验证 chat ID。
2. 普通文本消息会被自动当作 `/goal ...` 处理。
3. 规划器输出受限 shell 计划。
4. 执行器在当前执行模式下运行这些命令。

## 工作流 8：截图 skill

用户发送：

```text
/skill screenshot 截取当前屏幕并保存到 ./artifacts
```

系统流程：

1. Telegram 适配层验证 chat ID。
2. 服务加载内置的 `screenshot` skill。
3. skill 指令会引导规划器优先使用 `screencapture`。
4. 执行器在当前执行模式下运行生成出的截图命令。
5. 如果成功，回复里会带上保存后的文件路径。
