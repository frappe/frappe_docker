#!/usr/bin/env bash

get_easy_docker_jq_command() {
  if command -v jq >/dev/null 2>&1; then
    printf 'jq\n'
    return 0
  fi

  if command -v jq.exe >/dev/null 2>&1; then
    printf 'jq.exe\n'
    return 0
  fi

  return 1
}

easy_docker_require_jq() {
  get_easy_docker_jq_command >/dev/null 2>&1
}

easy_docker_run_jq() {
  local jq_command=""

  jq_command="$(get_easy_docker_jq_command)" || return 127
  "${jq_command}" "$@"
}
