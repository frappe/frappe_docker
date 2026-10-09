#!/usr/bin/env bash

handle_create_new_stack_flow() {
  local setup_type="${1:-production}"
  local stack_name=""
  local frappe_branch=""
  local stack_dir=""
  local create_stack_status=0
  local stack_input_status=0
  local branch_select_status=0
  local topology_status=0

  case "${setup_type}" in
  production | development) ;;
  *)
    show_warning_and_wait "Unknown setup type: ${setup_type}" 2
    return "${FLOW_CONTINUE}"
    ;;
  esac

  while true; do
    stack_name=""
    if prompt_stack_name_with_cancel stack_name; then
      :
    else
      stack_input_status=$?
      if [ "${stack_input_status}" -eq "${FLOW_ABORT_INPUT}" ]; then
        return "${FLOW_CONTINUE}"
      fi

      show_warning_and_wait "Input canceled."
      return "${FLOW_CONTINUE}"
    fi

    if [ -z "${stack_name}" ]; then
      return "${FLOW_CONTINUE}"
    fi

    if ! is_valid_stack_name "${stack_name}"; then
      show_warning_and_wait "Invalid stack name. Use letters, numbers, dot, underscore, or hyphen." 2
      continue
    fi

    frappe_branch=""
    if prompt_frappe_branch_with_cancel frappe_branch "${stack_name}"; then
      :
    else
      branch_select_status=$?
      if [ "${branch_select_status}" -eq "${FLOW_ABORT_INPUT}" ]; then
        continue
      fi

      show_warning_and_wait "Could not select Frappe branch profile." 2
      return "${FLOW_CONTINUE}"
    fi

    stack_dir=""
    if create_stack_directory_with_metadata stack_dir "${stack_name}" "${setup_type}" "${frappe_branch}"; then
      handle_stack_topology_flow "${stack_dir}"
      topology_status=$?
      case "${topology_status}" in
      "${FLOW_BACK_TO_MAIN}")
        return "${FLOW_BACK_TO_MAIN}"
        ;;
      "${FLOW_EXIT_APP}")
        return "${FLOW_EXIT_APP}"
        ;;
      *)
        return "${FLOW_CONTINUE}"
        ;;
      esac
    else
      create_stack_status=$?
      if [ "${create_stack_status}" -eq 2 ]; then
        show_warning_and_wait "Stack already exists: ${stack_name}" 2
        continue
      fi

      show_warning_and_wait "Could not create stack directory for: ${stack_name}" 2
      return "${FLOW_CONTINUE}"
    fi
  done
}

handle_manage_existing_stacks_flow() {
  local setup_type="${1:-production}"
  local manage_action=""
  local selected_stack_status=0
  local stack_names_raw=""
  local -a stack_names=()

  while true; do
    stack_names_raw="$(list_existing_stack_names "${setup_type}")"
    if [ -z "${stack_names_raw}" ]; then
      manage_action="$(show_manage_stacks_placeholder "${setup_type}" || true)"
    else
      mapfile -t stack_names <<<"${stack_names_raw}"
      manage_action="$(show_manage_stacks_menu "${setup_type}" "${stack_names[@]}" || true)"
    fi

    case "${manage_action}" in
    "Back" | "")
      return "${FLOW_CONTINUE}"
      ;;
    "Exit and close easy-docker")
      return "${FLOW_EXIT_APP}"
      ;;
    *)
      if [ -n "${stack_names_raw}" ] && stack_name_in_array "${manage_action}" "${stack_names[@]}"; then
        if handle_manage_selected_stack_flow "${manage_action}"; then
          selected_stack_status="${FLOW_CONTINUE}"
        else
          selected_stack_status=$?
        fi

        case "${selected_stack_status}" in
        "${FLOW_BACK_TO_MAIN}")
          return "${FLOW_BACK_TO_MAIN}"
          ;;
        "${FLOW_EXIT_APP}")
          return "${FLOW_EXIT_APP}"
          ;;
        *) ;;
        esac
      else
        show_warning_and_wait "Unknown manage-stacks action: ${manage_action}"
      fi
      ;;
    esac
  done
}

