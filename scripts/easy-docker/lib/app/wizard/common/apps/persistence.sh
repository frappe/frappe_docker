#!/usr/bin/env bash

render_stack_metadata_top_level_entry_from_json_file() {
  local metadata_path="${1}"
  local metadata_key="${2}"
  local entry_value=""
  local rendered_entry=""
  local line=""
  local delta=0
  local depth=0
  local started=0

  while IFS= read -r line || [ -n "${line}" ]; do
    if [ "${started}" -eq 0 ]; then
      case "${line}" in
      "  \"${metadata_key}\":"*)
        entry_value="${line#  \""${metadata_key}"\": }"
        entry_value="${entry_value%,}"
        if [[ "${entry_value}" == \{* || "${entry_value}" == \[* ]]; then
          rendered_entry="  \"${metadata_key}\": ${entry_value}"
          started=1
          delta="$(count_stack_metadata_json_structure_delta "${entry_value}")"
          depth=$((depth + delta))
          if [ "${depth}" -le 0 ]; then
            printf '%s' "${rendered_entry}"
            return 0
          fi
        else
          printf '  "%s": %s' "${metadata_key}" "${entry_value}"
          return 0
        fi
        ;;
      esac
      continue
    fi

    delta="$(count_stack_metadata_json_structure_delta "${line}")"
    if [ $((depth + delta)) -le 0 ]; then
      rendered_entry="${rendered_entry}"$'\n'"${line%,}"
      printf '%s' "${rendered_entry}"
      return 0
    fi

    rendered_entry="${rendered_entry}"$'\n'"${line}"
    depth=$((depth + delta))
  done <"${metadata_path}"

  return 1
}

count_stack_metadata_json_structure_delta() {
  local line="${1}"
  local opens=0
  local closes=0
  local matches=""

  matches="${line//[^\{]/}"
  opens=$((opens + ${#matches}))
  matches="${line//[^\[]/}"
  opens=$((opens + ${#matches}))
  matches="${line//[^\}]/}"
  closes=$((closes + ${#matches}))
  matches="${line//[^\]]/}"
  closes=$((closes + ${#matches}))

  printf '%s\n' "$((opens - closes))"
}

build_stack_metadata_top_level_object_content() {
  local result_var="${1}"
  local metadata_path="${2}"
  local object_key="${3}"
  local object_json="${4}"
  shift 4
  local rendered_metadata=""
  local entry_json=""
  local metadata_key=""
  local index=0
  local total_keys=0
  local -a ordered_keys=("$@")

  total_keys="${#ordered_keys[@]}"
  rendered_metadata="{"
  if [ "${total_keys}" -gt 0 ]; then
    rendered_metadata="${rendered_metadata}"$'\n'
  fi

  for index in "${!ordered_keys[@]}"; do
    metadata_key="${ordered_keys[${index}]}"
    if [ "${metadata_key}" = "${object_key}" ]; then
      entry_json="$(printf '  "%s": %s' "${metadata_key}" "${object_json}")"
    else
      entry_json="$(render_stack_metadata_top_level_entry_from_json_file "${metadata_path}" "${metadata_key}")" || return 1
    fi

    rendered_metadata="${rendered_metadata}${entry_json}"
    if [ "${index}" -lt $((total_keys - 1)) ]; then
      rendered_metadata="${rendered_metadata},"
    fi
    rendered_metadata="${rendered_metadata}"$'\n'
  done

  rendered_metadata="${rendered_metadata}}"$'\n'
  if ! printf '%s' "${rendered_metadata}" | easy_docker_run_jq -e 'type == "object"' >/dev/null 2>&1; then
    return 1
  fi

  printf -v "${result_var}" "%s" "${rendered_metadata}"
}

persist_stack_metadata_top_level_object() {
  local stack_dir="${1}"
  local object_key="${2}"
  local object_json="${3}"
  local insert_before_key="${4:-}"
  local metadata_path=""
  local metadata_tmp_path=""
  local metadata_content=""
  local existing_key=""
  local inserted=0
  local -a existing_keys=()
  local -a ordered_keys=()

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ -z "${object_json}" ]; then
    return 1
  fi

  if ! easy_docker_require_jq; then
    return 1
  fi

  if ! easy_docker_run_jq -e 'type == "object"' "${metadata_path}" >/dev/null 2>&1; then
    return 1
  fi

  object_json="${object_json%$'\n'}"
  if ! printf '%s\n' "${object_json}" | easy_docker_run_jq -e 'type == "object"' >/dev/null 2>&1; then
    return 1
  fi

  mapfile -t existing_keys < <(easy_docker_run_jq -r 'keys_unsorted[]' "${metadata_path}") || return 1

  for existing_key in "${existing_keys[@]}"; do
    if [ "${existing_key}" = "${object_key}" ]; then
      continue
    fi

    if [ "${inserted}" -eq 0 ] && [ -n "${insert_before_key}" ] && [ "${existing_key}" = "${insert_before_key}" ]; then
      ordered_keys+=("${object_key}")
      inserted=1
    fi

    ordered_keys+=("${existing_key}")
  done

  if [ "${inserted}" -eq 0 ]; then
    ordered_keys+=("${object_key}")
  fi

  build_stack_metadata_top_level_object_content metadata_content "${metadata_path}" "${object_key}" "${object_json}" "${ordered_keys[@]}" || return 1

  if ! printf '%s' "${metadata_content}" >"${metadata_tmp_path}"; then
    rm -f -- "${metadata_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! mv -- "${metadata_tmp_path}" "${metadata_path}"; then
    rm -f -- "${metadata_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  return 0
}

persist_stack_metadata_apps_object() {
  local stack_dir="${1}"
  local apps_json_object="${2}"

  persist_stack_metadata_top_level_object "${stack_dir}" "apps" "${apps_json_object}" "wizard"
}

persist_stack_metadata_wizard_object() {
  local stack_dir="${1}"
  local wizard_json_object="${2}"

  persist_stack_metadata_top_level_object "${stack_dir}" "wizard" "${wizard_json_object}"
}
