#!/usr/bin/env bash

set -euo pipefail

INSTALL_LANG="${OPENCLAWISH_INSTALL_LANG:-en}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
LOG_DIR="${REPO_ROOT}/logs"
DATA_DIR="${REPO_ROOT}/data"
SKILLS_DIR="${REPO_ROOT}/skills"
ARTIFACTS_DIR="${REPO_ROOT}/artifacts"
TMP_DIR="${REPO_ROOT}/tmp"
CONFIG_DIR="${REPO_ROOT}/config"
ENV_EXAMPLE="${CONFIG_DIR}/openclawish.env.example"
ENV_FILE="${CONFIG_DIR}/openclawish.env"

t() {
  local key="$1"
  case "${INSTALL_LANG}" in
    zh|zh-CN|zh_CN)
      case "${key}" in
        require_macos) printf '%s' '这个安装脚本仅适用于 macOS 的 Mac mini。' ;;
        require_python) printf '%s' '未找到 python3，请先安装。' ;;
        require_npm) printf '%s' '安装 Codex CLI 需要 npm，请先安装 Node.js 或 Homebrew。' ;;
        npm_installing) printf '%s' '未找到 npm，正在通过 Homebrew 安装 Node.js。' ;;
        codex_exists) printf '%s' 'Codex CLI 已安装：' ;;
        codex_install) printf '%s' '未找到 Codex CLI，正在安装 @openai/codex。' ;;
        codex_missing_after_install) printf '%s' '安装后仍未在 PATH 中找到 Codex CLI。' ;;
        gemini_exists) printf '%s' 'Gemini CLI 已安装：' ;;
        gemini_install) printf '%s' '未找到 Gemini CLI，正在安装 @google/gemini-cli。' ;;
        gemini_missing_after_install) printf '%s' '安装后仍未在 PATH 中找到 Gemini CLI。' ;;
        venv_create) printf '%s' '正在创建 Python 虚拟环境。' ;;
        deps_install) printf '%s' '正在安装项目依赖。' ;;
        dirs_prepare) printf '%s' '正在准备运行目录。' ;;
        env_create) printf '%s' '正在创建默认配置文件：' ;;
        env_keep) printf '%s' '保留现有配置文件：' ;;
        env_saved_prefix) printf '%s' '已写入' ;;
        env_saved_to) printf '%s' '到' ;;
        tg_guidance)
          cat <<'EOF'

Telegram 配置说明：
1. 打开 Telegram，和 BotFather 对话。
2. 执行 /newbot 创建你的机器人。
3. BotFather 会返回类似 123456789:AA... 的 bot token。
4. 稍后把这个 token 粘贴到下面的提示中。

如何获取 TELEGRAM_ALLOWED_CHAT_IDS：
1. 在 Telegram 中搜索你的 bot。
2. 给 bot 发送 /start。
3. 在另一个终端中执行：
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
4. 在返回 JSON 中找到 message.chat.id。
EOF
          ;;
        bot_running_1) printf '%s' '检测到 openclawish bot 正在运行。' ;;
        bot_running_2) printf '%s' '运行中的 bot 进程可能会先消费 Telegram updates，导致安装器读不到 chat.id。' ;;
        bot_running_3) printf '%s' '如果自动检测 chat.id 一直失败，请先停止 bot。' ;;
        prompt_bot_token) printf '%s' '请输入 TELEGRAM_BOT_TOKEN' ;;
        before_detect)
          cat <<'EOF'