handle_setup_flow() {
  local setup_type="${1}"
  local setup_action=""

  case "${setup_type}" in
  production | development) ;;
  *)
    show_warning_and_wait "Unknown setup type: ${setup_type}" 2
    return "${FLOW_CONTINUE}"
    ;;
  esac

  while true; do
    case "${setup_type}" in
    production)
      setup_action="$(show_production_setup_menu || true)"
      ;;
    development)
      setup_action="$(show_development_setup_menu || true)"
      ;;
    esac

    case "${setup_action}" in
    "Create new stack")
      if handle_create_new_stack_flow "${setup_type}"; then
        :
      else
        case "$?" in
        "${FLOW_BACK_TO_MAIN}")
          return "${FLOW_BACK_TO_MAIN}"
          ;;
        "${FLOW_EXIT_APP}")
          return "${FLOW_EXIT_APP}"
          ;;
        *) ;;
        esac
      fi
      ;;
    "Manage existing stacks")
      if handle_manage_existing_stacks_flow "${setup_type}"; then
        :
      else
        case "$?" in
        "${FLOW_BACK_TO_MAIN}")
          return "${FLOW_BACK_TO_MAIN}"
          ;;
        "${FLOW_EXIT_APP}")
          return "${FLOW_EXIT_APP}"
          ;;
        *) ;;
        esac
      fi
      ;;
    "Back" | "")
      return "${FLOW_BACK_TO_MAIN}"
      ;;
    "Exit and close easy-docker")
      return "${FLOW_EXIT_APP}"
      ;;
    *)
      show_warning_and_wait "Unknown ${setup_type} action: ${setup_action}"
      ;;
    esac
  done
}

handle_production_setup_flow() {
  handle_setup_flow "production"
}

handle_development_setup_flow() {
  handle_setup_flow "development"
}

handle_environment_check_flow() {
  local environment_action=""

  environment_action="$(show_environment_status || true)"
  case "${environment_action}" in
  "Back to main menu" | "")
    return "${FLOW_BACK_TO_MAIN}"
    ;;
  "Exit and close easy-docker")
    return "${FLOW_EXIT_APP}"
    ;;
  *)
    show_warning_and_wait "Unknown environment action: ${environment_action}"
    return "${FLOW_CONTINUE}"
    ;;
  esac
}

run_easy_docker_app() {
  local action=""
  local handler_status=0

  enter_alt_screen
  render_main_screen 1

  while true; do
    action="$(show_main_menu || true)"

    if [ -z "${action}" ]; then
      return 0
    fi

    case "${action}" in
    "Production Stack")
      if handle_production_setup_flow; then
        handler_status="${FLOW_CONTINUE}"
      else
        handler_status=$?
      fi
      case "${handler_status}" in
      "${FLOW_BACK_TO_MAIN}")
        render_main_screen 1
        ;;
      "${FLOW_EXIT_APP}")
        return 0
        ;;
      *) ;;
      esac
      ;;
    "Development Stack")
      if handle_development_setup_flow; then
        handler_status="${FLOW_CONTINUE}"
      else
        handler_status=$?
      fi
      case "${handler_status}" in
      "${FLOW_BACK_TO_MAIN}")
        render_main_screen 1
        ;;
      "${FLOW_EXIT_APP}")
        return 0
        ;;
      *) ;;
      esac
      ;;
    "Tools")
      if handle_tools_flow; then
        handler_status="${FLOW_CONTINUE}"
      else
        handler_status=$?
      fi
      case "${handler_status}" in
      "${FLOW_BACK_TO_MAIN}")
        render_main_screen 1
        ;;
      "${FLOW_EXIT_APP}")
        return 0
        ;;
      *) ;;
      esac
      ;;
    "Environment check")
      if handle_environment_check_flow; then
        handler_status="${FLOW_CONTINUE}"
      else
        handler_status=$?
      fi
      case "${handler_status}" in
      "${FLOW_BACK_TO_MAIN}")
        render_main_screen 1
        ;;
      "${FLOW_EXIT_APP}")
        return 0
        ;;
      *) ;;
      esac
      ;;
    "Exit")
      return 0
      ;;
    *)
      show_warning_and_wait "Unknown action: ${action}"
      ;;
    esac
  done
}
