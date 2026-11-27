#!/usr/bin/env bash

reset_easy_docker_site_error_state() {
  EASY_DOCKER_SITE_ERROR_DETAIL=""
  EASY_DOCKER_SITE_ERROR_LOG_PATH=""
}

build_stack_site_error_log_relative_path() {
  local result_var="${1}"
  local action_name="${2:-site-error}"
  local raw_timestamp=""
  local safe_timestamp=""
  local relative_path=""

  raw_timestamp="$(get_current_utc_timestamp)"
  safe_timestamp="$(printf '%s' "${raw_timestamp}" | tr ':' '-')"
  relative_path="$(printf 'logs/%s-%s.log' "${action_name}" "${safe_timestamp}")"
  printf -v "${result_var}" "%s" "${relative_path}"
}

write_stack_site_error_log() {
  local result_var="${1}"
  local stack_dir="${2}"
  local action_name="${3:-site-error}"
  local error_output="${4:-}"
  local relative_path=""
  local log_dir=""
  local absolute_path=""

  if [ -z "${error_output}" ]; then
    printf -v "${result_var}" "%s" ""
    return 0
  fi

  build_stack_site_error_log_relative_path relative_path "${action_name}"
  log_dir="${stack_dir}/logs"
  absolute_path="${stack_dir}/${relative_path}"

  if ! mkdir -p "${log_dir}"; then
    return 1
  fi

  if ! printf '%s\n' "${error_output}" >"${absolute_path}"; then
    return 1
  fi

  printf -v "${result_var}" "%s" "${relative_path}"
  return 0
}

run_stack_backend_bash_command_capture() {
  local result_var="${1}"
  local stack_dir="${2}"
  local backend_command="${3}"
  local command_output=""
  local command_status=0

  reset_easy_docker_site_error_state
  command_output="$(run_stack_backend_bash_command "${stack_dir}" "${backend_command}" 2>&1)"
  command_status=$?

  if [ -n "${command_output}" ]; then
    printf '%s\n' "${command_output}"
  fi

  printf -v "${result_var}" "%s" "${command_output}"
  return "${command_status}"
}

capture_stack_site_error_log() {
  local stack_dir="${1}"
  local action_name="${2:-site-error}"
  local error_output="${3:-}"
  local log_path=""

  EASY_DOCKER_SITE_ERROR_LOG_PATH=""
  if [ -z "${error_output}" ]; then
    return 0
  fi

  if ! write_stack_site_error_log log_path "${stack_dir}" "${action_name}" "${error_output}"; then
    EASY_DOCKER_SITE_ERROR_DETAIL="${EASY_DOCKER_SITE_ERROR_DETAIL:-Failed to write site error log.}"
    return 1
  fi

  # shellcheck disable=SC2034 # Read by manage flow after site bootstrap failures.
  EASY_DOCKER_SITE_ERROR_LOG_PATH="${log_path}"
  return 0
}
