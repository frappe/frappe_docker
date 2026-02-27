#!/usr/bin/env bash

list_existing_stack_names() {
  local setup_type_filter="${1:-}"
  local stacks_dir=""
  local stack_dir=""
  local metadata_path=""
  local stack_name=""
  local stack_setup_type=""

  stacks_dir="$(get_easy_docker_stacks_dir)"
  if [ ! -d "${stacks_dir}" ]; then
    return 0
  fi

  for stack_dir in "${stacks_dir}"/*; do
    if [ ! -d "${stack_dir}" ]; then
      continue
    fi

    metadata_path="${stack_dir}/metadata.json"
    if [ ! -f "${metadata_path}" ]; then
      continue
    fi

    stack_name="$(get_metadata_string_field "${metadata_path}" "stack_name" || true)"
    if [ -z "${stack_name}" ]; then
      continue
    fi

    stack_setup_type="$(get_metadata_string_field "${metadata_path}" "setup_type" || true)"
    if [ -z "${stack_setup_type}" ]; then
      stack_setup_type="production"
    fi

    case "${setup_type_filter}" in
    "" | all) ;;
    *)
      if [ "${stack_setup_type}" != "${setup_type_filter}" ]; then
        continue
      fi
      ;;
    esac

    printf '%s\n' "${stack_name}"
  done | sort
}

stack_name_in_array() {
  local stack_name="${1}"
  shift
  local candidate=""

  for candidate in "$@"; do
    if [ "${candidate}" = "${stack_name}" ]; then
      return 0
    fi
  done

  return 1
}

prompt_stack_name_with_cancel() {
  local result_var="${1}"
  local input_value=""
  local input_status=0

  input_value="$(prompt_new_stack_name)"
  input_status=$?
  if [ "${input_status}" -ne 0 ]; then
    return "${FLOW_ABORT_INPUT}"
  fi

  input_value="$(printf '%s' "${input_value}" | tr -d '\r\n')"

  case "${input_value}" in
  /cancel | /CANCEL | /Cancel)
    return "${FLOW_ABORT_INPUT}"
    ;;
  esac

  printf -v "${result_var}" "%s" "${input_value}"
  return "${FLOW_CONTINUE}"
}

show_warning_and_wait() {
  local message="${1}"
  local seconds="${2:-1}"

  show_warning_message "${message}"
  sleep "${seconds}"
}
