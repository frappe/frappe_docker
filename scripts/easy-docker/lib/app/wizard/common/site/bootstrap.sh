#!/usr/bin/env bash

is_valid_stack_site_name() {
  local site_name="${1}"

  if [ -z "${site_name}" ]; then
    return 1
  fi

  case "${site_name}" in
  *[!A-Za-z0-9._-]*)
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

is_safe_stack_site_cleanup_name() {
  local site_name="${1}"

  if ! is_valid_stack_site_name "${site_name}"; then
    return 1
  fi

  case "${site_name}" in
  "." | ".." | "/" | "")
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

shell_quote_site_command_arg() {
  local raw_value="${1}"

  printf "'%s'" "$(printf '%s' "${raw_value}" | sed "s/'/'\"'\"'/g")"
}

get_stack_primary_site_name_suggestion() {
  local stack_dir="${1}"
  local env_path=""
  local site_domains=""
  local primary_domain=""

  env_path="$(get_stack_env_path "${stack_dir}")"
  site_domains="$(get_env_file_key_value "${env_path}" "SITE_DOMAINS" || true)"
  primary_domain="${site_domains%%,*}"
  primary_domain="${primary_domain%% *}"

  if [ -n "${primary_domain}" ]; then
    printf '%s\n' "${primary_domain}"
    return 0
  fi

  printf '%s.localhost\n' "${stack_dir##*/}"
  return 0
}

get_stack_database_id() {
  local stack_dir="${1}"

  get_metadata_string_field "${stack_dir}/metadata.json" "database_id"
}

get_stack_redis_id() {
  local stack_dir="${1}"

  get_metadata_string_field "${stack_dir}/metadata.json" "redis_id"
}

get_stack_database_root_password() {
  local stack_dir="${1}"
  local env_path=""
  local db_password=""

  env_path="$(get_stack_env_path "${stack_dir}")"
  db_password="$(get_env_file_key_value "${env_path}" "DB_PASSWORD" || true)"
  if [ -z "${db_password}" ]; then
    db_password="123"
  fi

  printf '%s\n' "${db_password}"
  return 0
}

stack_site_bootstrap_supports_database() {
  local stack_dir="${1}"
  local database_id=""

  database_id="$(get_stack_database_id "${stack_dir}" || true)"
  case "${database_id}" in
  mariadb)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

stack_supports_single_site_management() {
  local stack_dir="${1}"
  local stack_topology=""

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  case "${stack_topology}" in
  single-host)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

run_stack_backend_bash_command() {
  local stack_dir="${1}"
  local backend_command="${2}"
  local wrapped_backend_command=""
  local metadata_path=""
  local env_path=""
  local compose_files_lines=""
  local compose_file=""
  local source_compose_path=""
  local env_erpnext_version=""
  local fallback_erpnext_version=""
  local compose_project_name=""
  local stack_topology=""
  local repo_root=""
  local -a compose_args=()

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  compose_project_name="$(get_stack_compose_project_name "${stack_dir}")"

  if [ ! -f "${metadata_path}" ]; then
    return 54
  fi

  if [ ! -f "${env_path}" ]; then
    return 54
  fi

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  if [ -z "${stack_topology}" ]; then
    return 54
  fi

  case "${stack_topology}" in
  single-host) ;;
  *)
    return 52
    ;;
  esac

  env_erpnext_version="$(get_env_file_key_value "${env_path}" "ERPNEXT_VERSION" || true)"
  if [ -z "${env_erpnext_version}" ]; then
    fallback_erpnext_version="$(get_default_erpnext_version || true)"
  fi

  compose_files_lines="$(get_metadata_compose_files_lines "${metadata_path}" || true)"
  if [ -z "${compose_files_lines}" ]; then
    return 54
  fi

  repo_root="$(get_easy_docker_repo_root)"
  while IFS= read -r compose_file; do
    if [ -z "${compose_file}" ]; then
      continue
    fi

    source_compose_path="${repo_root}/${compose_file}"
    if [ ! -f "${source_compose_path}" ]; then
      return 54
    fi

    compose_args+=(-f "${source_compose_path}")
  done <<EOF
${compose_files_lines}
EOF

  if [ "${#compose_args[@]}" -eq 0 ]; then
    return 54
  fi

  wrapped_backend_command="$(printf "cd /home/frappe/frappe-bench && %s" "${backend_command}")"

  if [ -n "${fallback_erpnext_version}" ]; then
    ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" exec -T backend bash -lc "${wrapped_backend_command}"
    return $?
  fi

  docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" exec -T backend bash -lc "${wrapped_backend_command}"
}

stack_backend_service_is_running() {
  local stack_dir="${1}"
  local backend_ready_status=0

  if run_stack_backend_bash_command "${stack_dir}" "true" >/dev/null 2>&1; then
    return 0
  fi

  backend_ready_status=$?
  if [ "${backend_ready_status}" -eq 54 ] || [ "${backend_ready_status}" -eq 52 ]; then
    return "${backend_ready_status}"
  fi

  # If exec fails, the backend service is not ready for site actions yet.
  return 1
}

