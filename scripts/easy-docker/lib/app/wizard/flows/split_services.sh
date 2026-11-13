#!/usr/bin/env bash

handle_split_services_stack_flow() {
  local stack_dir="${1}"
  local data_mode=""
  local database_choice=""
  local redis_choice=""
  local proxy_mode=""
  local summary_action=""
  local stack_env_path=""
  local stack_apps_path=""
  local generated_compose_path=""
  local save_selection_status=0
  local render_compose_status=0

  data_mode="$(show_split_services_data_mode_menu "${stack_dir}" || true)"
  case "${data_mode}" in
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    if ! get_split_services_data_mode_id "${data_mode}" >/dev/null; then
      show_warning_and_wait "Unknown data services mode: ${data_mode}"
      return "${FLOW_CONTINUE}"
    fi
    ;;
  esac

  database_choice="$(show_split_services_database_menu "${stack_dir}" || true)"
  case "${database_choice}" in
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    if ! get_single_host_database_id "${database_choice}" >/dev/null; then
      show_warning_and_wait "Unknown database choice: ${database_choice}"
      return "${FLOW_CONTINUE}"
    fi
    ;;
  esac

  redis_choice="$(show_split_services_redis_mode_menu "${stack_dir}" || true)"
  case "${redis_choice}" in
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    if ! get_split_services_redis_id "${redis_choice}" >/dev/null; then
      show_warning_and_wait "Unknown Redis choice: ${redis_choice}"
      return "${FLOW_CONTINUE}"
    fi
    ;;
  esac

  proxy_mode="$(show_split_services_proxy_mode_menu "${stack_dir}" || true)"
  case "${proxy_mode}" in
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    if ! get_single_host_proxy_mode_id "${proxy_mode}" >/dev/null; then
      show_warning_and_wait "Unknown reverse proxy mode: ${proxy_mode}"
      return "${FLOW_CONTINUE}"
    fi
    ;;
  esac

  summary_action="$(show_split_services_summary_menu "${stack_dir}" "${data_mode}" "${database_choice}" "${redis_choice}" "${proxy_mode}" || true)"
  case "${summary_action}" in
  "Yes, write stack files") ;;
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  "Abort wizard to main menu")
    handle_abort_wizard_flow "${stack_dir}"
    return $?
    ;;
  *)
    show_warning_and_wait "Unknown split-services summary action: ${summary_action}"
    return "${FLOW_CONTINUE}"
    ;;
  esac

  if save_split_services_selection "${stack_dir}" "${proxy_mode}" "${data_mode}" "${database_choice}" "${redis_choice}"; then
    :
  else
    save_selection_status=$?
    if [ "${save_selection_status}" -eq 2 ] || [ "${save_selection_status}" -eq 130 ]; then
      return "${FLOW_CONTINUE}"
    fi
    case "${save_selection_status}" in
    31)
      show_warning_and_wait "Could not write the split-services env file for stack: ${stack_dir}" 3
      ;;
    32)
      show_warning_and_wait "Could not write the split-services wizard metadata in ${stack_dir}/metadata.json." 3
      ;;
    33)
      show_warning_and_wait "Split-services app selection is empty. Select at least one app before writing stack files." 3
      ;;
    34)
      show_warning_and_wait "Could not write the selected app metadata in ${stack_dir}/metadata.json." 3
      ;;
    35)
      show_warning_and_wait "Could not generate ${stack_dir}/apps.json from the selected split-services apps." 3
      ;;
    *)
      show_warning_and_wait "Could not save split-services selection for stack: ${stack_dir} (${save_selection_status})." 3
      ;;
    esac
    return "${FLOW_CONTINUE}"
  fi

  if render_stack_compose_from_metadata "${stack_dir}"; then
    :
  else
    render_compose_status=$?
    stack_env_path="$(get_stack_env_path "${stack_dir}")"
    stack_apps_path="${stack_dir}/apps.json"
    generated_compose_path="$(get_stack_generated_compose_path "${stack_dir}")"
    show_warning_and_wait "Selection saved in ${stack_dir}/metadata.json, ${stack_env_path}, and ${stack_apps_path}, but compose rendering failed (${render_compose_status}) for ${generated_compose_path}." 3
    return "${FLOW_CONTINUE}"
  fi

  stack_env_path="$(get_stack_env_path "${stack_dir}")"
  stack_apps_path="${stack_dir}/apps.json"
  generated_compose_path="$(get_stack_generated_compose_path "${stack_dir}")"
  show_warning_and_wait "Split-services selection saved in ${stack_dir}/metadata.json, ${stack_env_path}, and ${stack_apps_path}. Rendered compose: ${generated_compose_path}." 3
  return "${FLOW_OPEN_MANAGE_STACK}"
}
