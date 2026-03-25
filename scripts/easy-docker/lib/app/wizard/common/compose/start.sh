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

get_stack_compose_runtime_status_label() {
  local result_var="${1}"
  local stack_dir="${2}"
  local metadata_path=""
  local env_path=""
  local stack_topology=""
  local compose_files_lines=""
  local compose_file=""
  local source_compose_path=""
  local env_erpnext_version=""
  local fallback_erpnext_version=""
  local container_ids_lines=""
  local container_id=""
  local container_status_lines=""
  local container_status_line=""
  local container_state=""
  local container_status_text=""
  local first_running_status=""
  local running_status_excerpt=""
  local running_status_varies=0
  local compose_status=0
  local total_containers_count=0
  local running_containers_count=0
  local exited_containers_count=0
  local created_containers_count=0
  local restarting_containers_count=0
  local paused_containers_count=0
  local dead_containers_count=0
  local other_containers_count=0
  local compose_project_name=""
  local repo_root=""
  local status_label=""
  local -a compose_args=()
  local -a docker_ps_args=()

  metadata_path="${stack_dir}/metadata.json"
  env_path="$(get_stack_env_path "${stack_dir}")"
  compose_project_name="$(get_stack_compose_project_name "${stack_dir}")"

  if [ ! -f "${metadata_path}" ]; then
    printf -v "${result_var}" "%s" "Unknown (metadata missing)"
    return 0
  fi

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  if [ -z "${stack_topology}" ]; then
    printf -v "${result_var}" "%s" "Unknown (topology missing)"
    return 0
  fi

  case "${stack_topology}" in
  "single-host") ;;
  *)
    printf -v "${result_var}" "%s" "N/A (${stack_topology})"
    return 0
    ;;
  esac

  if [ ! -f "${env_path}" ]; then
    printf -v "${result_var}" "%s" "Unknown (env missing)"
    return 0
  fi

  env_erpnext_version="$(get_env_file_key_value "${env_path}" "ERPNEXT_VERSION" || true)"
  if [ -z "${env_erpnext_version}" ]; then
    fallback_erpnext_version="$(get_default_erpnext_version || true)"
  fi

  compose_files_lines="$(get_metadata_compose_files_lines "${metadata_path}" || true)"
  if [ -z "${compose_files_lines}" ]; then
    printf -v "${result_var}" "%s" "Unknown (compose files missing)"
    return 0
  fi

  repo_root="$(get_easy_docker_repo_root)"
  while IFS= read -r compose_file; do
    if [ -z "${compose_file}" ]; then
      continue
    fi

    source_compose_path="${repo_root}/${compose_file}"
    if [ ! -f "${source_compose_path}" ]; then
      printf -v "${result_var}" "%s" "Unknown (missing file: ${compose_file})"
      return 0
    fi

    compose_args+=(-f "${source_compose_path}")
  done <<EOF
${compose_files_lines}
EOF

  if [ "${#compose_args[@]}" -eq 0 ]; then
    printf -v "${result_var}" "%s" "Unknown (compose files missing)"
    return 0
  fi

  if [ -n "${fallback_erpnext_version}" ]; then
    container_ids_lines="$(
      ERPNEXT_VERSION="${fallback_erpnext_version}" docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" ps -a -q 2>/dev/null
    )"
    compose_status=$?
  else
    container_ids_lines="$(
      docker compose --project-name "${compose_project_name}" --env-file "${env_path}" "${compose_args[@]}" ps -a -q 2>/dev/null
    )"
    compose_status=$?
  fi

  if [ "${compose_status}" -ne 0 ]; then
    printf -v "${result_var}" "%s" "Unknown (docker compose status failed)"
    return 0
  fi

  if [ -z "${container_ids_lines}" ]; then
    printf -v "${result_var}" "%s" "Not created"
    return 0
  fi

  docker_ps_args=(-a --no-trunc --format "{{.ID}}|{{.State}}|{{.Status}}")
  while IFS= read -r container_id; do
    if [ -n "${container_id}" ]; then
      docker_ps_args+=(--filter "id=${container_id}")
    fi
  done <<EOF
