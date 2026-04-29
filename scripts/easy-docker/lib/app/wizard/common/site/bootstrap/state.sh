#!/usr/bin/env bash

stack_site_exists_in_bench() {
  local stack_dir="${1}"
  local site_name="${2}"
  local exists_command=""
  local exists_status=0

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  exists_command="$(
    printf "bench list-sites | grep -F -x -- %s >/dev/null" "$(shell_quote_site_command_arg "${site_name}")"
  )"
  if run_stack_backend_bash_command "${stack_dir}" "${exists_command}" >/dev/null 2>&1; then
    return 0
  fi

  exists_status=$?
  if [ "${exists_status}" -eq 54 ] || [ "${exists_status}" -eq 52 ]; then
    return "${exists_status}"
  fi

  return 1
}

stack_site_directory_exists() {
  local stack_dir="${1}"
  local site_name="${2}"
  local exists_command=""
  local exists_status=0

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  exists_command="$(
    printf "test -d sites/%s" "$(shell_quote_site_command_arg "${site_name}")"
  )"
  if run_stack_backend_bash_command "${stack_dir}" "${exists_command}" >/dev/null 2>&1; then
    return 0
  fi

  exists_status=$?
  if [ "${exists_status}" -eq 54 ] || [ "${exists_status}" -eq 52 ]; then
    return "${exists_status}"
  fi

  return 1
}

stack_site_config_exists() {
  local stack_dir="${1}"
  local site_name="${2}"
  local exists_command=""
  local exists_status=0

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  exists_command="$(
    printf "test -f sites/%s/site_config.json" "$(shell_quote_site_command_arg "${site_name}")"
  )"
  if run_stack_backend_bash_command "${stack_dir}" "${exists_command}" >/dev/null 2>&1; then
    return 0
  fi

  exists_status=$?
  if [ "${exists_status}" -eq 54 ] || [ "${exists_status}" -eq 52 ]; then
    return "${exists_status}"
  fi

  return 1
}

get_stack_site_database_name() {
  local stack_dir="${1}"
  local site_name="${2}"
  local read_command=""

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  read_command="$(
    printf "python - <<'PY'\nimport json\nfrom pathlib import Path\npath = Path('sites') / %s / 'site_config.json'\nwith path.open(encoding='utf-8') as handle:\n    print(json.load(handle).get('db_name', ''))\nPY" \
      "$(shell_quote_site_command_arg "${site_name}")"
  )"

  run_stack_backend_bash_command "${stack_dir}" "${read_command}"
}

get_stack_site_runtime_app_names_lines() {
  local stack_dir="${1}"
  local site_name="${2}"
  local list_apps_command=""

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  list_apps_command="$(
    printf "bench --site %s list-apps | awk 'NF { print \$1 }'" \
      "$(shell_quote_site_command_arg "${site_name}")"
  )"

  run_stack_backend_bash_command "${stack_dir}" "${list_apps_command}"
}

get_stack_site_runtime_selected_apps_lines() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local selected_app_lines=""
  local runtime_app_lines=""
  local selected_app_name=""
  local installed_app_lines=""

  if ! get_stack_selected_installable_apps selected_app_lines "${stack_dir}"; then
    printf -v "${result_var}" "%s" ""
    return 0
  fi

  if [ -z "${selected_app_lines}" ]; then
    printf -v "${result_var}" "%s" ""
    return 0
  fi

  runtime_app_lines="$(get_stack_site_runtime_app_names_lines "${stack_dir}" "${site_name}" || true)"
  if [ -z "${runtime_app_lines}" ]; then
    printf -v "${result_var}" "%s" ""
    return 1
  fi

  while IFS= read -r selected_app_name; do
    if [ -z "${selected_app_name}" ]; then
      continue
    fi

    if ! printf '%s\n' "${runtime_app_lines}" | grep -F -x -- "${selected_app_name}" >/dev/null 2>&1; then
      continue
    fi

    if [ -z "${installed_app_lines}" ]; then
      installed_app_lines="${selected_app_name}"
    else
      installed_app_lines="${installed_app_lines}"$'\n'"${selected_app_name}"
    fi
  done <<EOF
${selected_app_lines}
EOF

  printf -v "${result_var}" "%s" "${installed_app_lines}"
  return 0
}

repair_stack_site_runtime_state() {
  local stack_dir="${1}"
  local database_id=""
  local redis_id=""
  local db_host=""
  local db_port=""
  local repair_command=""

  database_id="$(get_stack_database_id "${stack_dir}" || true)"
  redis_id="$(get_stack_redis_id "${stack_dir}" || true)"

  case "${database_id}" in
  mariadb)
    db_host="db"
    db_port="3306"
    ;;
  postgres)
    db_host="db"
    db_port="5432"
    ;;
  *)
    return 57
    ;;
  esac

  repair_command="$(
    cat <<EOF
mkdir -p sites
test -f sites/common_site_config.json || printf '{}' > sites/common_site_config.json
ls -1 apps > sites/apps.txt
bench set-config -g db_host ${db_host}
bench set-config -gp db_port ${db_port}
EOF
  )"

  case "${redis_id}" in
  enabled)
    repair_command="${repair_command}"$'\n'"bench set-config -g redis_cache redis://redis-cache:6379"
    repair_command="${repair_command}"$'\n'"bench set-config -g redis_queue redis://redis-queue:6379"
    repair_command="${repair_command}"$'\n'"bench set-config -g redis_socketio redis://redis-queue:6379"
    ;;
  "" | disabled)
    :
    ;;
  *)
    return 62
    ;;
  esac

  repair_command="${repair_command}"$'\n'"bench set-config -gp socketio_port 9000"
  repair_command="${repair_command}"$'\n'"bench set-config -g chromium_path /usr/bin/chromium-headless-shell"

  if ! run_stack_backend_bash_command "${stack_dir}" "${repair_command}"; then
    return 62
  fi

  return 0
}

stack_site_has_partial_artifacts() {
  local stack_dir="${1}"
  local site_name="${2}"

  if ! is_safe_stack_site_cleanup_name "${site_name}"; then
    return 61
  fi

  if stack_site_exists_in_bench "${stack_dir}" "${site_name}"; then
    return 0
  fi

  case $? in
  61)
    return 61
    ;;
  54 | 52)
    return $?
    ;;
  esac

  if stack_site_directory_exists "${stack_dir}" "${site_name}"; then
    return 0
  fi

  case $? in
  61)
    return 61
    ;;
  54 | 52)
    return $?
    ;;
  esac

  return 1
}
