#!/usr/bin/env bash

render_main_screen() {
  local clear_screen="${1:-0}"
  local header_text=""

  if [ "${clear_screen}" = "1" ]; then
    clear
  fi

  header_text="$(printf "Easy Frappe Docker\nManage Docker setups quickly and easily")"

  gum style \
    --border rounded \
    --border-foreground 63 \
    --padding "1 2" \
    --margin "1 2" \
    --foreground 252 \
    "${header_text}"
}

show_main_menu() {
  gum choose \
    --height 7 \
    --header "Choose an action" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Environment check" \
    "Exit"
}

show_environment_status() {
  local docker_status="not installed"
  local docker_daemon_status="not running"
  local status_text=""

  if command_exists docker; then
    docker_status="installed"

    if docker_daemon_running; then
      docker_daemon_status="running"
    fi
  fi

  render_main_screen 1 >&2

  status_text="$(printf "Environment status\n\n- docker: %s\n- docker daemon: %s" "${docker_status}" "${docker_daemon_status}")"

  gum style \
    --border rounded \
    --border-foreground 63 \
    --padding "1 2" \
    --margin "0 2" \
    --foreground 252 \
    "${status_text}" >&2

  gum choose \
    --height 6 \
    --header "Environment actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Back to main menu" \
    "Exit and close easy-docker"
}

show_warning_message() {
  local message="${1}"
  gum style --foreground 214 "${message}"
}
