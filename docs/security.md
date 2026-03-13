# Security Model

## Threat model

This service gives remote command capability to a local machine. That makes safety controls part of the product, not an afterthought.

## Current protections

- Chat allowlist via `TELEGRAM_ALLOWED_CHAT_IDS`
- Workspace scoping via `OPENCLAWISH_WORKSPACE`
- Configurable execution scope via `OPENCLAWISH_EXECUTION_MODE`
- Default denylist for destructive shell patterns
- Per-command timeout
- Per-task step limit
- Full audit logging in SQLite

## Mode-specific behavior

- `workspace` mode rejects absolute paths outside the configured workspace and blocks parent traversal such as `../`.
- `system` mode removes those path-scope checks, so host permissions become the real security boundary.

## Default blocked patterns

- `rm -rf /`
- `shutdown`
- `reboot`
- `mkfs`
- `dd if=`
- `diskutil eraseDisk`
- `sudo `

You should treat this denylist as a minimum baseline. In production, pair it with:

- a dedicated macOS user account
- a restricted workspace tree
- SSH disabled unless required
- disk encryption
- secret rotation
- Telegram bot token rotation

## Recommended deployment stance

- run the bot under a non-admin account
- only mount the repositories or folders the agent actually needs
- keep OpenAI and Telegram secrets in the LaunchAgent environment or a secrets manager
- never allow arbitrary chat IDs

## Moving toward higher assurance

For stronger isolation, execute commands in:

- a VM
- a container with bind-mounted repos
- a dedicated runner process under a separate user

That is the right step before exposing the system to more than one trusted operator.
