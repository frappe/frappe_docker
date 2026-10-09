#!/usr/bin/env bash

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
  local image_inspect_error=""
  local compose_project_name=""
  local stack_topology=""
  local repo_root=""
  local -a compose_args=()

  # shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  compose_project_name="$(get_stack_compose_project_name "${stack_dir}")"

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
  "single-host" | "split-services") ;;
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
