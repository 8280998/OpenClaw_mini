# Operations Guide

## Day-to-day workflow

1. Start the bot service on the Mac mini.
2. Send `/status` to verify connectivity.
3. Use `/backend` and `/mode` to confirm runtime backend and execution scope.
4. Use `/run` for exact shell commands.
5. Use `/goal` or plain text for higher-level instructions that need planning.
6. Use `/skills` and `/skill` when you want a reusable preset.
7. Use `/task <id>` to inspect a stored task and its results.

## Observability

Every task stores:

- the requester chat ID
- original input
- current status
- planner output
- executed commands
- stdout and stderr
- timestamps

This data lives in SQLite, which is enough for a single-machine deployment. When you need multi-user or higher throughput, move the same schema to Postgres.

## Failure handling

Planner failures:

- task remains recorded
- service reports the error back to Telegram
- direct `/run` execution remains available

Command failures:

- non-zero exit code is stored
- stderr is returned in the Telegram summary
- later commands in the same goal stop by default

## Upgrade path

The easiest next upgrades are:

- add a queue worker so Telegram handlers stay responsive
- stream partial output back to Telegram
- add inline approval buttons for blocked commands
- attach files and logs as Telegram documents
- support remote git checkout and branch workflows

## Skill operations

Application skills are local JSON presets. To add one:

1. Drop a new `*.json` file into the configured skills directory.
2. Include `name`, `description`, and `prompt_prefix`.
3. Restart the bot, or add a future reload command if you want hot reload.
