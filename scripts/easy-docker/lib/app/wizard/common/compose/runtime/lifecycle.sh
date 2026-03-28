#!/usr/bin/env bash

start_stack_with_compose_from_metadata() {
  local stack_dir="${1}"
  local metadata_path=""
  local env_path=""
  local compose_project_name=""
  local fallback_erpnext_version=""
  local configured_pull_policy=""
  local runtime_pull_policy=""
  local custom_image=""
  local custom_tag=""
  local image_ref=""
  local image_inspect_error=""
  local -a compose_args=()

  # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  easy_docker_compose_init_context "${stack_dir}" metadata_path env_path compose_project_name

  if [ ! -f "${metadata_path}" ]; then
    return 31
  fi

  if [ ! -f "${env_path}" ]; then
    return 32
  fi

  if ! easy_docker_compose_require_single_host_topology "${stack_dir}" 33 34; then
    return $?
  fi

  easy_docker_compose_get_fallback_erpnext_version fallback_erpnext_version "${env_path}"

  configured_pull_policy="$(get_env_file_key_value "${env_path}" "PULL_POLICY" || true)"
  if [ -z "${configured_pull_policy}" ]; then
    custom_image="$(get_env_file_key_value "${env_path}" "CUSTOM_IMAGE" || true)"
    custom_tag="$(get_env_file_key_value "${env_path}" "CUSTOM_TAG" || true)"
    if [ -n "${custom_image}" ] && [ -n "${custom_tag}" ]; then
      image_ref="${custom_image}:${custom_tag}"
      if image_inspect_error="$(docker image inspect "${image_ref}" 2>&1 >/dev/null)"; then
        runtime_pull_policy="if_not_present"
      else
        case "${image_inspect_error}" in
        *"No such image"* | *"No such object"*)
          # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata returns 38.
          EASY_DOCKER_COMPOSE_ERROR_DETAIL="${image_ref}"
          return 38
          ;;
        *)
          if [ -z "${image_inspect_error}" ]; then
            image_inspect_error="docker image inspect failed for ${image_ref}"
          fi
          # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata returns 39.
          EASY_DOCKER_COMPOSE_ERROR_DETAIL="${image_inspect_error}"
          return 39
          ;;
        esac
      fi
    fi
  fi

  if ! easy_docker_compose_collect_args compose_args "${metadata_path}" 35 36; then
    return $?
  fi

  if [ -n "${fallback_erpnext_version}" ] && [ -n "${runtime_pull_policy}" ]; then
    if ! ERPNEXT_VERSION="${fallback_erpnext_version}" PULL_POLICY="${runtime_pull_policy}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" up -d; then
      return 37
    fi
  elif [ -n "${fallback_erpnext_version}" ]; then
    if ! ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" up -d; then
      return 37
    fi
  elif [ -n "${runtime_pull_policy}" ]; then
    if ! PULL_POLICY="${runtime_pull_policy}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" up -d; then
      return 37
    fi
  elif ! docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" up -d; then
    return 37
  fi

  return 0
}

stop_stack_with_compose_from_metadata() {
  local stack_dir="${1}"
  local metadata_path=""
  local env_path=""
  local compose_project_name=""
  local fallback_erpnext_version=""
  local -a compose_args=()

  # shellcheck disable=SC2034 # Read by manage flow after stop_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  easy_docker_compose_init_context "${stack_dir}" metadata_path env_path compose_project_name

  if [ ! -f "${metadata_path}" ]; then
    return 41
  fi

  if [ ! -f "${env_path}" ]; then
    return 42
  fi

  if ! easy_docker_compose_require_single_host_topology "${stack_dir}" 43 44; then
    return $?
  fi

  easy_docker_compose_get_fallback_erpnext_version fallback_erpnext_version "${env_path}"

  if ! easy_docker_compose_collect_args compose_args "${metadata_path}" 45 46; then
    return $?
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

delete_stack_with_compose_from_metadata() {
  local stack_dir="${1}"
  local metadata_path=""
  local env_path=""
  local compose_project_name=""
  local fallback_erpnext_version=""
  local custom_image=""
  local custom_tag=""
  local custom_image_ref=""
  local -a compose_args=()

  # shellcheck disable=SC2034 # Read by manage flow after delete_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  easy_docker_compose_init_context "${stack_dir}" metadata_path env_path compose_project_name

  if [ ! -f "${metadata_path}" ]; then
    return 48
  fi

  if [ ! -f "${env_path}" ]; then
    return 49
  fi

  if ! easy_docker_compose_require_single_host_topology "${stack_dir}" 50 51; then
    return $?
  fi

  easy_docker_compose_get_fallback_erpnext_version fallback_erpnext_version "${env_path}"

  custom_image="$(get_env_file_key_value "${env_path}" "CUSTOM_IMAGE" || true)"
  custom_tag="$(get_env_file_key_value "${env_path}" "CUSTOM_TAG" || true)"
  if [ -n "${custom_image}" ] && [ -n "${custom_tag}" ]; then
    custom_image_ref="${custom_image}:${custom_tag}"
  fi

  if ! easy_docker_compose_collect_args compose_args "${metadata_path}" 52 53; then
    return $?
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
