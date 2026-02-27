#!/usr/bin/env bash

readonly FLOW_CONTINUE=0
readonly FLOW_BACK_TO_MAIN=10
readonly FLOW_EXIT_APP=11
readonly FLOW_ABORT_INPUT=12

get_easy_docker_repo_root() {
  local app_lib_dir=""
  app_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  (cd "${app_lib_dir}/../../../.." && pwd)
}

get_easy_docker_stacks_dir() {
  printf '%s/.easy-docker/stacks\n' "$(get_easy_docker_repo_root)"
}

get_current_utc_timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ"
}

is_valid_stack_name() {
  local stack_name="${1}"

  if [ -z "${stack_name}" ]; then
    return 1
  fi

  case "${stack_name}" in
  *[!A-Za-z0-9._-]*)
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

create_stack_directory_with_metadata() {
  local stack_dir_var="${1}"
  local stack_name="${2}"
  local stacks_dir=""
  local created_stack_dir=""
  local metadata_path=""
  local created_at=""

  stacks_dir="$(get_easy_docker_stacks_dir)"
  created_stack_dir="${stacks_dir}/${stack_name}"
  metadata_path="${created_stack_dir}/metadata.json"

  if ! mkdir -p "${stacks_dir}"; then
    return 1
  fi

  if [ -e "${created_stack_dir}" ]; then
    return 2
  fi

  if ! mkdir -p "${created_stack_dir}"; then
    return 1
  fi

  created_at="$(get_current_utc_timestamp)"
  if ! cat >"${metadata_path}" <<EOF; then
{
  "schema_version": 1,
  "stack_name": "${stack_name}",
  "created_at": "${created_at}"
}
EOF
    rollback_stack_directory "${created_stack_dir}" >/dev/null 2>&1 || true
    return 1
  fi

  printf -v "${stack_dir_var}" "%s" "${created_stack_dir}"
  return 0
}

rollback_stack_directory() {
  local stack_dir="${1}"
  local stacks_dir=""

  if [ -z "${stack_dir}" ]; then
    return 1
  fi

  stacks_dir="$(get_easy_docker_stacks_dir)"
  case "${stack_dir}" in
  "${stacks_dir}"/*) ;;
  *)
    return 2
    ;;
  esac

  if [ ! -d "${stack_dir}" ]; then
    return 0
  fi

  rm -rf -- "${stack_dir}"
}

prompt_stack_name_with_cancel() {
  local result_var="${1}"
  local input_value=""
  local input_status=0

  input_value="$(prompt_new_stack_name)"
  input_status=$?
  if [ "${input_status}" -ne 0 ]; then
    return "${FLOW_ABORT_INPUT}"
  fi

  input_value="$(printf '%s' "${input_value}" | tr -d '\r\n')"

  case "${input_value}" in
  /cancel | /CANCEL | /Cancel)
    return "${FLOW_ABORT_INPUT}"
    ;;
  esac

  printf -v "${result_var}" "%s" "${input_value}"
  return "${FLOW_CONTINUE}"
}

show_warning_and_wait() {
  local message="${1}"
  local seconds="${2:-1}"

  show_warning_message "${message}"
  sleep "${seconds}"
}

handle_topology_examples_flow() {
  local topology_name="${1}"
  local detail_action=""

  case "${topology_name}" in
  "Single-host")
    detail_action="$(show_single_host_examples || true)"
    ;;
  "Split services")
    detail_action="$(show_split_services_examples || true)"
    ;;
  "Advanced")
    detail_action="$(show_advanced_examples || true)"
    ;;
  *)
    show_warning_and_wait "Unknown topology: ${topology_name}"
    return "${FLOW_CONTINUE}"
    ;;
  esac

  case "${detail_action}" in
  "Use this topology")
    show_warning_and_wait "Topology '${topology_name}' selected. Next wizard step is coming soon." 2
    return "${FLOW_CONTINUE}"
    ;;
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    show_warning_and_wait "Unknown topology action: ${detail_action}"
    return "${FLOW_CONTINUE}"
    ;;
  esac
}

handle_abort_wizard_flow() {
  local stack_dir="${1}"
  local abort_action=""
  local rollback_status=0

  abort_action="$(show_abort_wizard_prompt "${stack_dir}" || true)"
  case "${abort_action}" in
  "Rollback files and return to main menu")
    if rollback_stack_directory "${stack_dir}"; then
      return "${FLOW_BACK_TO_MAIN}"
    fi

    rollback_status=$?
    if [ "${rollback_status}" -eq 2 ]; then
      show_warning_and_wait "Refused rollback for unsafe path: ${stack_dir}" 2
    else
      show_warning_and_wait "Could not rollback stack files: ${stack_dir}" 2
    fi
    return "${FLOW_CONTINUE}"
    ;;
  "Keep files and return to main menu")
    return "${FLOW_BACK_TO_MAIN}"
    ;;
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    show_warning_and_wait "Unknown abort action: ${abort_action}"
    return "${FLOW_CONTINUE}"
    ;;
  esac
}

handle_stack_topology_flow() {
  local stack_dir="${1}"
  local topology_action=""
  local abort_status=0

  while true; do
    topology_action="$(show_stack_topology_menu "${stack_dir}" || true)"
    case "${topology_action}" in
    "Single-host" | "Split services" | "Advanced")
      handle_topology_examples_flow "${topology_action}"
      ;;
    "Abort wizard to main menu")
      handle_abort_wizard_flow "${stack_dir}"
      abort_status=$?
      case "${abort_status}" in
      "${FLOW_BACK_TO_MAIN}")
        return "${FLOW_BACK_TO_MAIN}"
        ;;
      *) ;;
      esac
      ;;
    "")
      return "${FLOW_CONTINUE}"
      ;;
    *)
      show_warning_and_wait "Unknown topology selection: ${topology_action}"
      ;;
    esac
  done
}

handle_create_new_stack_flow() {
  local stack_name=""
  local stack_dir=""
  local create_stack_status=0
  local stack_input_status=0
  local topology_status=0

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

    stack_dir=""
    if create_stack_directory_with_metadata stack_dir "${stack_name}"; then
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
  local manage_action=""

  manage_action="$(show_manage_stacks_placeholder || true)"
  case "${manage_action}" in
  "Back to production setup")
    return "${FLOW_CONTINUE}"
    ;;
  "Back to main menu" | "")
    return "${FLOW_BACK_TO_MAIN}"
    ;;
  "Exit and close easy-docker")
    return "${FLOW_EXIT_APP}"
    ;;
  *)
    show_warning_and_wait "Unknown manage-stacks action: ${manage_action}"
    return "${FLOW_CONTINUE}"
    ;;
  esac
}

handle_production_setup_flow() {
  local production_action=""

  while true; do
    production_action="$(show_production_setup_menu || true)"

    case "${production_action}" in
    "Create new stack")
      if handle_create_new_stack_flow; then
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
      if handle_manage_existing_stacks_flow; then
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
    "Back to main menu" | "")
      return "${FLOW_BACK_TO_MAIN}"
      ;;
    "Exit and close easy-docker")
      return "${FLOW_EXIT_APP}"
      ;;
    *)
      show_warning_and_wait "Unknown production action: ${production_action}"
      ;;
    esac
  done
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
    "Production setup")
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
