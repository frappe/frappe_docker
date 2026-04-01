#!/usr/bin/env bash

drop_stack_site_database() {
  local stack_dir="${1}"
  local db_name="${2}"
  local db_password=""
  local db_endpoint=""
  local db_host=""
  local db_port=""
  local drop_db_command=""

  db_password="$(get_stack_database_root_password "${stack_dir}")"
  db_endpoint="$(get_stack_common_db_endpoint "${stack_dir}" || true)"
  db_host="${db_endpoint%%|*}"
  db_port="${db_endpoint#*|}"

  if [ -z "${db_host}" ] || [ -z "${db_port}" ]; then
    return 1
  fi

  drop_db_command="$(
    printf "mysql --protocol=TCP -h %s -P %s -u root -p%s -e %s" \
      "$(shell_quote_site_command_arg "${db_host}")" \
      "$(shell_quote_site_command_arg "${db_port}")" \
      "$(printf '%s' "${db_password}" | sed "s/'/'\"'\"'/g")" \
      "$(shell_quote_site_command_arg "DROP DATABASE IF EXISTS \`${db_name}\`; DROP USER IF EXISTS '${db_name}'@'%'; DROP USER IF EXISTS '${db_name}'@'localhost'; FLUSH PRIVILEGES;")"
  )"

  if ! run_stack_backend_bash_command "${stack_dir}" "${drop_db_command}"; then
    return 1
  fi

  return 0
}

remove_stack_site_directory() {
  local stack_dir="${1}"
  local site_name="${2}"
  local remove_command=""

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  remove_command="$(
    printf "rm -rf -- sites/%s archived_sites/%s" \
      "$(shell_quote_site_command_arg "${site_name}")" \
      "$(shell_quote_site_command_arg "${site_name}")"
  )"

  if ! run_stack_backend_bash_command "${stack_dir}" "${remove_command}"; then
    return 1
  fi

  return 0
}

cleanup_partial_stack_site() {
  local stack_dir="${1}"
  local site_name="${2}"
  local artifact_status=0
  local db_name=""
  local has_site_config=1

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  if stack_site_has_partial_artifacts "${stack_dir}" "${site_name}"; then
    :
  else
    artifact_status=$?
    case "${artifact_status}" in
    61)
      return 61
      ;;
    54 | 52)
      return "${artifact_status}"
      ;;
    *)
      return 0
      ;;
    esac
  fi

  if stack_site_config_exists "${stack_dir}" "${site_name}"; then
    :
  else
    artifact_status=$?
    case "${artifact_status}" in
    61)
      return 61
      ;;
    54 | 52)
      return "${artifact_status}"
      ;;
    *)
      has_site_config=0
      ;;
    esac
  fi

  if [ "${has_site_config}" -eq 1 ]; then
    db_name="$(get_stack_site_database_name "${stack_dir}" "${site_name}" || true)"
    if [ -z "${db_name}" ]; then
      return 60
    fi
  fi

  if [ "${has_site_config}" -eq 1 ] && ! drop_stack_site_database "${stack_dir}" "${db_name}"; then
    return 60
  fi

  if ! remove_stack_site_directory "${stack_dir}" "${site_name}"; then
    return 60
  fi

  if stack_site_has_partial_artifacts "${stack_dir}" "${site_name}"; then
    return 60
  fi

  artifact_status=$?
  case "${artifact_status}" in
  54 | 52)
    return "${artifact_status}"
    ;;
  esac

  return 0
}

delete_configured_stack_site() {
  local stack_dir="${1}"
  local site_name=""
  local delete_status=0

  if ! stack_supports_single_site_management "${stack_dir}"; then
    return 52
  fi

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  if ! stack_backend_service_is_running "${stack_dir}"; then
    return 51
  fi

  if cleanup_partial_stack_site "${stack_dir}" "${site_name}"; then
    :
  else
    delete_status=$?
    case "${delete_status}" in
    54 | 52 | 61)
      return "${delete_status}"
      ;;
    *)
      return 60
      ;;
    esac
  fi

  if ! clear_stack_site_metadata "${stack_dir}"; then
    return 58
  fi

  return 0
}

create_first_stack_site() {
  local stack_dir="${1}"
  local site_name="${2}"
  local admin_password="${3}"
  local create_site_command=""
  local create_site_output=""

  create_site_command="$(
    printf "bench new-site %s --mariadb-user-host-login-scope='%%' --admin-password %s --db-root-username root --db-root-password %s" \
      "$(shell_quote_site_command_arg "${site_name}")" \
      "$(shell_quote_site_command_arg "${admin_password}")" \
      "$(shell_quote_site_command_arg "$(get_stack_database_root_password "${stack_dir}")")"
  )"

  if ! run_stack_backend_bash_command_capture create_site_output "${stack_dir}" "${create_site_command}"; then
    EASY_DOCKER_SITE_ERROR_DETAIL="bench new-site failed."
    capture_stack_site_error_log "${stack_dir}" "site-create-error" "${create_site_output}" >/dev/null 2>&1 || true
    return 55
  fi

  return 0
}

