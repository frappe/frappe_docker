#!/usr/bin/env bash

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
    ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" exec -T backend bash -lc "${wrapped_backend_command}" </dev/null
    return $?
  fi

  docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" exec -T backend bash -lc "${wrapped_backend_command}" </dev/null
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

get_stack_runtime_available_app_lines() {
  local stack_dir="${1}"

  run_stack_backend_bash_command "${stack_dir}" "ls -1 apps"
}
