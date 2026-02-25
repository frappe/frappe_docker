#!/usr/bin/env bash

run_easy_docker_app() {
  local action=""
  local local_env_action=""

  enter_alt_screen
  render_main_screen 1

  while true; do
    local_env_action=""
    action="$(show_main_menu || true)"

    if [ -z "${action}" ]; then
      return 0
    fi

    case "${action}" in
    "Environment check")
      local_env_action="$(show_environment_status || true)"
      case "${local_env_action}" in
      "Back to main menu" | "")
        render_main_screen 1
        ;;
      "Exit and close easy-docker")
        return 0
        ;;
      *)
        show_warning_message "Unknown environment action: ${local_env_action}"
        sleep 1
        ;;
      esac
      ;;
    "Exit")
      return 0
      ;;
    *)
      show_warning_message "Unknown action: ${action}"
      sleep 1
      ;;
    esac
  done
}
