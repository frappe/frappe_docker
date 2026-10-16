#!/usr/bin/env bash

docker_compose_available() {
  docker compose version >/dev/null 2>&1
}

docker_daemon_running() {
  docker info >/dev/null 2>&1
}

docker_supports_command() {
  docker "$@" --help >/dev/null 2>&1
}

get_missing_docker_commands() {
  local missing=()
  local subcommand=""

  for subcommand in ps exec inspect cp build; do
    if ! docker_supports_command "${subcommand}"; then
      missing+=("docker ${subcommand}")
    fi
  done

  for subcommand in config up down logs exec pull ps; do
    if ! docker_supports_command compose "${subcommand}"; then
      missing+=("docker compose ${subcommand}")
    fi
  done

  if [ "${#missing[@]}" -eq 0 ]; then
    return 0
  fi

  printf '%s\n' "${missing[@]}"
  return 1
}

format_missing_commands_list() {
  local missing_commands="${1}"
  local missing_list=""

  missing_list="$(printf '%s' "${missing_commands}" | tr '\n' ',')"
  missing_list="${missing_list%,}"
  missing_list="${missing_list#,}"
  printf '%s\n' "${missing_list}"
}

ensure_docker() {
  local missing_commands=""
  local missing_list=""

  if ! command_exists docker; then
    echo "docker is not installed."
    print_docker_install_guidance
    return 1
  fi

  if ! docker_compose_available; then
    echo "docker compose (Compose v2 command) is not available."
    print_docker_compose_install_guidance
    return 1
  fi

  if ! docker_daemon_running; then
    echo "docker daemon is not running."
    print_docker_daemon_start_guidance
    return 1
  fi

  if ! missing_commands="$(get_missing_docker_commands)"; then
    missing_list="$(format_missing_commands_list "${missing_commands}")"
    echo "Missing required docker commands: ${missing_list}"
    print_docker_command_support_guidance
    return 1
  fi

  return 0
}
