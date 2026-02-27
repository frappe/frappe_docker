#!/usr/bin/env bash

handle_single_host_stack_flow() {
  local stack_dir="${1}"
  local proxy_mode=""
  local database_choice=""
  local redis_choice=""
  local stack_env_path=""
  local stack_apps_path=""
  local generated_compose_path=""
  local save_selection_status=0
  local render_compose_status=0

  proxy_mode="$(show_single_host_proxy_menu "${stack_dir}" || true)"
  case "${proxy_mode}" in
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    if ! get_single_host_proxy_mode_id "${proxy_mode}" >/dev/null; then
      show_warning_and_wait "Unknown proxy mode: ${proxy_mode}"
      return "${FLOW_CONTINUE}"
    fi
    ;;
  esac

  database_choice="$(show_single_host_database_menu "${stack_dir}" || true)"
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

  redis_choice="$(show_single_host_redis_menu "${stack_dir}" || true)"
  case "${redis_choice}" in
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    if ! get_single_host_redis_id "${redis_choice}" >/dev/null; then
      show_warning_and_wait "Unknown Redis choice: ${redis_choice}"
      return "${FLOW_CONTINUE}"
    fi
    ;;
  esac

  if ! save_single_host_selection "${stack_dir}" "${proxy_mode}" "${database_choice}" "${redis_choice}"; then
    save_selection_status=$?
    if [ "${save_selection_status}" -eq 2 ]; then
      return "${FLOW_CONTINUE}"
    fi

    show_warning_and_wait "Could not save single-host selection for stack: ${stack_dir}" 2
    return "${FLOW_CONTINUE}"
  fi

  if ! render_stack_compose_from_metadata "${stack_dir}"; then
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
  show_warning_and_wait "Single-host selection saved in ${stack_dir}/metadata.json, ${stack_env_path}, and ${stack_apps_path}. Rendered compose: ${generated_compose_path}." 3
  return "${FLOW_CONTINUE}"
}

handle_topology_examples_flow() {
  local topology_name="${1}"
  local detail_action=""

  case "${topology_name}" in
  "Split services")
    detail_action="$(show_split_services_examples || true)"
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
