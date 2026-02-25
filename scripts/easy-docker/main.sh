#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/easy-docker/lib/env.sh
source "${SCRIPT_DIR}/lib/env.sh"
# shellcheck source=scripts/easy-docker/lib/ui.sh
source "${SCRIPT_DIR}/lib/ui.sh"

print_usage() {
  cat <<'USAGE'
Usage: bash easy-docker.sh [options]

Options:
  --no-github-binary-fallback  Disable GitHub binary fallback prompt
  -h, --help                   Show this help
USAGE
}

DISABLE_GITHUB_BINARY_FALLBACK=0

while [ "$#" -gt 0 ]; do
  case "$1" in
  --no-github-binary-fallback)
    DISABLE_GITHUB_BINARY_FALLBACK=1
    ;;
  -h | --help)
    print_usage
    exit 0
    ;;
  *)
    echo "Unknown option: $1"
    print_usage
    exit 1
    ;;
  esac
  shift
done

ensure_gum "${DISABLE_GITHUB_BINARY_FALLBACK}"

ALT_SCREEN_ACTIVE=0

enter_alt_screen() {
  if [ -t 1 ] && command -v tput >/dev/null 2>&1; then
    tput smcup || true
    tput civis || true
    ALT_SCREEN_ACTIVE=1
  fi
}

leave_alt_screen() {
  if [ "${ALT_SCREEN_ACTIVE}" = "1" ] && command -v tput >/dev/null 2>&1; then
    tput cnorm || true
    tput rmcup || true
    ALT_SCREEN_ACTIVE=0
  fi
}

cleanup_screen() {
  leave_alt_screen
}

cleanup_and_exit() {
  exit 0
}

trap cleanup_and_exit INT TERM
trap cleanup_screen EXIT

enter_alt_screen

render_main_screen 1

while true; do
  local_env_action=""
  action="$(show_main_menu || true)"

  if [ -z "${action}" ]; then
    cleanup_and_exit
  fi

  case "${action}" in
  "Environment check")
    local_env_action="$(show_environment_status || true)"
    case "${local_env_action}" in
    "Back to main menu" | "")
      render_main_screen 1
      ;;
    "Exit and close easy-docker")
      cleanup_and_exit
      ;;
    *)
      gum style --foreground 214 "Unknown environment action: ${local_env_action}"
      sleep 1
      ;;
    esac
    ;;
  "Exit")
    cleanup_and_exit
    ;;
  *)
    gum style --foreground 214 "Unknown action: ${action}"
    sleep 1
    ;;
  esac
done
