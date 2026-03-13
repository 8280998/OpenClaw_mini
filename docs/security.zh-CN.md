# 安全模型

## 威胁模型

这套服务本质上是在给本地机器增加远程执行能力，所以安全控制必须是产品本身的一部分，而不是后补功能。

## 当前保护措施

- 通过 `TELEGRAM_ALLOWED_CHAT_IDS` 做聊天白名单
- 通过 `OPENCLAWISH_WORKSPACE` 限制工作目录
- 通过 `OPENCLAWISH_EXECUTION_MODE` 控制执行范围
- 默认 denylist 拦截破坏性 shell 模式
- 每条命令都有超时限制
- 每个任务都有最大步骤数限制
- 所有行为都会记录到 SQLite 中

## 模式差异

- `workspace` 模式会拒绝访问工作区外的绝对路径，也会拦截 `../` 这类父目录穿越。
- `system` 模式会移除这部分路径范围限制，此时真正的安全边界就变成运行该服务的 macOS 账号权限本身。

## 默认拦截模式

- `rm -rf /`
- `shutdown`
- `reboot`
- `mkfs`
- `dd if=`
- `diskutil eraseDisk`
- `sudo `

这份 denylist 只能看作最低安全基线。正式部署时还应该配合：

- 单独的 macOS 用户账号
- 受限的工作目录树
- 非必要情况下禁用 SSH
- 启用磁盘加密
- 定期轮换密钥
- 轮换 Telegram bot token

## 推荐部署姿态

- 用非管理员账号运行机器人
- 只挂载 agent 实际需要访问的仓库或目录
- 将 OpenAI 和 Telegram 密钥放在 LaunchAgent 环境变量或专门的 secrets manager 中
- 不允许任意 chat ID 访问

## 更高安全等级的演进

如果要进一步提升隔离性，建议把命令执行放进：

- 虚拟机
- 带 bind mount 的容器
- 由独立用户运行的专用 runner 进程

在开放给多个受信任操作者之前，这是非常值得优先做的一步。