install_stack_apps_on_site() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local selected_app_lines=""
  local installed_app_lines=""
  local app_name=""
  local install_app_command=""
  local install_app_output=""
  local available_app_lines=""
  local -a selected_apps=()

  if ! get_stack_selected_installable_apps selected_app_lines "${stack_dir}"; then
    printf -v "${result_var}" "%s" ""
    return 0
  fi

  if [ -z "${selected_app_lines}" ]; then
    printf -v "${result_var}" "%s" ""
    return 0
  fi

  available_app_lines="$(get_stack_runtime_available_app_lines "${stack_dir}" || true)"
  if [ -z "${available_app_lines}" ]; then
    EASY_DOCKER_SITE_ERROR_DETAIL="Could not inspect available apps in the backend image."
    capture_stack_site_error_log "${stack_dir}" "site-install-apps-error" "easy-docker could not list /home/frappe/frappe-bench/apps before install-app." >/dev/null 2>&1 || true
    return 63
  fi

  mapfile -t selected_apps <<<"${selected_app_lines}"
  for app_name in "${selected_apps[@]}"; do
    if [ -z "${app_name}" ]; then
      continue
    fi

    if ! printf '%s\n' "${available_app_lines}" | grep -F -x -- "${app_name}" >/dev/null 2>&1; then
      EASY_DOCKER_SITE_ERROR_DETAIL="$(printf "Selected app '%s' is not available in the backend image." "${app_name}")"
      capture_stack_site_error_log "${stack_dir}" "site-install-apps-error" "$(printf "Selected app '%s' was requested in stack metadata but is missing from /home/frappe/frappe-bench/apps.\nAvailable apps:\n%s" "${app_name}" "${available_app_lines}")" >/dev/null 2>&1 || true
      if [ -n "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" ]; then
        printf 'Details written to %s\n' "${stack_dir}/${EASY_DOCKER_SITE_ERROR_LOG_PATH}" >&2
      fi
      printf -v "${result_var}" "%s" "${installed_app_lines}"
      return 63
    fi

    install_app_command="$(
      printf "bench --site %s install-app %s" \
        "$(shell_quote_site_command_arg "${site_name}")" \
        "$(shell_quote_site_command_arg "${app_name}")"
    )"

    if ! run_stack_backend_bash_command_capture install_app_output "${stack_dir}" "${install_app_command}"; then
      EASY_DOCKER_SITE_ERROR_DETAIL="$(printf "bench install-app failed for '%s'." "${app_name}")"
      capture_stack_site_error_log "${stack_dir}" "site-install-apps-error" "${install_app_output}" >/dev/null 2>&1 || true
      printf -v "${result_var}" "%s" "${installed_app_lines}"
      return 56
    fi

    if [ -z "${installed_app_lines}" ]; then
      installed_app_lines="${app_name}"
    else
      installed_app_lines="${installed_app_lines}"$'\n'"${app_name}"
    fi

    if ! persist_stack_site_metadata \
      "${stack_dir}" \
      "single-site" \
      "${site_name}" \
      "${installed_app_lines}" \
      "install-apps" \
      "" \
      "" \
      "$(get_stack_site_created_at "${stack_dir}" || true)" \
      "$(get_current_utc_timestamp)"; then
      return 58
    fi
  done

  printf -v "${result_var}" "%s" "${installed_app_lines}"
  return 0
}

run_stack_site_migrate() {
  local stack_dir="${1}"
  local site_name="${2}"
  local migrate_command=""
  local migrate_output=""

  migrate_command="$(
    printf "bench --site %s migrate" \
      "$(shell_quote_site_command_arg "${site_name}")"
  )"

  if ! run_stack_backend_bash_command_capture migrate_output "${stack_dir}" "${migrate_command}"; then
    EASY_DOCKER_SITE_ERROR_DETAIL="$(printf "bench migrate failed for '%s'." "${site_name}")"
    capture_stack_site_error_log "${stack_dir}" "site-migrate-error" "${migrate_output}" >/dev/null 2>&1 || true
    return 64
  fi

  return 0
}

