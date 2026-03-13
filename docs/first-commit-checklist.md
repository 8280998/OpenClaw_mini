# First Commit Checklist

- Confirm `config/openclawish.env` is not tracked.
- Confirm `.venv/`, `data/`, `logs/`, `artifacts/`, `tmp/`, and `tmp_smoke/` are ignored.
- Rotate any Telegram bot token used during local testing before making the repository public.
- Review `git diff --cached` to ensure no local absolute paths or machine-specific secrets remain.
- Verify README links are relative and still work on GitHub.
- Run `python3 -m compileall src tests`.
- Optionally run the test suite in a dev environment with `pytest`.
- Create the GitHub repository as `OpenClaw_mini`.
- Push the default branch after the first clean commit.