在自动检测 TELEGRAM_ALLOWED_CHAT_IDS 之前：
1. 打开 Telegram。
2. 找到你的 bot。
3. 当终端提示时，再给 bot 发送一次 /start 或任意消息。
EOF
          ;;
        confirm_sent) printf '%s' '你是否已经从目标聊天窗口给 bot 发过消息？' ;;
        waiting_update_1) printf '%s' '正在等待最新 Telegram update，最多 20 秒。' ;;
        waiting_update_2) printf '%s' '如果你还没有刚刚发送 /start，请现在切到 Telegram 发送。' ;;
        detected_chat) printf '%s' '检测到最新 chat.id：' ;;
        use_detected_chat) printf '%s' '是否使用这个 chat.id 作为 TELEGRAM_ALLOWED_CHAT_IDS？' ;;
        detect_failed_1) printf '%s' '暂时没有自动检测到 chat.id。' ;;
        detect_failed_2) printf '%s' '通常是因为没有新的 update，或被其他 bot 进程先消费了。' ;;
        retry_detect) printf '%s' '现在去给 bot 发 /start 后，再重试一次 chat.id 检测？' ;;
        press_enter_after_start) printf '%s' '给 bot 发送 /start 后按回车继续...' ;;
        skip_detect) printf '%s' '跳过自动检测，你可以手动填写 TELEGRAM_ALLOWED_CHAT_IDS。' ;;
        prompt_chat_ids) printf '%s' '请输入 TELEGRAM_ALLOWED_CHAT_IDS（多个值用逗号分隔）' ;;
        prompt_backend) printf '%s' '选择默认模型后端' ;;
        backend_menu)
          cat <<'EOF'
1) codex_auth
2) gemini_auth
3) api_key
4) fallback
EOF
          ;;
        backend_invalid) printf '%s' '无效选择，请输入 1/2/3/4，或输入后端名称。' ;;
        prompt_openai_model) printf '%s' 'OpenAI 模型（用于 codex_auth/api_key）' ;;
        prompt_gemini_model) printf '%s' 'Gemini 模型（用于 gemini_auth，可留空）' ;;
        prompt_mode) printf '%s' '选择执行权限' ;;
        mode_menu)
          cat <<'EOF'
1) workspace
2) system
EOF
          ;;
        mode_invalid) printf '%s' '无效选择，请输入 1/2，或输入 workspace/system。' ;;
        prompt_workspace) printf '%s' '工作区路径（仓库相对路径或绝对路径）' ;;
        offer_codex_login) printf '%s' '你选择了 codex_auth，现在立即运行 codex login 完成本机浏览器登录吗？' ;;
        offer_gemini_login) printf '%s' '你选择了 gemini_auth，现在立即运行 gemini 启动本机登录流程吗？' ;;
        codex_login_skip) printf '%s' '已跳过 codex login，稍后仍可手动执行。' ;;
        gemini_login_skip) printf '%s' '已跳过 gemini 登录流程，稍后仍可手动执行。' ;;
        codex_login_start) printf '%s' '正在启动 codex login，浏览器可能会自动打开。' ;;
        gemini_login_start) printf '%s' '正在新 Terminal 窗口中启动 gemini 登录流程，浏览器可能会自动打开。' ;;
        gemini_login_wait) printf '%s' '请在新打开的 Terminal 窗口中完成 gemini 登录，完成后回到这里按回车继续。' ;;
        new_terminal_failed) printf '%s' '无法自动打开新的 Terminal 窗口，请手动执行：' ;;
        finished)
          cat <<EOF

安装完成。

后续步骤：
1. 查看生成的配置文件：
   ${ENV_FILE}

2. 如需补做本机 CLI 登录：
   codex login
   gemini

3. 验证登录状态：
   codex login status
   codex exec --help
   gemini --help

4. 启动机器人：
   bash "${REPO_ROOT}/scripts/start_bot.sh"

可选 LaunchAgent 生成：
   "${VENV_DIR}/bin/openclawish" print-launchagent --label com.openclawish.bot > ~/Library/LaunchAgents/com.openclawish.bot.plist
