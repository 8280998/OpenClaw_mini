# Workflows

## Workflow 1: Direct shell command

User sends:

```text
/run git status
```

System flow:

1. Telegram adapter validates the chat ID.
2. Service creates a task in SQLite.
3. Policy validates `git status`.
4. Executor runs the command in the configured workspace.
5. Result is stored and summarized back to Telegram.

## Workflow 2: Natural-language goal

User sends:

```text
/goal inspect the repository and summarize the testing setup
```

System flow:

1. Telegram adapter stores the request.
2. Planner asks OpenAI for a short bounded shell plan.
3. Service validates each command against policy.
4. Executor runs commands one by one.
5. The final summary includes the planner output and command results.

## Workflow 3: Rejected command

User sends:

```text
/run sudo shutdown -h now
```

System flow:

1. Policy matches a blocked pattern.
2. Task is recorded as rejected.
3. Telegram returns a refusal message with the matching rule.

## Workflow 4: Future approval flow

The current MVP rejects blocked commands. A richer OpenClaw-like system can instead:

1. store a pending approval request
2. show Telegram inline approve and deny buttons
3. re-run the task only after explicit approval

## Workflow 5: Mode switch

User sends:

```text
/mode system
```

System flow:

1. Telegram adapter validates the chat ID.
2. Service validates the requested mode.
3. Runtime execution scope switches to `system`.
4. Later `/run` and `/goal` tasks use the new mode until changed again or restarted.

## Workflow 6: Skill-driven goal

User sends:

```text
/skill repo_audit inspect the repository and summarize its risks
```

System flow:

1. Telegram adapter validates the chat ID.
2. Service loads the `repo_audit` skill from the local skills directory.
3. Skill instructions are prepended to the planning prompt.
4. Planner creates a bounded shell plan.
5. Executor runs the resulting commands under the current execution mode.

## Workflow 7: Plain-text natural language

User sends:

```text
Inspect the repository and summarize its risks
```

System flow:

1. Telegram adapter validates the chat ID.
2. The plain-text message is routed as if the user had sent `/goal ...`.
3. Planner creates a bounded shell plan.
4. Executor runs the resulting commands under the current execution mode.

## Workflow 8: Screenshot skill

User sends:

```text
/skill screenshot capture the current screen and save it under ./artifacts
```

System flow:

1. Telegram adapter validates the chat ID.
2. Service loads the built-in `screenshot` skill.
3. Skill instructions steer the planner toward `screencapture`.
4. Executor runs the generated screenshot command under the current execution mode.
5. The reply includes the saved file path if the command succeeds.
