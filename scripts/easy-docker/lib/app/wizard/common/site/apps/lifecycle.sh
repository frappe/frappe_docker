#!/usr/bin/env bash

stack_site_app_lines_contain() {
  local app_lines="${1:-}"
  local app_name="${2:-}"

  if [ -z "${app_name}" ]; then
    return 1
  fi

  printf '%s\n' "${app_lines}" | grep -F -x -- "${app_name}" >/dev/null 2>&1
}

remove_stack_site_app_line() {
  local result_var="${1}"
  local existing_lines="${2:-}"
  local app_name="${3:-}"
  local existing_app=""
  local remaining_lines=""

  while IFS= read -r existing_app; do
    if [ -z "${existing_app}" ] || [ "${existing_app}" = "${app_name}" ]; then
      continue
    fi

    if [ -z "${remaining_lines}" ]; then
      remaining_lines="${existing_app}"
    else
      remaining_lines="${remaining_lines}"$'\n'"${existing_app}"
    fi
  done <<EOF
${existing_lines}
EOF

  printf -v "${result_var}" "%s" "${remaining_lines}"
}

get_stack_site_managed_runtime_app_lines() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local runtime_app_lines=""
  local app_name=""
  local managed_app_lines=""
  local runtime_status=0

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  if runtime_app_lines="$(get_stack_site_runtime_app_names_lines "${stack_dir}" "${site_name}")"; then
    :
    runtime_status=0
  else
    runtime_status=$?
  fi
  if [ "${runtime_status}" -eq 54 ] || [ "${runtime_status}" -eq 52 ]; then
    return "${runtime_status}"
  fi

  if [ -z "${runtime_app_lines}" ]; then
    return 1
  fi

  while IFS= read -r app_name; do
    if [ -z "${app_name}" ] || [ "${app_name}" = "frappe" ]; then
      continue
    fi

    append_stack_installable_app_line managed_app_lines "${managed_app_lines}" "${app_name}"
  done <<EOF
${runtime_app_lines}
EOF

  printf -v "${result_var}" "%s" "${managed_app_lines}"
  return 0
}

persist_stack_site_app_operation_metadata() {
  local stack_dir="${1}"
  local site_name="${2}"
  local apps_installed_lines="${3:-}"
  local last_action="${4:-manage-site-apps}"
  local last_error="${5:-}"
  local error_log_path="${6:-}"
  local created_at=""
  local updated_at=""

  created_at="$(get_stack_site_created_at "${stack_dir}" || true)"
  updated_at="$(get_current_utc_timestamp)"

  persist_stack_site_metadata \
    "${stack_dir}" \
    "single-site" \
    "${site_name}" \
    "${apps_installed_lines}" \
    "${last_action}" \
    "${last_error}" \
    "${error_log_path}" \
    "${created_at}" \
    "${updated_at}"
}

get_configured_stack_site_installable_app_lines() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_name=""
  local backend_status=0
  local selected_app_lines=""
  local available_app_lines=""
  local installed_app_lines=""
  local candidate_app=""
  local installable_app_lines=""
  local inspect_status=0

  if ! stack_supports_single_site_management "${stack_dir}"; then
    return 82
  fi

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 83
  fi

  if stack_backend_service_is_running "${stack_dir}"; then
    :
  else
    backend_status=$?
    case "${backend_status}" in
    54)
      return 84
      ;;
    52)
      return 82
      ;;
    *)
      return 81
      ;;
    esac
  fi

  if ! get_stack_selected_installable_apps selected_app_lines "${stack_dir}"; then
    return 84
  fi

  if available_app_lines="$(get_stack_runtime_available_app_lines "${stack_dir}")"; then
    :
  else
    inspect_status=$?
    case "${inspect_status}" in
    54)
      return 84
      ;;
    52)
      return 82
      ;;
    *)
      return 87
      ;;
    esac
  fi

  if get_stack_site_managed_runtime_app_lines installed_app_lines "${stack_dir}" "${site_name}"; then
    :
  else
    inspect_status=$?
    case "${inspect_status}" in
    54)
      return 84
      ;;
    52)
      return 82
      ;;
    61)
      return 83
      ;;
    *)
      return 87
      ;;
    esac
  fi

  while IFS= read -r candidate_app; do
    if [ -z "${candidate_app}" ]; then
      continue
    fi

    if ! stack_site_app_lines_contain "${available_app_lines}" "${candidate_app}"; then
      continue
    fi

    if stack_site_app_lines_contain "${installed_app_lines}" "${candidate_app}"; then
      continue
    fi

    append_stack_installable_app_line installable_app_lines "${installable_app_lines}" "${candidate_app}"
  done <<EOF
${selected_app_lines}
EOF

  printf -v "${result_var}" "%s" "${installable_app_lines}"
  return 0
}

get_configured_stack_site_uninstallable_app_lines() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_name=""
  local backend_status=0
  local installed_app_lines=""

  if ! stack_supports_single_site_management "${stack_dir}"; then
    return 92
  fi

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 93
  fi

  if stack_backend_service_is_running "${stack_dir}"; then
    :
  else
    backend_status=$?
    case "${backend_status}" in
    54)
      return 94
      ;;
    52)
      return 92
      ;;
    *)
      return 91
      ;;
    esac
  fi

  if get_stack_site_managed_runtime_app_lines installed_app_lines "${stack_dir}" "${site_name}"; then
    :
  else
    backend_status=$?
    case "${backend_status}" in
    54)
      return 94
      ;;
    52)
      return 92
      ;;
    61)
      return 93
      ;;
    *)
      return 97
      ;;
    esac
  fi

  printf -v "${result_var}" "%s" "${installed_app_lines}"
  return 0
}

