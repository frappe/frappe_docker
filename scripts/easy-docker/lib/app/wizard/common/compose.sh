#!/usr/bin/env bash

EASY_DOCKER_BUILD_ERROR_DETAIL=""
# shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata fails.
EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

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

start_stack_with_compose_from_metadata() {
  local stack_dir="${1}"
  local metadata_path=""
  local env_path=""
  local compose_files_lines=""
  local compose_file=""
  local source_compose_path=""
  local env_erpnext_version=""
  local fallback_erpnext_version=""
  local configured_pull_policy=""
  local runtime_pull_policy=""
  local custom_image=""
  local custom_tag=""
  local image_ref=""
  local stack_topology=""
  local repo_root=""
  local -a compose_args=()

  # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"

  if [ ! -f "${metadata_path}" ]; then
    return 31
  fi

  if [ ! -f "${env_path}" ]; then
    return 32
  fi

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  if [ -z "${stack_topology}" ]; then
    # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata returns 33.
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="metadata.json missing topology"
    return 33
  fi

  case "${stack_topology}" in
  "single-host") ;;
  *)
    # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata returns 34.
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="${stack_topology}"
    return 34
    ;;
  esac

  env_erpnext_version="$(get_env_file_key_value "${env_path}" "ERPNEXT_VERSION" || true)"
  if [ -z "${env_erpnext_version}" ]; then
    fallback_erpnext_version="$(get_default_erpnext_version || true)"
  fi

  configured_pull_policy="$(get_env_file_key_value "${env_path}" "PULL_POLICY" || true)"
  if [ -z "${configured_pull_policy}" ]; then
    custom_image="$(get_env_file_key_value "${env_path}" "CUSTOM_IMAGE" || true)"
    custom_tag="$(get_env_file_key_value "${env_path}" "CUSTOM_TAG" || true)"
    if [ -n "${custom_image}" ] && [ -n "${custom_tag}" ]; then
      image_ref="${custom_image}:${custom_tag}"
      if docker image inspect "${image_ref}" >/dev/null 2>&1; then
        runtime_pull_policy="if_not_present"
      fi
    fi
  fi

  compose_files_lines="$(get_metadata_compose_files_lines "${metadata_path}" || true)"
  if [ -z "${compose_files_lines}" ]; then
    return 35
  fi

  repo_root="$(get_easy_docker_repo_root)"
  while IFS= read -r compose_file; do
    if [ -z "${compose_file}" ]; then
      continue
    fi

    source_compose_path="${repo_root}/${compose_file}"
    if [ ! -f "${source_compose_path}" ]; then
      # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata returns 36.
      EASY_DOCKER_COMPOSE_ERROR_DETAIL="${source_compose_path}"
      return 36
    fi

    compose_args+=(-f "${source_compose_path}")
  done <<EOF
${compose_files_lines}
EOF

  if [ "${#compose_args[@]}" -eq 0 ]; then
    return 35
  fi

  if [ -n "${fallback_erpnext_version}" ] && [ -n "${runtime_pull_policy}" ]; then
    if ! ERPNEXT_VERSION="${fallback_erpnext_version}" PULL_POLICY="${runtime_pull_policy}" docker compose --env-file "${env_path}" "${compose_args[@]}" up -d; then
      return 37
    fi
  elif [ -n "${fallback_erpnext_version}" ]; then
    if ! ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --env-file "${env_path}" "${compose_args[@]}" up -d; then
      return 37
    fi
  elif [ -n "${runtime_pull_policy}" ]; then
    if ! PULL_POLICY="${runtime_pull_policy}" docker compose --env-file "${env_path}" "${compose_args[@]}" up -d; then
      return 37
    fi
  elif ! docker compose --env-file "${env_path}" "${compose_args[@]}" up -d; then
    return 37
  fi

  return 0
}

build_stack_custom_image() {
  local stack_dir="${1}"
  local metadata_path=""
  local env_path=""
  local apps_json_path=""
  local custom_image=""
  local custom_tag=""
  local frappe_branch=""
  local frappe_path="https://github.com/frappe/frappe"
  local repo_root=""
  local containerfile_path=""
  local apps_json_base64=""
  local apps_refs_lines=""
  local app_ref_line=""
  local app_url=""
  local app_branch=""
  local git_error=""
  local image_ref=""

  EASY_DOCKER_BUILD_ERROR_DETAIL=""

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  apps_json_path="${stack_dir}/apps.json"

  if [ ! -f "${metadata_path}" ]; then
    return 11
  fi
  if [ ! -f "${env_path}" ]; then
    return 12
  fi

  custom_image="$(get_env_file_key_value "${env_path}" "CUSTOM_IMAGE" || true)"
  custom_tag="$(get_env_file_key_value "${env_path}" "CUSTOM_TAG" || true)"
  frappe_branch="$(get_stack_frappe_branch "${stack_dir}" || true)"
  if [ -z "${custom_image}" ]; then
    return 13
  fi
  if [ -z "${custom_tag}" ]; then
    return 14
  fi
  if [ -z "${frappe_branch}" ]; then
    return 15
  fi

  # Keep apps.json aligned with current metadata app selection before build.
  if ! persist_stack_apps_json_from_metadata_apps "${stack_dir}"; then
    return 16
  fi
  if [ ! -f "${apps_json_path}" ]; then
    return 17
  fi

  if ! command_exists git; then
    return 22
  fi

  apps_refs_lines="$(
    awk '
      match($0, /"url"[[:space:]]*:[[:space:]]*"([^"]+)"/, url_parts) &&
      match($0, /"branch"[[:space:]]*:[[:space:]]*"([^"]+)"/, branch_parts) {
        print url_parts[1] "|" branch_parts[1]
      }
    ' "${apps_json_path}"
  )"
  if [ -z "${apps_refs_lines}" ]; then
    return 23
  fi

  while IFS= read -r app_ref_line; do
    if [ -z "${app_ref_line}" ]; then
      continue
    fi

    app_url="${app_ref_line%%|*}"
    app_branch="${app_ref_line#*|}"
    if [ -z "${app_url}" ] || [ -z "${app_branch}" ]; then
      continue
    fi

    if git_error="$(git ls-remote --exit-code --heads "${app_url}" "${app_branch}" 2>&1)"; then
      :
    else
      # shellcheck disable=SC2034 # Read by manage flow after build_stack_custom_image returns 24.
      EASY_DOCKER_BUILD_ERROR_DETAIL="$(printf '%s@%s :: %s' "${app_url}" "${app_branch}" "${git_error}")"
      return 24
    fi
  done <<EOF
${apps_refs_lines}
EOF

  if ! command_exists base64; then
    return 18
  fi

  apps_json_base64="$(base64 "${apps_json_path}" | tr -d '\r\n')"
  if [ -z "${apps_json_base64}" ]; then
    return 19
  fi

  repo_root="$(get_easy_docker_repo_root)"
  containerfile_path="${repo_root}/images/layered/Containerfile"
  if [ ! -f "${containerfile_path}" ]; then
    return 20
  fi

  image_ref="${custom_image}:${custom_tag}"

  docker build \
    -f "${containerfile_path}" \
    --build-arg "FRAPPE_BRANCH=${frappe_branch}" \
    --build-arg "FRAPPE_PATH=${frappe_path}" \
    --build-arg "APPS_JSON_BASE64=${apps_json_base64}" \
    -t "${image_ref}" \
    "${repo_root}" || return 21

  return 0
}
