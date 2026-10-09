#!/usr/bin/env bash

is_valid_docker_image_tag() {
  local value="${1}"

  if [ -z "${value}" ] || [ "${#value}" -gt 128 ]; then
    return 1
  fi

  case "${value}" in
  .* | -*)
    return 1
    ;;
  *[!A-Za-z0-9_.-]*)
    return 1
    ;;
  esac

  return 0
}

get_stack_custom_image_name() {
  local stack_dir="${1}"
  local env_path=""

  env_path="$(get_stack_env_path "${stack_dir}")"
  get_env_file_key_value "${env_path}" "CUSTOM_IMAGE"
}

get_stack_custom_image_tag() {
  local stack_dir="${1}"
  local env_path=""

  env_path="$(get_stack_env_path "${stack_dir}")"
  get_env_file_key_value "${env_path}" "CUSTOM_TAG"
}

get_stack_custom_image_ref() {
  local stack_dir="${1}"
  local custom_image=""
  local custom_tag=""

  custom_image="$(get_stack_custom_image_name "${stack_dir}" || true)"
  custom_tag="$(get_stack_custom_image_tag "${stack_dir}" || true)"
  if [ -z "${custom_image}" ] || [ -z "${custom_tag}" ]; then
    return 1
  fi

  printf '%s:%s\n' "${custom_image}" "${custom_tag}"
}

persist_env_file_key_value() {
  local env_path="${1}"
  local key="${2}"
  local value="${3}"
  local tmp_path=""

  if [ ! -f "${env_path}" ]; then
    return 1
  fi

  tmp_path="${env_path}.tmp"
  if ! awk -v key="${key}" -v value="${value}" '
    BEGIN {
      updated = 0
    }
    {
      line = $0
      sub(/\r$/, "", line)

      if (line ~ "^[[:space:]]*(export[[:space:]]+)?" key "[[:space:]]*=") {
        print key "=" value
        updated = 1
        next
      }

      print line
    }
    END {
      if (!updated) {
        print key "=" value
      }
    }
  ' "${env_path}" >"${tmp_path}"; then
    rm -f -- "${tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! mv -- "${tmp_path}" "${env_path}"; then
    rm -f -- "${tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  return 0
}

set_stack_custom_image_tag() {
  local stack_dir="${1}"
  local custom_tag="${2:-}"
  local env_path=""
  local custom_image=""

  env_path="$(get_stack_env_path "${stack_dir}")"
  if [ ! -f "${env_path}" ]; then
    return 31
  fi

  if ! is_valid_docker_image_tag "${custom_tag}"; then
    return 32
  fi

  custom_image="$(get_env_file_key_value "${env_path}" "CUSTOM_IMAGE" || true)"
  if [ -z "${custom_image}" ]; then
    return 33
  fi

  if ! persist_env_file_key_value "${env_path}" "CUSTOM_TAG" "${custom_tag}"; then
    return 34
  fi

  return 0
}

prompt_stack_custom_image_tag_with_cancel() {
  local result_var="${1}"
  local stack_dir="${2}"
  local current_image=""
  local current_tag=""
  local guidance_text=""
  local custom_tag=""
  local prompt_status=0

  current_image="$(get_stack_custom_image_name "${stack_dir}" || true)"
  current_tag="$(get_stack_custom_image_tag "${stack_dir}" || true)"
  guidance_text="$(printf "Current custom image: %s\nCurrent custom tag: %s\n\nEnter the next CUSTOM_TAG for the rebuilt image.\nExample: v1.4.3 or 2026-04-02-appupdate.\nType /back to return." "${current_image:-n/a}" "${current_tag:-n/a}")"

  if prompt_env_value_with_validation custom_tag "${stack_dir}" "CUSTOM_TAG" "${guidance_text}" "${current_tag}" "required" "image_tag"; then
    :
  else
    prompt_status=$?
    return "${prompt_status}"
  fi

  printf -v "${result_var}" "%s" "${custom_tag}"
  return 0
}
