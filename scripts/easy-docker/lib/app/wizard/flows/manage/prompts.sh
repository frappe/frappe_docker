#!/usr/bin/env bash

prompt_manage_stack_site_name_with_cancel() {
  local result_var="${1}"
  local stack_name="${2}"
  local stack_dir="${3}"
  local input_site_name=""
  local suggestion=""
  local prompt_status=0

  suggestion="$(get_stack_primary_site_name_suggestion "${stack_dir}" || true)"
  while true; do
    input_site_name="$(prompt_stack_site_name "${stack_name}" "${suggestion}")"
    prompt_status=$?
    if [ "${prompt_status}" -ne 0 ]; then
      return "${FLOW_ABORT_INPUT}"
    fi

    input_site_name="$(printf '%s' "${input_site_name}" | tr -d '\r\n')"
    case "${input_site_name}" in
    "")
      show_warning_and_wait "Site name is required." 2
      ;;
    /back | /Back | /BACK)
      return "${FLOW_ABORT_INPUT}"
      ;;
    *)
      if ! is_valid_stack_site_name "${input_site_name}"; then
        show_warning_and_wait "Site name may only contain letters, numbers, dots, dashes, and underscores." 3
        continue
      fi
      printf -v "${result_var}" "%s" "${input_site_name}"
      return "${FLOW_CONTINUE}"
      ;;
    esac
  done
}

prompt_manage_stack_site_admin_password_with_cancel() {
  local result_var="${1}"
  local stack_name="${2}"
  local input_admin_password=""
  local prompt_status=0

  while true; do
    input_admin_password="$(prompt_stack_site_admin_password "${stack_name}")"
    prompt_status=$?
    if [ "${prompt_status}" -ne 0 ]; then
      return "${FLOW_ABORT_INPUT}"
    fi

    input_admin_password="$(printf '%s' "${input_admin_password}" | tr -d '\r\n')"
    case "${input_admin_password}" in
    "")
      show_warning_and_wait "Administrator password is required." 2
      ;;
    /back | /Back | /BACK)
      return "${FLOW_ABORT_INPUT}"
      ;;
    *)
      printf -v "${result_var}" "%s" "${input_admin_password}"
      return "${FLOW_CONTINUE}"
      ;;
    esac
  done
}

prompt_manage_stack_delete_keyword_with_cancel() {
  local result_var="${1}"
  local stack_name="${2}"
  local delete_confirmation=""
  local prompt_status=0

  while true; do
    delete_confirmation="$(prompt_manage_stack_delete_keyword "${stack_name}")"
    prompt_status=$?
    if [ "${prompt_status}" -ne 0 ]; then
      return "${FLOW_ABORT_INPUT}"
    fi

    delete_confirmation="$(printf '%s' "${delete_confirmation}" | tr -d '\r\n')"
    case "${delete_confirmation}" in
    /back | /Back | /BACK | "")
      return "${FLOW_ABORT_INPUT}"
      ;;
    delete)
      printf -v "${result_var}" "%s" "${delete_confirmation}"
      return "${FLOW_CONTINUE}"
      ;;
    *)
      show_warning_and_wait "Type exactly delete to confirm stack removal." 3
      ;;
    esac
  done
}
