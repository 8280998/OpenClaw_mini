# Skill Development

## What skills are in this project

OpenClawish skills are local JSON presets used by the application at runtime. They are not the same thing as Codex session skills from the desktop app.

## Skill file format

Each file in the configured skills directory should look like this:

```json
{
  "name": "repo_audit",
  "description": "Inspect a repository and summarize risks.",
  "prompt_prefix": "Prefer read-only repository inspection commands.",
  "suggested_mode": "workspace"
}
```

## Fields

- `name`: the command name used in `/skill <name> ...`
- `description`: shown in `/skills`
- `prompt_prefix`: prepended to the goal before planning
- `suggested_mode`: optional hint for operators

## Current behavior

- Skills are loaded at startup from `OPENCLAWISH_SKILLS_DIR`
- `/skills` lists installed skills
- `/skill <name> <goal>` runs the planner with the skill prefix attached

## Good skill ideas

- repository audit
- test triage
- macOS system inspection
- screenshots and visual capture
- deployment checklists
- incident response triage

## Built-in screenshot skill

This repository now ships a default `screenshot` skill in [`./skills/screenshot.json`](../skills/screenshot.json).

Example:

```text
/skill screenshot capture the current screen and save it under ./artifacts
```

This skill is designed for macOS and steers the planner toward the built-in `screencapture` command.
