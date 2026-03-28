#!/usr/bin/env bash

stop_stack_with_compose_from_metadata() {
  local stack_dir="${1}"
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

  # shellcheck disable=SC2034 # Read by manage flow after stop_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  compose_project_name="$(get_stack_compose_project_name "${stack_dir}")"

  if [ ! -f "${metadata_path}" ]; then
    return 41
  fi

  if [ ! -f "${env_path}" ]; then
    return 42
  fi

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  if [ -z "${stack_topology}" ]; then
    # shellcheck disable=SC2034 # Read by manage flow after stop_stack_with_compose_from_metadata returns 43.
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="metadata.json missing topology"
    return 43
  fi

  case "${stack_topology}" in
  "single-host") ;;
  *)
    # shellcheck disable=SC2034 # Read by manage flow after stop_stack_with_compose_from_metadata returns 44.
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="${stack_topology}"
    return 44
    ;;
  esac

  env_erpnext_version="$(get_env_file_key_value "${env_path}" "ERPNEXT_VERSION" || true)"
  if [ -z "${env_erpnext_version}" ]; then
    fallback_erpnext_version="$(get_default_erpnext_version || true)"
  fi

  compose_files_lines="$(get_metadata_compose_files_lines "${metadata_path}" || true)"
  if [ -z "${compose_files_lines}" ]; then
    return 45
  fi

  repo_root="$(get_easy_docker_repo_root)"
  while IFS= read -r compose_file; do
    if [ -z "${compose_file}" ]; then
      continue
    fi

    source_compose_path="${repo_root}/${compose_file}"
    if [ ! -f "${source_compose_path}" ]; then
      # shellcheck disable=SC2034 # Read by manage flow after stop_stack_with_compose_from_metadata returns 46.
      EASY_DOCKER_COMPOSE_ERROR_DETAIL="${source_compose_path}"
      return 46
    fi

    compose_args+=(-f "${source_compose_path}")
  done <<EOF
${compose_files_lines}
EOF

  if [ "${#compose_args[@]}" -eq 0 ]; then
    return 45
  fi

  if [ -n "${fallback_erpnext_version}" ]; then
    if ! ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" stop; then
      return 47
    fi
  elif ! docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" stop; then
    return 47
  fi

  return 0
}
