#!/usr/bin/env bash

_openclawish_load_env_fail() {
  echo "$1" >&2
  return 1 2>/dev/null || exit 1
}

if [ -n "${ZSH_VERSION:-}" ]; then
  eval 'OPENCLAWISH_SCRIPT_PATH="${(%):-%x}"'
else
  OPENCLAWISH_SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
fi

OPENCLAWISH_SCRIPT_DIR="$(cd "$(dirname "${OPENCLAWISH_SCRIPT_PATH}")" && pwd)"
OPENCLAWISH_REPO_ROOT="$(cd "${OPENCLAWISH_SCRIPT_DIR}/.." && pwd)"
OPENCLAWISH_ENV_FILE="${OPENCLAWISH_ENV_FILE:-${OPENCLAWISH_REPO_ROOT}/config/openclawish.env}"
export OPENCLAWISH_BASE_DIR="${OPENCLAWISH_REPO_ROOT}"

if [ ! -f "${OPENCLAWISH_ENV_FILE}" ]; then
  _openclawish_load_env_fail "Environment file not found: ${OPENCLAWISH_ENV_FILE}"
fi

set -a
# shellcheck disable=SC1090
. "${OPENCLAWISH_ENV_FILE}"
set +a

echo "Loaded ${OPENCLAWISH_ENV_FILE}"