EOF
          ;;
        *)
          printf '%s' "${key}"
          ;;
      esac
      ;;
    *)
      case "${key}" in
        require_macos) printf '%s' 'This installer is intended for macOS on a Mac mini.' ;;
        require_python) printf '%s' 'python3 is required but was not found.' ;;
        require_npm) printf '%s' 'npm is required to install Codex CLI. Install Node.js or Homebrew first.' ;;
        npm_installing) printf '%s' 'npm not found. Installing Node.js via Homebrew.' ;;
        codex_exists) printf '%s' 'Codex CLI already installed:' ;;
        codex_install) printf '%s' 'Codex CLI not found. Installing @openai/codex.' ;;
        codex_missing_after_install) printf '%s' 'Codex CLI was not found on PATH after installation.' ;;
        gemini_exists) printf '%s' 'Gemini CLI already installed:' ;;
        gemini_install) printf '%s' 'Gemini CLI not found. Installing @google/gemini-cli.' ;;
        gemini_missing_after_install) printf '%s' 'Gemini CLI was not found on PATH after installation.' ;;
        venv_create) printf '%s' 'Creating Python virtual environment.' ;;
        deps_install) printf '%s' 'Installing project dependencies.' ;;
        dirs_prepare) printf '%s' 'Preparing runtime directories.' ;;
        env_create) printf '%s' 'Creating default config file at' ;;
        env_keep) printf '%s' 'Keeping existing config file at' ;;
        env_saved_prefix) printf '%s' 'Saved' ;;
        env_saved_to) printf '%s' 'to' ;;
        tg_guidance)
          cat <<'EOF'

Telegram setup guidance:
1. Open Telegram and chat with BotFather.
2. Run /newbot and create your bot.
3. BotFather will return a bot token like 123456789:AA...
4. Paste that token below when prompted.

To get TELEGRAM_ALLOWED_CHAT_IDS:
1. Search for your bot in Telegram.
2. Send /start to the bot.
3. Run this command in another terminal:
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
4. Find message.chat.id in the returned JSON.
EOF
          ;;
        bot_running_1) printf '%s' 'Detected a running openclawish bot process.' ;;
        bot_running_2) printf '%s' 'That process may consume Telegram updates before the installer can read chat.id.' ;;
        bot_running_3) printf '%s' 'Please stop the bot first if automatic chat.id detection keeps failing.' ;;
        prompt_bot_token) printf '%s' 'Enter TELEGRAM_BOT_TOKEN' ;;
        before_detect)
          cat <<'EOF'

Before we try to detect TELEGRAM_ALLOWED_CHAT_IDS automatically:
1. Open Telegram.
2. Find your bot.
3. When prompted, send /start or any message to the bot once.
EOF
          ;;
        confirm_sent) printf '%s' 'Have you already sent a message to the bot from the chat you want to allow?' ;;
        waiting_update_1) printf '%s' 'Waiting up to 20 seconds for a fresh Telegram update.' ;;
        waiting_update_2) printf '%s' 'If you have not just sent /start, switch to Telegram and send it now.' ;;
        detected_chat) printf '%s' 'Detected latest chat.id:' ;;
        use_detected_chat) printf '%s' 'Use detected chat.id as TELEGRAM_ALLOWED_CHAT_IDS?' ;;
        detect_failed_1) printf '%s' 'Could not detect a chat.id automatically yet.' ;;
        detect_failed_2) printf '%s' 'This usually means no fresh update arrived, or another bot process consumed the update first.' ;;
        retry_detect) printf '%s' 'Send /start to the bot now and try detecting chat.id again?' ;;
        press_enter_after_start) printf '%s' 'Press Enter after you have sent /start to the bot...' ;;
        skip_detect) printf '%s' 'Skipping automatic detection. You can fill TELEGRAM_ALLOWED_CHAT_IDS manually.' ;;
        prompt_chat_ids) printf '%s' 'Enter TELEGRAM_ALLOWED_CHAT_IDS (comma-separated if multiple)' ;;
        prompt_backend) printf '%s' 'Choose default model backend' ;;
        backend_menu)
          cat <<'EOF'
