#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export OPENCLAWISH_INSTALL_LANG="zh-CN"

exec "${SCRIPT_DIR}/install_mac_mini.sh" "$@"
