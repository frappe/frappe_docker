#!/usr/bin/env bash

easy_docker_compose_init_context() {
  local stack_dir="${1}"
  local metadata_var="${2}"
  local env_var="${3}"
  local project_var="${4}"
  local metadata_path=""
  local env_path=""
  local compose_project_name=""

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  compose_project_name="$(get_stack_compose_project_name "${stack_dir}")"

  printf -v "${metadata_var}" "%s" "${metadata_path}"
  printf -v "${env_var}" "%s" "${env_path}"
  printf -v "${project_var}" "%s" "${compose_project_name}"
}

easy_docker_compose_get_fallback_erpnext_version() {
  local result_var="${1}"
  local env_path="${2}"
  local env_erpnext_version=""
  local fallback_erpnext_version=""

  env_erpnext_version="$(get_env_file_key_value "${env_path}" "ERPNEXT_VERSION" || true)"
  if [ -z "${env_erpnext_version}" ]; then
    fallback_erpnext_version="$(get_default_erpnext_version || true)"
  fi

  printf -v "${result_var}" "%s" "${fallback_erpnext_version}"
}

easy_docker_compose_require_supported_topology() {
  local stack_dir="${1}"
  local missing_topology_code="${2}"
  local unsupported_topology_code="${3}"
  local stack_topology=""

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  if [ -z "${stack_topology}" ]; then
    # shellcheck disable=SC2034 # Read by callers after topology resolution fails.
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="metadata.json missing topology"
    return "${missing_topology_code}"
  fi

  case "${stack_topology}" in
  "single-host" | "split-services")
    return 0
    ;;
  *)
    # shellcheck disable=SC2034 # Read by callers after unsupported topology is returned.
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="${stack_topology}"
    return "${unsupported_topology_code}"
    ;;
  esac
}

easy_docker_compose_collect_args() {
  local result_array_name="${1}"
  local metadata_path="${2}"
  local missing_compose_code="${3}"
  local missing_file_code="${4}"
  local compose_files_lines=""
  local compose_file=""
  local source_compose_path=""
  local repo_root=""
  local -n compose_args_ref="${result_array_name}"

  compose_args_ref=()
  compose_files_lines="$(get_metadata_compose_files_lines "${metadata_path}" || true)"
  if [ -z "${compose_files_lines}" ]; then
    return "${missing_compose_code}"
  fi

  repo_root="$(get_easy_docker_repo_root)"
  while IFS= read -r compose_file; do
    if [ -z "${compose_file}" ]; then
      continue
    fi

    source_compose_path="${repo_root}/${compose_file}"
    if [ ! -f "${source_compose_path}" ]; then
      # shellcheck disable=SC2034 # Read by callers after compose file resolution fails.
      EASY_DOCKER_COMPOSE_ERROR_DETAIL="${source_compose_path}"
      return "${missing_file_code}"
    fi

    compose_args_ref+=(-f "${source_compose_path}")
  done <<EOF
${compose_files_lines}
EOF

  if [ "${#compose_args_ref[@]}" -eq 0 ]; then
    return "${missing_compose_code}"
  fi

  return 0
}