1) codex_auth
2) gemini_auth
3) api_key
4) fallback
EOF
          ;;
        backend_invalid) printf '%s' 'Invalid choice. Enter 1/2/3/4 or a backend name.' ;;
        prompt_openai_model) printf '%s' 'OpenAI model for codex_auth/api_key' ;;
        prompt_gemini_model) printf '%s' 'Gemini model for gemini_auth (optional)' ;;
        prompt_mode) printf '%s' 'Choose execution permissions' ;;
        mode_menu)
          cat <<'EOF'
1) workspace
2) system
EOF
          ;;
        mode_invalid) printf '%s' 'Invalid choice. Enter 1/2 or workspace/system.' ;;
        prompt_workspace) printf '%s' 'Workspace path relative to repo or absolute path' ;;
        offer_codex_login) printf '%s' 'You selected codex_auth. Run codex login now to complete local browser sign-in?' ;;
        offer_gemini_login) printf '%s' 'You selected gemini_auth. Run gemini now to start the local login flow?' ;;
        codex_login_skip) printf '%s' 'Skipping codex login for now. You can run it manually later.' ;;
        gemini_login_skip) printf '%s' 'Skipping gemini login for now. You can run it manually later.' ;;
        codex_login_start) printf '%s' 'Starting codex login. Your browser may open for authentication.' ;;
        gemini_login_start) printf '%s' 'Starting gemini login in a new Terminal window. Your browser may open for authentication.' ;;
        gemini_login_wait) printf '%s' 'Finish the gemini login in the new Terminal window, then return here and press Enter to continue.' ;;
        new_terminal_failed) printf '%s' 'Could not open a new Terminal window automatically. Run this command manually:' ;;
        finished)
          cat <<EOF

Installation finished.

Next steps:
1. Review the generated config file:
   ${ENV_FILE}

2. Finish any remaining local CLI logins:
   codex login
   gemini

3. Verify the login:
   codex login status
   codex exec --help
   gemini --help

4. Start the bot:
   bash "${REPO_ROOT}/scripts/start_bot.sh"

Optional LaunchAgent generation:
   "${VENV_DIR}/bin/openclawish" print-launchagent --label com.openclawish.bot > ~/Library/LaunchAgents/com.openclawish.bot.plist
EOF
          ;;
        *)
          printf '%s' "${key}"
          ;;
      esac
      ;;
  esac
}

info() {
  printf '[INFO] %s\n' "$1"
}

warn() {
  printf '[WARN] %s\n' "$1"
}

fail() {
  printf '[ERROR] %s\n' "$1" >&2
  exit 1
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    fail "$(t require_macos)"
  fi
}

ensure_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    fail "$(t require_python)"
  fi
}

ensure_node_and_npm() {
  if command -v npm >/dev/null 2>&1; then
    return
  fi

  if command -v brew >/dev/null 2>&1; then
    info "$(t npm_installing)"
    brew install node
    return
  fi

  fail "$(t require_npm)"
}

install_codex_cli() {
  if command -v codex >/dev/null 2>&1; then
    info "$(t codex_exists) $(command -v codex)"
    return
  fi

  info "$(t codex_install)"
  npm install -g @openai/codex

  if ! command -v codex >/dev/null 2>&1; then
    fail "$(t codex_missing_after_install)"
  fi
}

install_gemini_cli() {
  if command -v gemini >/dev/null 2>&1; then
    info "$(t gemini_exists) $(command -v gemini)"
    return
  fi

  info "$(t gemini_install)"
  npm install -g @google/gemini-cli

  if ! command -v gemini >/dev/null 2>&1; then
    fail "$(t gemini_missing_after_install)"
  fi
}

setup_python_env() {
  info "$(t venv_create)"
  python3 -m venv "${VENV_DIR}"

  info "$(t deps_install)"
  "${VENV_DIR}/bin/pip" install --upgrade pip
  "${VENV_DIR}/bin/pip" install -e "${REPO_ROOT}[dev]"
}

