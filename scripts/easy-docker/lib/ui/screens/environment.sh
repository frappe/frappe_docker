#!/usr/bin/env bash

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

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 6 \
    --header "Environment actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Back to main menu" \
    "Exit and close easy-docker"
}