install_app_on_configured_stack_site() {
  local stack_dir="${1}"
  local app_name="${2:-}"
  local site_name=""
  local installable_app_lines=""
  local current_installed_app_lines=""
  local updated_installed_app_lines=""
  local install_command=""
  local install_output=""
  local command_status=0
  local installable_status=0

  reset_easy_docker_site_error_state

  if [ -z "${app_name}" ]; then
    return 86
  fi

  if get_configured_stack_site_installable_app_lines installable_app_lines "${stack_dir}"; then
    :
  else
    installable_status=$?
    return "${installable_status}"
  fi

  if [ -z "${installable_app_lines}" ]; then
    return 85
  fi

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if ! get_stack_site_managed_runtime_app_lines current_installed_app_lines "${stack_dir}" "${site_name}"; then
    current_installed_app_lines="$(get_stack_site_apps_installed_lines "${stack_dir}" || true)"
  fi

  if ! stack_site_app_lines_contain "${installable_app_lines}" "${app_name}"; then
    return 86
  fi

  install_command="$(
    printf "bench --site %s install-app %s" \
      "$(shell_quote_site_command_arg "${site_name}")" \
      "$(shell_quote_site_command_arg "${app_name}")"
  )"

  if run_stack_backend_bash_command_capture install_output "${stack_dir}" "${install_command}"; then
    :
  else
    command_status=$?
    EASY_DOCKER_SITE_ERROR_DETAIL="$(printf "bench install-app failed for '%s'." "${app_name}")"
    capture_stack_site_error_log "${stack_dir}" "site-install-app-error" "${install_output}" >/dev/null 2>&1 || true
    if ! persist_stack_site_app_operation_metadata \
      "${stack_dir}" \
      "${site_name}" \
      "${current_installed_app_lines}" \
      "install-app" \
      "${EASY_DOCKER_SITE_ERROR_DETAIL}" \
      "${EASY_DOCKER_SITE_ERROR_LOG_PATH}"; then
      return 89
    fi
    case "${command_status}" in
    54)
      return 84
      ;;
    52)
      return 82
      ;;
    *)
      return 88
      ;;
    esac
  fi

  if ! get_stack_site_managed_runtime_app_lines updated_installed_app_lines "${stack_dir}" "${site_name}"; then
    updated_installed_app_lines="${current_installed_app_lines}"
    append_stack_installable_app_line updated_installed_app_lines "${updated_installed_app_lines}" "${app_name}"
  fi

  if ! persist_stack_site_app_operation_metadata \
    "${stack_dir}" \
    "${site_name}" \
    "${updated_installed_app_lines}" \
    "install-app" \
    "" \
    ""; then
    return 89
  fi

  return 0
}

uninstall_app_from_configured_stack_site() {
  local stack_dir="${1}"
  local app_name="${2:-}"
  local site_name=""
  local uninstallable_app_lines=""
  local current_installed_app_lines=""
  local updated_installed_app_lines=""
  local uninstall_command=""
  local uninstall_output=""
  local command_status=0
  local uninstallable_status=0

  reset_easy_docker_site_error_state

  if [ -z "${app_name}" ] || [ "${app_name}" = "frappe" ]; then
    return 96
  fi

  if get_configured_stack_site_uninstallable_app_lines uninstallable_app_lines "${stack_dir}"; then
    :
  else
    uninstallable_status=$?
    return "${uninstallable_status}"
  fi

  if [ -z "${uninstallable_app_lines}" ]; then
    return 95
  fi

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  current_installed_app_lines="${uninstallable_app_lines}"

  if ! stack_site_app_lines_contain "${uninstallable_app_lines}" "${app_name}"; then
    return 96
  fi

  uninstall_command="$(
    printf "bench --site %s uninstall-app %s --yes" \
      "$(shell_quote_site_command_arg "${site_name}")" \
      "$(shell_quote_site_command_arg "${app_name}")"
  )"

  if run_stack_backend_bash_command_capture uninstall_output "${stack_dir}" "${uninstall_command}"; then
    :
  else
    command_status=$?
    EASY_DOCKER_SITE_ERROR_DETAIL="$(printf "bench uninstall-app failed for '%s'." "${app_name}")"
    capture_stack_site_error_log "${stack_dir}" "site-uninstall-app-error" "${uninstall_output}" >/dev/null 2>&1 || true
    if ! persist_stack_site_app_operation_metadata \
      "${stack_dir}" \
      "${site_name}" \
      "${current_installed_app_lines}" \
      "uninstall-app" \
      "${EASY_DOCKER_SITE_ERROR_DETAIL}" \
      "${EASY_DOCKER_SITE_ERROR_LOG_PATH}"; then
      return 99
    fi
    case "${command_status}" in
    54)
      return 94
      ;;
    52)
      return 92
      ;;
    *)
      return 98
      ;;
    esac
  fi

  if ! get_stack_site_managed_runtime_app_lines updated_installed_app_lines "${stack_dir}" "${site_name}"; then
    remove_stack_site_app_line updated_installed_app_lines "${current_installed_app_lines}" "${app_name}"
  fi

  if ! persist_stack_site_app_operation_metadata \
    "${stack_dir}" \
    "${site_name}" \
    "${updated_installed_app_lines}" \
    "uninstall-app" \
    "" \
    ""; then
    return 99
  fi

  return 0
}