prepare_dirs() {
  info "$(t dirs_prepare)"
  mkdir -p "${LOG_DIR}" "${DATA_DIR}" "${SKILLS_DIR}" "${ARTIFACTS_DIR}" "${TMP_DIR}" "${CONFIG_DIR}"
}

prepare_env_file() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    info "$(t env_create) ${ENV_FILE}."
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  else
    info "$(t env_keep) ${ENV_FILE}."
  fi
}

prompt_value() {
  local prompt_text="$1"
  local default_value="$2"
  local user_value

  if [[ -n "${default_value}" ]]; then
    read -r -p "${prompt_text} [${default_value}]: " user_value
    if [[ -z "${user_value}" ]]; then
      user_value="${default_value}"
    fi
  else
    read -r -p "${prompt_text}: " user_value
  fi

  printf '%s' "${user_value}"
}

prompt_confirm() {
  local prompt_text="$1"
  local default_value="${2:-Y}"
  local suffix="[1/2]"
  local user_value

  if [[ "${default_value}" == "N" ]]; then
    suffix="[2/1]"
  fi

  printf '%s\n' "${prompt_text}"
  if [[ "${INSTALL_LANG}" == "zh" || "${INSTALL_LANG}" == "zh-CN" || "${INSTALL_LANG}" == "zh_CN" ]]; then
    printf '1) 是\n2) 否\n'
  else
    printf '1) Yes\n2) No\n'
  fi
  read -r -p "> ${suffix}: " user_value
  user_value="${user_value:-${default_value}}"
  case "${user_value}" in
    1|Y|y) return 0 ;;
    2|N|n) return 1 ;;
    *)
      [[ "${default_value}" =~ ^[Yy]$ ]]
      ;;
  esac
}

update_env_value() {
  local key="$1"
  local value="$2"
  local tmp_file
  tmp_file="$(mktemp)"

  awk -v key="${key}" -v value="${value}" '
    BEGIN { done = 0 }
    index($0, key "=") == 1 {
      print key "=\"" value "\""
      done = 1
      next
    }
    { print }
    END {
      if (!done) {
        print key "=\"" value "\""
      }
    }
  ' "${ENV_FILE}" > "${tmp_file}"
  mv "${tmp_file}" "${ENV_FILE}"
}

persist_env_value() {
  local key="$1"
  local value="$2"
  update_env_value "${key}" "${value}"
  info "$(t env_saved_prefix) ${key} $(t env_saved_to) ${ENV_FILE}"
}

normalize_backend_choice() {
  local value="$1"
  case "${value}" in
    1) printf '%s' 'codex_auth' ;;
    2) printf '%s' 'gemini_auth' ;;
    3) printf '%s' 'api_key' ;;
    4) printf '%s' 'fallback' ;;
    openai|codex) printf '%s' 'codex_auth' ;;
    gemini) printf '%s' 'gemini_auth' ;;
    codex_auth|gemini_auth|api_key|fallback) printf '%s' "${value}" ;;
    *) return 1 ;;
  esac
}

backend_default_choice() {
  local backend="$1"
  case "${backend}" in
    codex_auth|openai|codex|"") printf '%s' '1' ;;
    gemini_auth|gemini) printf '%s' '2' ;;
    api_key) printf '%s' '3' ;;
    fallback) printf '%s' '4' ;;
    *) printf '%s' '1' ;;
  esac
}

prompt_backend_choice() {
  local current_backend="$1"
  local default_choice user_choice normalized
  default_choice="$(backend_default_choice "${current_backend}")"

  while true; do
    printf '%s\n' "$(t prompt_backend)"
    t backend_menu
    user_choice="$(prompt_value ">" "${default_choice}")"
    normalized="$(normalize_backend_choice "${user_choice}" || true)"
    if [[ -n "${normalized}" ]]; then
      printf '%s' "${normalized}"
      return 0
    fi
    warn "$(t backend_invalid)"
  done
}

