#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${OPENCLAWISH_ENV_FILE:-${REPO_ROOT}/config/openclawish.env}"

cd "${REPO_ROOT}"

if [[ ! -d "${REPO_ROOT}/.venv" ]]; then
  echo "Virtual environment not found at ${REPO_ROOT}/.venv" >&2
  echo "Run: bash ./scripts/install_mac_mini.sh" >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Config file not found: ${ENV_FILE}" >&2
  echo "Create it from ./config/openclawish.env.example first." >&2
  exit 1
fi

mkdir -p "${REPO_ROOT}/data" "${REPO_ROOT}/logs" "${REPO_ROOT}/artifacts" "${REPO_ROOT}/tmp"

if grep -q 'replace_with_your_telegram_bot_token' "${ENV_FILE}"; then
  echo "Config file still contains the placeholder TELEGRAM_BOT_TOKEN." >&2
  echo "Edit ${ENV_FILE} before starting the bot." >&2
  exit 1
fi

if pgrep -f "openclawish run-bot" >/dev/null 2>&1; then
  echo "Existing OpenClawish bot process detected. Restarting..."
  pkill -f "openclawish run-bot"
  sleep 1
fi

# shellcheck disable=SC1091
source "${REPO_ROOT}/.venv/bin/activate"
# shellcheck disable=SC1091
source "${REPO_ROOT}/scripts/load_env.sh"

echo "启动配置："
echo "  backend=${OPENCLAWISH_MODEL_BACKEND:-}"
echo "  mode=${OPENCLAWISH_EXECUTION_MODE:-}"
echo "  workspace=${OPENCLAWISH_WORKSPACE:-}"
echo "  openai_model=${OPENAI_MODEL:-}"
echo "  gemini_model=${GEMINI_MODEL:-}"
echo "  chat_ids=${TELEGRAM_ALLOWED_CHAT_IDS:-}"

echo "Running startup checks..."
openclawish check

echo "Starting OpenClawish bot..."
exec openclawish run-bot