stack_database_service_is_reachable() {
  local stack_dir="${1}"
  local reachability_command=""
  local db_ready_status=0

  IFS= read -r -d '' reachability_command <<'EOF' || true
python - <<'PY'
import json
import socket
from pathlib import Path

config_path = Path("/home/frappe/frappe-bench/sites/common_site_config.json")
with config_path.open(encoding="utf-8") as handle:
    config = json.load(handle)

db_host = config.get("db_host")
db_port = int(config.get("db_port", 3306))
socket.create_connection((db_host, db_port), 5).close()
PY
EOF

  if run_stack_backend_bash_command "${stack_dir}" "${reachability_command}" >/dev/null 2>&1; then
    return 0
  fi

  db_ready_status=$?
  if [ "${db_ready_status}" -eq 54 ] || [ "${db_ready_status}" -eq 52 ]; then
    return "${db_ready_status}"
  fi

  return 1
}

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

get_stack_common_db_endpoint() {
  local stack_dir="${1}"
  local read_command=""

  read_command="$(
    cat <<'EOF'
python - <<'PY'
import json
from pathlib import Path
path = Path("sites/common_site_config.json")
with path.open(encoding="utf-8") as handle:
    config = json.load(handle)
print(f"{config.get('db_host', '')}|{config.get('db_port', 3306)}")
PY
EOF
  )"

  run_stack_backend_bash_command "${stack_dir}" "${read_command}"
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

create_first_stack_site() {
  local stack_dir="${1}"
  local site_name="${2}"
  local admin_password="${3}"
  local create_site_command=""

  create_site_command="$(
    printf "bench new-site %s --mariadb-user-host-login-scope='%%' --admin-password %s --db-root-username root --db-root-password %s" \
      "$(shell_quote_site_command_arg "${site_name}")" \
      "$(shell_quote_site_command_arg "${admin_password}")" \
      "$(shell_quote_site_command_arg "$(get_stack_database_root_password "${stack_dir}")")"
  )"

  if ! run_stack_backend_bash_command "${stack_dir}" "${create_site_command}"; then
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

  if ! get_stack_selected_installable_apps selected_app_lines "${stack_dir}"; then
    printf -v "${result_var}" "%s" ""
    return 0
  fi

  while IFS= read -r app_name; do
    if [ -z "${app_name}" ]; then
      continue
    fi

    install_app_command="$(
      printf "bench --site %s install-app %s" \
        "$(shell_quote_site_command_arg "${site_name}")" \
        "$(shell_quote_site_command_arg "${app_name}")"
    )"

    if ! run_stack_backend_bash_command "${stack_dir}" "${install_app_command}"; then
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
      "apps_installing" \
      "${installed_app_lines}" \
      "install-apps" \
      "" \
      "$(get_stack_site_created_at "${stack_dir}" || true)" \
      "$(get_current_utc_timestamp)"; then
      return 58
    fi
  done <<EOF
${selected_app_lines}
EOF

  printf -v "${result_var}" "%s" "${installed_app_lines}"
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
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "requested" "" "create-site" "" "${created_at}" "${updated_at}"; then
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
      mark_stack_site_failed "${stack_dir}" "${site_name}" "" "cleanup-partial-site" "Partial site artifacts could not be removed automatically. Manual cleanup is required." "" >/dev/null 2>&1 || true
      return 60
      ;;
    *)
      mark_stack_site_failed "${stack_dir}" "${site_name}" "" "cleanup-partial-site" "Unexpected cleanup failure before create-site." "${created_at}" >/dev/null 2>&1 || true
      return 60
      ;;
    esac
  fi

  updated_at="${created_at}"
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "creating" "" "create-site" "" "${created_at}" "${updated_at}"; then
    return 58
  fi

  if create_first_stack_site "${stack_dir}" "${site_name}" "${admin_password}"; then
    :
  else
    site_create_status=$?
    if cleanup_partial_stack_site "${stack_dir}" "${site_name}"; then
      mark_stack_site_failed "${stack_dir}" "${site_name}" "" "create-site" "bench new-site failed. Partial site data was cleaned up automatically." "${created_at}" >/dev/null 2>&1 || true
      return "${site_create_status}"
    fi

    cleanup_status=$?
    mark_stack_site_failed "${stack_dir}" "${site_name}" "" "create-site" "bench new-site failed and partial site data could not be cleaned up automatically. Manual cleanup is required." "${created_at}" >/dev/null 2>&1 || true
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
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "created" "" "create-site" "" "${created_at}" "${updated_at}"; then
    return 58
  fi

  if install_stack_apps_on_site installed_app_lines "${stack_dir}" "${site_name}"; then
    :
  else
    app_install_status=$?
    case "${app_install_status}" in
    56)
      if cleanup_partial_stack_site "${stack_dir}" "${site_name}"; then
        mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "install-apps" "App installation failed. Partial site data was cleaned up automatically." "${created_at}" >/dev/null 2>&1 || true
      else
        cleanup_status=$?
        mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "install-apps" "App installation failed and partial site data could not be cleaned up automatically. Manual cleanup is required." "${created_at}" >/dev/null 2>&1 || true
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
      mark_stack_site_failed "${stack_dir}" "${site_name}" "${installed_app_lines}" "install-apps" "Unknown app installation failure." "${created_at}" >/dev/null 2>&1 || true
      ;;
    esac
    return "${app_install_status}"
  fi

  updated_at="$(get_current_utc_timestamp)"
  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "ready" "${installed_app_lines}" "install-apps" "" "${created_at}" "${updated_at}"; then
    return 58
  fi

  return 0
}
