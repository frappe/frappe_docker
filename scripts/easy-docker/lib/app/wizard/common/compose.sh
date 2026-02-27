#!/usr/bin/env bash

render_stack_compose_from_metadata() {
  local stack_dir="${1}"
  local metadata_path=""
  local env_path=""
  local generated_compose_path=""
  local generated_compose_tmp_path=""
  local compose_files_lines=""
  local compose_file=""
  local source_compose_path=""
  local env_erpnext_version=""
  local fallback_erpnext_version=""
  local repo_root=""
  local -a compose_args=()

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  generated_compose_path="$(get_stack_generated_compose_path "${stack_dir}")"
  generated_compose_tmp_path="${generated_compose_path}.tmp"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ ! -f "${env_path}" ]; then
    return 1
  fi

  env_erpnext_version="$(get_env_file_key_value "${env_path}" "ERPNEXT_VERSION" || true)"
  if [ -z "${env_erpnext_version}" ]; then
    fallback_erpnext_version="$(get_default_erpnext_version || true)"
  fi

  compose_files_lines="$(get_metadata_compose_files_lines "${metadata_path}" || true)"
  if [ -z "${compose_files_lines}" ]; then
    return 1
  fi

  repo_root="$(get_easy_docker_repo_root)"
  while IFS= read -r compose_file; do
    if [ -z "${compose_file}" ]; then
      continue
    fi

    source_compose_path="${repo_root}/${compose_file}"
    if [ ! -f "${source_compose_path}" ]; then
      return 1
    fi

    compose_args+=(-f "${source_compose_path}")
  done <<EOF
${compose_files_lines}
EOF

  if [ "${#compose_args[@]}" -eq 0 ]; then
    return 1
  fi

  if [ -n "${fallback_erpnext_version}" ]; then
    if ! ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --env-file "${env_path}" "${compose_args[@]}" config >"${generated_compose_tmp_path}"; then
      rm -f -- "${generated_compose_tmp_path}" >/dev/null 2>&1 || true
      return 1
    fi
  elif ! docker compose --env-file "${env_path}" "${compose_args[@]}" config >"${generated_compose_tmp_path}"; then
    rm -f -- "${generated_compose_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! mv -- "${generated_compose_tmp_path}" "${generated_compose_path}"; then
    rm -f -- "${generated_compose_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  return 0
}
