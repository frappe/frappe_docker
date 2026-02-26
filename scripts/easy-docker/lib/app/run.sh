#!/usr/bin/env bash

get_easy_docker_repo_root() {
  local app_lib_dir=""
  app_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  (cd "${app_lib_dir}/../../../.." && pwd)
}

get_easy_docker_stacks_dir() {
  printf '%s/.easy-docker/stacks\n' "$(get_easy_docker_repo_root)"
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

create_stack_env_file() {
  local result_var="${1}"
  local stack_name="${2}"
  local stacks_dir=""
  local env_path=""

  stacks_dir="$(get_easy_docker_stacks_dir)"
  env_path="${stacks_dir}/${stack_name}.env"

  if ! mkdir -p "${stacks_dir}"; then
    return 1
  fi

  if [ -e "${env_path}" ]; then
    return 2
  fi

  : >"${env_path}"

  printf -v "${result_var}" "%s" "${env_path}"
  return 0
}

prompt_stack_name_with_cancel() {
  local result_var="${1}"
  local input_value=""
  local input_status=0

  input_value="$(prompt_new_stack_name)"
  input_status=$?
  if [ "${input_status}" -ne 0 ]; then
    return 3
  fi

  input_value="$(printf '%s' "${input_value}" | tr -d '\r\n')"

  case "${input_value}" in
  /cancel | /CANCEL | /Cancel)
    return 3
    ;;
  esac

  printf -v "${result_var}" "%s" "${input_value}"
  return 0
}

run_easy_docker_app() {
  local action=""
  local local_env_action=""
  local local_production_action=""
  local local_production_sub_action=""
  local stack_name=""
  local stack_env_path=""
  local create_stack_status=0
  local stack_input_status=0

  enter_alt_screen
  render_main_screen 1

  while true; do
    local_env_action=""
    local_production_action=""
    local_production_sub_action=""
    action="$(show_main_menu || true)"

    if [ -z "${action}" ]; then
      return 0
    fi

    case "${action}" in
    "Production setup")
      while true; do
        local_production_action="$(show_production_setup_menu || true)"
        case "${local_production_action}" in
        "Create new stack")
          while true; do
            stack_name=""
            if ! prompt_stack_name_with_cancel stack_name; then
              stack_input_status=$?
              if [ "${stack_input_status}" -eq 3 ]; then
                break
              fi

              show_warning_message "Input canceled."
              sleep 1
              break
            fi

            if [ -z "${stack_name}" ]; then
              break
            fi

            if ! is_valid_stack_name "${stack_name}"; then
              show_warning_message "Invalid stack name. Use letters, numbers, dot, underscore, or hyphen."
              sleep 2
              continue
            fi

            stack_env_path=""
            if create_stack_env_file stack_env_path "${stack_name}"; then
              local_production_sub_action="$(show_create_stack_created "${stack_name}" "${stack_env_path}" || true)"
            else
              create_stack_status=$?
              if [ "${create_stack_status}" -eq 2 ]; then
                show_warning_message "Stack already exists: ${stack_name}"
                sleep 2
                continue
              else
                show_warning_message "Could not create stack env file for: ${stack_name}"
                sleep 2
                break
              fi
            fi

            case "${local_production_sub_action}" in
            "Continue stack wizard")
              show_warning_message "Next wizard step is coming soon."
              sleep 2
              ;;
            "Back to production setup" | "") ;;
            *)
              show_warning_message "Unknown create-stack action: ${local_production_sub_action}"
              sleep 1
              ;;
            esac

            break
          done
          ;;
        "Manage existing stacks")
          local_production_sub_action="$(show_manage_stacks_placeholder || true)"
          case "${local_production_sub_action}" in
          "Back to production setup") ;;
          "Back to main menu" | "")
            render_main_screen 1
            break
            ;;
          "Exit and close easy-docker")
            return 0
            ;;
          *)
            show_warning_message "Unknown manage-stacks action: ${local_production_sub_action}"
            sleep 1
            ;;
          esac
          ;;
        "Back to main menu" | "")
          render_main_screen 1
          break
          ;;
        "Exit and close easy-docker")
          return 0
          ;;
        *)
          show_warning_message "Unknown production action: ${local_production_action}"
          sleep 1
          ;;
        esac
      done
      ;;
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
