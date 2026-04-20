#!/usr/bin/env bash

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
  if ! easy_docker_require_jq; then
    return 25
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
    easy_docker_run_jq -r '.[]? | select((.url // "") != "" and (.branch // "") != "") | "\(.url)|\(.branch)"' "${apps_json_path}"
  )" || return 23
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
