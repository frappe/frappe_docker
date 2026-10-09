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

prompt_frappe_branch_with_cancel() {
  local result_var="${1}"
  local stack_name="${2}"
  local options_lines=""
  local selection=""
  local selection_status=0
  local selected_label=""
  local selected_branch=""
  local default_branch=""
  local default_label=""
  local version_entry=""
  local version_id=""
  local version_label=""
  local version_branch=""
  local -a version_entries=()

  mapfile -t version_entries < <(get_frappe_versions_catalog_entries || true)
  for version_entry in "${version_entries[@]}"; do
    IFS='|' read -r version_id version_label version_branch <<<"${version_entry}"
    if [ -z "${version_id}" ] || [ -z "${version_label}" ] || [ -z "${version_branch}" ]; then
      continue
    fi

    if [ -z "${options_lines}" ]; then
      options_lines="${version_label}"
    else
      options_lines="$(printf '%s\n%s' "${options_lines}" "${version_label}")"
    fi
  done

  if [ -z "${options_lines}" ]; then
    show_warning_and_wait "No Frappe version profiles available in scripts/easy-docker/config/frappe.tsv." 3
    return 1
  fi

  default_branch="$(get_default_frappe_branch || true)"
  default_label="$(get_frappe_version_label_by_branch "${default_branch}" || true)"

  selection="$(show_frappe_version_profile_menu "${stack_name}" "${options_lines}" "${default_label}")"
  selection_status=$?
  if [ "${selection_status}" -ne 0 ]; then
    return "${FLOW_ABORT_INPUT}"
  fi

  selected_label="$(printf '%s' "${selection}" | tr -d '\r\n')"
  case "${selected_label}" in
  "" | "Back")
    return "${FLOW_ABORT_INPUT}"
    ;;
  esac

  selected_branch="$(get_frappe_version_branch_by_label "${selected_label}" || true)"
  if [ -z "${selected_branch}" ]; then
    show_warning_and_wait "Could not resolve branch for selected profile: ${selected_label}" 2
    return 1
  fi

  printf -v "${result_var}" "%s" "${selected_branch}"
  return "${FLOW_CONTINUE}"
}

show_warning_and_wait() {
  local message="${1}"
  local seconds="${2:-1}"

  show_warning_message "${message}"
  sleep "${seconds}"
}
