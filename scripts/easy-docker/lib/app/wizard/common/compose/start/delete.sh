#!/usr/bin/env bash

delete_stack_with_compose_from_metadata() {
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
  local custom_image=""
  local custom_tag=""
  local custom_image_ref=""
  local -a compose_args=()

  # shellcheck disable=SC2034 # Read by manage flow after delete_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  compose_project_name="$(get_stack_compose_project_name "${stack_dir}")"

  if [ ! -f "${metadata_path}" ]; then
    return 48
  fi

  if [ ! -f "${env_path}" ]; then
    return 49
  fi

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  if [ -z "${stack_topology}" ]; then
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="metadata.json missing topology"
    return 50
  fi

  case "${stack_topology}" in
  "single-host") ;;
  *)
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="${stack_topology}"
    return 51
    ;;
  esac

  env_erpnext_version="$(get_env_file_key_value "${env_path}" "ERPNEXT_VERSION" || true)"
  if [ -z "${env_erpnext_version}" ]; then
    fallback_erpnext_version="$(get_default_erpnext_version || true)"
  fi

  custom_image="$(get_env_file_key_value "${env_path}" "CUSTOM_IMAGE" || true)"
  custom_tag="$(get_env_file_key_value "${env_path}" "CUSTOM_TAG" || true)"
  if [ -n "${custom_image}" ] && [ -n "${custom_tag}" ]; then
    custom_image_ref="${custom_image}:${custom_tag}"
  fi

  compose_files_lines="$(get_metadata_compose_files_lines "${metadata_path}" || true)"
  if [ -z "${compose_files_lines}" ]; then
    return 52
  fi

  repo_root="$(get_easy_docker_repo_root)"
  while IFS= read -r compose_file; do
    if [ -z "${compose_file}" ]; then
      continue
    fi

    source_compose_path="${repo_root}/${compose_file}"
    if [ ! -f "${source_compose_path}" ]; then
      EASY_DOCKER_COMPOSE_ERROR_DETAIL="${source_compose_path}"
      return 53
    fi

    compose_args+=(-f "${source_compose_path}")
  done <<EOF
${compose_files_lines}
EOF

  if [ "${#compose_args[@]}" -eq 0 ]; then
    return 52
  fi

  if [ -n "${fallback_erpnext_version}" ]; then
    if ! ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" down -v --remove-orphans --rmi local; then
      return 54
    fi
  elif ! docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" down -v --remove-orphans --rmi local; then
    return 54
  fi

  if [ -n "${custom_image_ref}" ]; then
    if docker image inspect "${custom_image_ref}" >/dev/null 2>&1; then
      if ! docker image rm "${custom_image_ref}"; then
        EASY_DOCKER_COMPOSE_ERROR_DETAIL="${custom_image_ref}"
        return 55
      fi
    fi
  fi

  if ! rollback_stack_directory "${stack_dir}"; then
    # shellcheck disable=SC2034 # Read by manage flow after delete_stack_with_compose_from_metadata returns 56.
    EASY_DOCKER_COMPOSE_ERROR_DETAIL="${stack_dir}"
    return 56
  fi

  return 0
}
