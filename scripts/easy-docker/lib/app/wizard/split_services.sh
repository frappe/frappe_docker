#!/usr/bin/env bash

get_split_services_data_mode_id() {
  local data_mode="${1}"

  case "${data_mode}" in
  "Managed Data Services")
    printf 'managed\n'
    ;;
  "External Data Services")
    printf 'external\n'
    ;;
  *)
    return 1
    ;;
  esac
}

get_split_services_redis_id() {
  local redis_choice="${1}"

  case "${redis_choice}" in
  "Managed Redis Services")
    printf 'managed\n'
    ;;
  "External Redis Services")
    printf 'external\n'
    ;;
  "No Redis Services")
    printf 'disabled\n'
    ;;
  *)
    return 1
    ;;
  esac
}

persist_split_services_selection_metadata() {
  local stack_dir="${1}"
  local proxy_mode_id="${2}"
  local data_mode_id="${3}"
  local database_id="${4}"
  local redis_id="${5}"
  local compose_files_lines="${6}"
  local env_lines="${7}"
  local updated_at=""
  local compose_files_json=""
  local env_json_object=""
  local wizard_json_object=""

  updated_at="$(get_current_utc_timestamp)"
  compose_files_json="$(build_compose_files_json_array "${compose_files_lines}")"
  env_json_object="$(build_env_json_object "${env_lines}")"

  if ! wizard_json_object="$(
    cat <<EOF
{
    "topology": "split-services",
    "selection": {
      "proxy_mode_id": "${proxy_mode_id}",
      "data_mode_id": "${data_mode_id}",
      "database_id": "${database_id}",
      "redis_id": "${redis_id}"
    },
    "env": ${env_json_object},
    "compose_files": [
${compose_files_json}
    ],
    "updated_at": "${updated_at}"
  }
EOF
  )"; then
    return 1
  fi

  if ! persist_stack_metadata_wizard_object "${stack_dir}" "${wizard_json_object}"; then
    return 1
  fi

  return 0
}

save_split_services_selection() {
  local stack_dir="${1}"
  local proxy_mode="${2}"
  local data_mode="${3}"
  local database_choice="${4}"
  local redis_choice="${5}"
  local proxy_mode_id=""
  local data_mode_id=""
  local database_id=""
  local redis_id=""
  local database_override=""
  local redis_override=""
  local proxy_overrides=""
  local compose_files_lines=""
  local env_lines=""
  local apps_metadata_json_object=""
  local collect_env_status=0

  proxy_mode_id="$(get_single_host_proxy_mode_id "${proxy_mode}")" || return 1
  data_mode_id="$(get_split_services_data_mode_id "${data_mode}")" || return 1
  database_id="$(get_single_host_database_id "${database_choice}")" || return 1
  redis_id="$(get_split_services_redis_id "${redis_choice}")" || return 1

  if [ "${data_mode_id}" = "managed" ]; then
    database_override="$(get_single_host_database_override "${database_choice}")" || return 1
  fi

  if [ "${redis_id}" = "managed" ]; then
    redis_override="$(get_single_host_redis_override "Include Redis (recommended)")" || return 1
  fi

  proxy_overrides="$(get_single_host_proxy_overrides "${proxy_mode}")" || return 1

  compose_files_lines="compose.yaml"
  if [ -n "${database_override}" ]; then
    compose_files_lines="$(printf '%s\n%s' "${compose_files_lines}" "${database_override}")"
  fi
  if [ -n "${redis_override}" ]; then
    compose_files_lines="$(printf '%s\n%s' "${compose_files_lines}" "${redis_override}")"
  fi
  compose_files_lines="$(printf '%s\n%s' "${compose_files_lines}" "${proxy_overrides}")"

  if collect_split_services_env_lines env_lines apps_metadata_json_object "${stack_dir}" "${proxy_mode_id}" "${data_mode_id}" "${database_id}" "${redis_id}"; then
    :
  else
    collect_env_status=$?
    return "${collect_env_status}"
  fi

  if ! persist_single_host_env_file "${stack_dir}" "${env_lines}"; then
    return 31
  fi

  if persist_split_services_selection_metadata \
    "${stack_dir}" \
    "${proxy_mode_id}" \
    "${data_mode_id}" \
    "${database_id}" \
    "${redis_id}" \
    "${compose_files_lines}" \
    "${env_lines}"; then
    :
  else
    return 32
  fi

  if [ -z "${apps_metadata_json_object}" ]; then
    return 33
  fi

  if persist_stack_metadata_apps_object "${stack_dir}" "${apps_metadata_json_object}"; then
    :
  else
    return 34
  fi

  if ! persist_stack_apps_json_from_metadata_apps "${stack_dir}"; then
    return 35
  fi

  return 0
}