bootstrap_first_stack_site() {
  local stack_dir="${1}"
  local site_name="${2}"
  local admin_password="${3}"
  local created_at=""
  local updated_at=""
  local installed_app_lines=""
  local site_create_status=0
  local app_install_status=0
  local site_migrate_status=0
  local cleanup_status=0

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  if ! stack_supports_single_site_management "${stack_dir}"; then
    return 52
  fi

  if ! stack_site_bootstrap_supports_database "${stack_dir}"; then
    return 57
  fi

  if stack_has_site_configured "${stack_dir}"; then
    return 53
  fi

  if ! stack_backend_service_is_running "${stack_dir}"; then
    return 51
  fi

  if ! repair_stack_site_runtime_state "${stack_dir}"; then
    return $?
  fi

  if ! stack_database_service_is_reachable "${stack_dir}"; then
    return 59
  fi

  created_at="$(get_current_utc_timestamp)"
  updated_at="${created_at}"
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "" "create-site" "" "" "${created_at}" "${updated_at}"; then
    return 58
  fi

  if cleanup_partial_stack_site "${stack_dir}" "${site_name}"; then
    :
  else
    cleanup_status=$?
    case "${cleanup_status}" in
    54 | 52)
      return "${cleanup_status}"
      ;;
    60)
      mark_stack_site_failed "${stack_dir}" "${site_name}" "" "cleanup-partial-site" "Partial site artifacts could not be removed automatically. Manual cleanup is required." "" "" >/dev/null 2>&1 || true
      return 60
      ;;
    *)
      mark_stack_site_failed "${stack_dir}" "${site_name}" "" "cleanup-partial-site" "Unexpected cleanup failure before create-site." "" "${created_at}" >/dev/null 2>&1 || true
      return 60
      ;;
    esac
  fi

  updated_at="${created_at}"
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "" "create-site" "" "" "${created_at}" "${updated_at}"; then
    return 58
  fi

  if create_first_stack_site "${stack_dir}" "${site_name}" "${admin_password}"; then
    :
  else
    site_create_status=$?
    if cleanup_partial_stack_site "${stack_dir}" "${site_name}"; then
      mark_stack_site_failed "${stack_dir}" "${site_name}" "" "create-site" "bench new-site failed. Partial site data was cleaned up automatically." "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" "${created_at}" >/dev/null 2>&1 || true
      return "${site_create_status}"
    fi

    cleanup_status=$?
    mark_stack_site_failed "${stack_dir}" "${site_name}" "" "create-site" "bench new-site failed and partial site data could not be cleaned up automatically. Manual cleanup is required." "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" "${created_at}" >/dev/null 2>&1 || true
    case "${cleanup_status}" in
    54 | 52)
      return "${cleanup_status}"
      ;;
    *)
      return 60
      ;;
    esac
  fi

  updated_at="$(get_current_utc_timestamp)"
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "" "create-site" "" "" "${created_at}" "${updated_at}"; then
    return 58
  fi

  if install_stack_apps_on_site installed_app_lines "${stack_dir}" "${site_name}"; then
    :
  else
    app_install_status=$?
    case "${app_install_status}" in
    56 | 63)
      if cleanup_partial_stack_site "${stack_dir}" "${site_name}"; then
        mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "install-apps" "${EASY_DOCKER_SITE_ERROR_DETAIL:-App installation failed. Partial site data was cleaned up automatically.}" "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" "${created_at}" >/dev/null 2>&1 || true
      else
        cleanup_status=$?
        mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "install-apps" "${EASY_DOCKER_SITE_ERROR_DETAIL:-App installation failed and partial site data could not be cleaned up automatically. Manual cleanup is required.}" "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" "${created_at}" >/dev/null 2>&1 || true
        case "${cleanup_status}" in
        54 | 52)
          return "${cleanup_status}"
          ;;
        *)
          return 60
          ;;
        esac
      fi
      ;;
    58)
      return 58
      ;;
    *)
      mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "install-apps" "Unknown app installation failure." "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" "${created_at}" >/dev/null 2>&1 || true
      ;;
    esac
    return "${app_install_status}"
  fi

  if run_stack_site_migrate "${stack_dir}" "${site_name}"; then
    :
  else
    site_migrate_status=$?
    case "${site_migrate_status}" in
    64)
      mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "migrate-site" "${EASY_DOCKER_SITE_ERROR_DETAIL:-Site migration failed.}" "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" "${created_at}" >/dev/null 2>&1 || true
      ;;
    *)
      mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "migrate-site" "Unknown site migration failure." "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" "${created_at}" >/dev/null 2>&1 || true
      ;;
    esac
    return "${site_migrate_status}"
  fi

  updated_at="$(get_current_utc_timestamp)"
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "${installed_app_lines}" "migrate-site" "" "" "${created_at}" "${updated_at}"; then
    return 58
  fi

  return 0
}