normalize_mode_choice() {
  local value="$1"
  case "${value}" in
    1) printf '%s' 'workspace' ;;
    2) printf '%s' 'system' ;;
    workspace|system) printf '%s' "${value}" ;;
    *) return 1 ;;
  esac
}

mode_default_choice() {
  local mode="$1"
  case "${mode}" in
    workspace|"") printf '%s' '1' ;;
    system) printf '%s' '2' ;;
    *) printf '%s' '1' ;;
  esac
}

prompt_mode_choice() {
  local current_mode="$1"
  local default_choice user_choice normalized
  default_choice="$(mode_default_choice "${current_mode}")"

  while true; do
    printf '%s\n' "$(t prompt_mode)"
    t mode_menu
    user_choice="$(prompt_value ">" "${default_choice}")"
    normalized="$(normalize_mode_choice "${user_choice}" || true)"
    if [[ -n "${normalized}" ]]; then
      printf '%s' "${normalized}"
      return 0
    fi
    warn "$(t mode_invalid)"
  done
}

read_existing_env_value() {
  local key="$1"
  awk -F'"' -v key="${key}" 'index($0, key "=") == 1 { print $2; exit }' "${ENV_FILE}"
}

show_telegram_guidance() {
  t tg_guidance
}

warn_if_bot_running() {
  if pgrep -f "openclawish run-bot" >/dev/null 2>&1; then
    warn "$(t bot_running_1)"
    warn "$(t bot_running_2)"
    warn "$(t bot_running_3)"
  fi
}

fetch_latest_chat_id() {
  local bot_token="$1"
  local timeout_seconds="${2:-0}"
  local response
  local latest_chat_id

  response="$(
    curl -fsS \
      --max-time "$((timeout_seconds + 10))" \
      "https://api.telegram.org/bot${bot_token}/getUpdates?timeout=${timeout_seconds}" \
      2>/dev/null || true
  )"
  if [[ -z "${response}" ]]; then
    return 1
  fi

  latest_chat_id="$(
    printf '%s' "${response}" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)
result = data.get("result") or []
if not result:
    sys.exit(2)

def extract_chat_id(item):
    message = item.get("message") or item.get("edited_message") or item.get("channel_post")
    if message:
        chat = message.get("chat") or {}
        if chat.get("id") is not None:
            return chat.get("id")
    callback = item.get("callback_query") or {}
    message = callback.get("message") or {}
    chat = message.get("chat") or {}
    if chat.get("id") is not None:
        return chat.get("id")
    member = item.get("my_chat_member") or item.get("chat_member") or {}
    chat = member.get("chat") or {}
    if chat.get("id") is not None:
        return chat.get("id")
    return None

for item in reversed(result):
    chat_id = extract_chat_id(item)
    if chat_id is not None:
        print(chat_id)
        sys.exit(0)
sys.exit(3)
' 2>/dev/null
  )" || true

  if [[ -z "${latest_chat_id}" ]]; then
    return 1
  fi

  printf '%s' "${latest_chat_id}"
}

run_in_new_terminal_window() {
  local command_text="$1"
  local escaped_command

  escaped_command="$(printf '%s' "${command_text}" | sed 's/\\/\\\\/g; s/"/\\"/g')"
  osascript <<EOF >/dev/null
tell application "Terminal"
  activate
  do script "${escaped_command}"
end tell
EOF
}

maybe_run_backend_login() {
  local backend="$1"
  case "${backend}" in
    codex_auth|openai)
      if prompt_confirm "$(t offer_codex_login)" "Y"; then
        info "$(t codex_login_start)"
        codex login
      else
        warn "$(t codex_login_skip)"
      fi
      ;;
    gemini_auth|gemini)
      if prompt_confirm "$(t offer_gemini_login)" "Y"; then
        info "$(t gemini_login_start)"
        if run_in_new_terminal_window "cd \"${REPO_ROOT}\" && gemini"; then
          read -r -p "$(t gemini_login_wait)" _
        else
          warn "$(t new_terminal_failed) gemini"
        fi
      else
        warn "$(t gemini_login_skip)"
      fi
      ;;
  esac
}