${container_ids_lines}
EOF

  container_status_lines="$(docker ps "${docker_ps_args[@]}" 2>/dev/null)"
  compose_status=$?
  if [ "${compose_status}" -ne 0 ]; then
    printf -v "${result_var}" "%s" "Unknown (docker ps status failed)"
    return 0
  fi

  while IFS= read -r container_status_line; do
    if [ -z "${container_status_line}" ]; then
      continue
    fi

    total_containers_count=$((total_containers_count + 1))
    IFS='|' read -r container_id container_state container_status_text <<EOF
${container_status_line}
EOF

    case "${container_state}" in
    running)
      running_containers_count=$((running_containers_count + 1))
      if [ -z "${first_running_status}" ]; then
        first_running_status="${container_status_text}"
      elif [ "${container_status_text}" != "${first_running_status}" ]; then
        running_status_varies=1
      fi
      ;;
    exited)
      exited_containers_count=$((exited_containers_count + 1))
      ;;
    created)
      created_containers_count=$((created_containers_count + 1))
      ;;
    restarting)
      restarting_containers_count=$((restarting_containers_count + 1))
      ;;
    paused)
      paused_containers_count=$((paused_containers_count + 1))
      ;;
    dead)
      dead_containers_count=$((dead_containers_count + 1))
      ;;
    *)
      other_containers_count=$((other_containers_count + 1))
      ;;
    esac
  done <<EOF
${container_status_lines}
EOF

  if [ "${total_containers_count}" -eq 0 ]; then
    printf -v "${result_var}" "%s" "Not created"
    return 0
  fi

  if [ -n "${first_running_status}" ]; then
    case "${first_running_status}" in
    Up\ *)
      running_status_excerpt="${first_running_status#Up }"
      ;;
    *)
      running_status_excerpt="${first_running_status}"
      ;;
    esac
  fi

  if [ "${running_containers_count}" -eq "${total_containers_count}" ]; then
    status_label="Running (${running_containers_count}/${total_containers_count} containers"
    if [ -n "${running_status_excerpt}" ]; then
      status_label="${status_label}, up ${running_status_excerpt}"
      if [ "${running_status_varies}" -eq 1 ]; then
        status_label="${status_label}+"
      fi
    fi
    status_label="${status_label})"
  elif [ "${running_containers_count}" -gt 0 ]; then
    status_label="Partial (${running_containers_count}/${total_containers_count} running"
    if [ "${restarting_containers_count}" -gt 0 ]; then
      status_label="${status_label}, ${restarting_containers_count} restarting"
    elif [ "${paused_containers_count}" -gt 0 ]; then
      status_label="${status_label}, ${paused_containers_count} paused"
    elif [ "${exited_containers_count}" -gt 0 ]; then
      status_label="${status_label}, ${exited_containers_count} stopped"
    elif [ "${created_containers_count}" -gt 0 ]; then
      status_label="${status_label}, ${created_containers_count} created"
    elif [ "${dead_containers_count}" -gt 0 ]; then
      status_label="${status_label}, ${dead_containers_count} dead"
    elif [ "${other_containers_count}" -gt 0 ]; then
      status_label="${status_label}, ${other_containers_count} other"
    fi

    if [ -n "${running_status_excerpt}" ]; then
      status_label="${status_label}, up ${running_status_excerpt}"
      if [ "${running_status_varies}" -eq 1 ]; then
        status_label="${status_label}+"
      fi
    fi
    status_label="${status_label})"
  elif [ "${restarting_containers_count}" -eq "${total_containers_count}" ]; then
    status_label="Restarting (${total_containers_count} containers)"
  elif [ "${paused_containers_count}" -eq "${total_containers_count}" ]; then
    status_label="Paused (${total_containers_count} containers)"
  elif [ "${created_containers_count}" -eq "${total_containers_count}" ]; then
    status_label="Created (${total_containers_count} containers)"
  else
    status_label="Stopped (${total_containers_count} containers)"
  fi

  printf -v "${result_var}" "%s" "${status_label}"
  return 0
}
