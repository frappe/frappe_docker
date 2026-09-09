#!/usr/bin/env bash

backup_configured_stack_site() {
  local stack_dir="${1}"
  local site_name=""
  local backup_command=""
  local backup_output=""
  local command_status=0
  local created_at=""
  local updated_at=""
  local apps_installed_lines=""
  local last_backup_at=""
  local existing_last_backup_at=""
  local backend_status=0

  reset_easy_docker_site_error_state

  if ! stack_supports_single_site_management "${stack_dir}"; then
    return 72
  fi

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 73
  fi

  if stack_backend_service_is_running "${stack_dir}"; then
    :
  else
    backend_status=$?
    case "${backend_status}" in
    54)
      return 74
      ;;
    52)
      return 72
      ;;
    *)
      return 71
      ;;
    esac
  fi

  created_at="$(get_stack_site_created_at "${stack_dir}" || true)"
  apps_installed_lines="$(get_stack_site_apps_installed_lines "${stack_dir}" || true)"
  existing_last_backup_at="$(get_stack_site_last_backup_at "${stack_dir}" || true)"

  backup_command="$(
    printf "bench --site %s backup --with-files" \
      "$(shell_quote_site_command_arg "${site_name}")"
  )"

  if run_stack_backend_bash_command_capture backup_output "${stack_dir}" "${backup_command}"; then
    :
  else
    command_status=$?
    EASY_DOCKER_SITE_ERROR_DETAIL="$(printf "bench backup failed for '%s'." "${site_name}")"
    capture_stack_site_error_log "${stack_dir}" "site-backup-error" "${backup_output}" >/dev/null 2>&1 || true
    updated_at="$(get_current_utc_timestamp)"
    if ! persist_stack_site_metadata \
      "${stack_dir}" \
      "single-site" \
      "${site_name}" \
      "${apps_installed_lines}" \
      "backup-site" \
      "${EASY_DOCKER_SITE_ERROR_DETAIL}" \
      "${EASY_DOCKER_SITE_ERROR_LOG_PATH}" \
      "${created_at}" \
      "${updated_at}" \
      "${existing_last_backup_at}"; then
      return 76
    fi
    case "${command_status}" in
    54)
      return 74
      ;;
    52)
      return 72
      ;;
    *)
      return 75
      ;;
    esac
  fi

  last_backup_at="$(get_current_utc_timestamp)"
  updated_at="${last_backup_at}"
  if ! persist_stack_site_metadata \
    "${stack_dir}" \
    "single-site" \
    "${site_name}" \
    "${apps_installed_lines}" \
    "backup-site" \
    "" \
    "" \
    "${created_at}" \
    "${updated_at}" \
    "${last_backup_at}"; then
    return 76
  fi

  return 0
}