configure_env_interactively() {
  local current_bot_token current_chat_ids current_backend current_openai_model current_gemini_model current_mode current_workspace
  current_bot_token="$(read_existing_env_value "TELEGRAM_BOT_TOKEN")"
  current_chat_ids="$(read_existing_env_value "TELEGRAM_ALLOWED_CHAT_IDS")"
  current_backend="$(read_existing_env_value "OPENCLAWISH_MODEL_BACKEND")"
  current_openai_model="$(read_existing_env_value "OPENAI_MODEL")"
  current_gemini_model="$(read_existing_env_value "GEMINI_MODEL")"
  current_mode="$(read_existing_env_value "OPENCLAWISH_EXECUTION_MODE")"
  current_workspace="$(read_existing_env_value "OPENCLAWISH_WORKSPACE")"

  show_telegram_guidance

  local bot_token chat_ids backend openai_model gemini_model execution_mode workspace
  bot_token="$(prompt_value "$(t prompt_bot_token)" "${current_bot_token}")"
  persist_env_value "TELEGRAM_BOT_TOKEN" "${bot_token}"

  local detected_chat_id=""
  if [[ -n "${bot_token}" ]]; then
    warn_if_bot_running
    t before_detect

    if prompt_confirm "$(t confirm_sent)" "Y"; then
      while true; do
        info "$(t waiting_update_1)"
        info "$(t waiting_update_2)"
        detected_chat_id="$(fetch_latest_chat_id "${bot_token}" "20" || true)"
        if [[ -n "${detected_chat_id}" ]]; then
          info "$(t detected_chat) ${detected_chat_id}"
          if prompt_confirm "$(t use_detected_chat)" "Y"; then
            chat_ids="${detected_chat_id}"
            persist_env_value "TELEGRAM_ALLOWED_CHAT_IDS" "${chat_ids}"
          fi
          break
        fi

        warn "$(t detect_failed_1)"
        warn "$(t detect_failed_2)"
        if prompt_confirm "$(t retry_detect)" "Y"; then
          read -r -p "$(t press_enter_after_start)" _
          continue
        fi
        warn "$(t skip_detect)"
        break
      done
    fi
  fi

  chat_ids="${chat_ids:-$(prompt_value "$(t prompt_chat_ids)" "${current_chat_ids}")}"
  persist_env_value "TELEGRAM_ALLOWED_CHAT_IDS" "${chat_ids}"

  backend="$(prompt_backend_choice "${current_backend:-codex_auth}")"
  persist_env_value "OPENCLAWISH_MODEL_BACKEND" "${backend}"

  openai_model="$(prompt_value "$(t prompt_openai_model)" "${current_openai_model:-gpt-5.1-codex}")"
  persist_env_value "OPENAI_MODEL" "${openai_model}"

  gemini_model="$(prompt_value "$(t prompt_gemini_model)" "${current_gemini_model}")"
  persist_env_value "GEMINI_MODEL" "${gemini_model}"

  execution_mode="$(prompt_mode_choice "${current_mode:-workspace}")"
  persist_env_value "OPENCLAWISH_EXECUTION_MODE" "${execution_mode}"

  workspace="$(prompt_value "$(t prompt_workspace)" "${current_workspace:-.}")"
  persist_env_value "OPENCLAWISH_WORKSPACE" "${workspace}"

  maybe_run_backend_login "${backend}"
}

print_next_steps() {
  t finished
}

main() {
  require_macos
  ensure_python
  ensure_node_and_npm
  install_codex_cli
  install_gemini_cli
  setup_python_env
  prepare_dirs
  prepare_env_file
  configure_env_interactively
  print_next_steps
}

main "$@"
