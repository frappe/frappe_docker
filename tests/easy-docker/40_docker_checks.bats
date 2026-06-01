#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_docker_modules
}

teardown() {
  easy_docker_test_end
}

@test "format_missing_commands_list joins newline separated commands" {
  run format_missing_commands_list $'docker exec\ndocker compose pull\ndocker compose logs'

  [ "${status}" -eq 0 ]
  [ "${output}" = "docker exec,docker compose pull,docker compose logs" ]
}

@test "get_missing_docker_commands reports missing docker and compose subcommands" {
  docker_supports_command() {
    case "$*" in
    "exec" | "compose pull")
      return 1
      ;;
    *)
      return 0
      ;;
    esac
  }

  run get_missing_docker_commands

  [ "${status}" -eq 1 ]
  [ "${output}" = $'docker exec\ndocker compose pull' ]
}

@test "ensure_docker fails when docker is not installed" {
  # shellcheck disable=SC2317
  command_exists() {
    return 1
  }

  run ensure_docker

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"docker is not installed."* ]]
  [[ "${output}" == *"Install Docker first:"* ]]
}

@test "ensure_docker fails when docker compose is unavailable" {
  # shellcheck disable=SC2317
  command_exists() {
    [ "${1}" = "docker" ]
  }

  # shellcheck disable=SC2317
  docker_compose_available() {
    return 1
  }

  run ensure_docker

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"docker compose (Compose v2 command) is not available."* ]]
  [[ "${output}" == *"This script requires Docker Compose v2 via the 'docker compose' command."* ]]
}

@test "ensure_docker fails when the docker daemon is not running" {
  # shellcheck disable=SC2317
  command_exists() {
    [ "${1}" = "docker" ]
  }

  # shellcheck disable=SC2317
  docker_compose_available() {
    return 0
  }

  # shellcheck disable=SC2317
  docker_daemon_running() {
    return 1
  }

  run ensure_docker

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"docker daemon is not running."* ]]
  [[ "${output}" == *"Start the Docker daemon/service and retry."* ]]
}

@test "ensure_docker reports missing required docker commands" {
  # shellcheck disable=SC2317
  command_exists() {
    [ "${1}" = "docker" ]
  }

  # shellcheck disable=SC2317
  docker_compose_available() {
    return 0
  }

  # shellcheck disable=SC2317
  docker_daemon_running() {
    return 0
  }

  # shellcheck disable=SC2317
  get_missing_docker_commands() {
    printf '%s\n' "docker exec" "docker compose pull"
    return 1
  }

  run ensure_docker

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"Missing required docker commands: docker exec,docker compose pull"* ]]
  [[ "${output}" == *"Standard 'docker' and 'docker compose' commands are required."* ]]
}

@test "ensure_docker succeeds when all prerequisites are satisfied" {
  # shellcheck disable=SC2317
  command_exists() {
    [ "${1}" = "docker" ]
  }

  # shellcheck disable=SC2317
  docker_compose_available() {
    return 0
  }

  # shellcheck disable=SC2317
  docker_daemon_running() {
    return 0
  }

  # shellcheck disable=SC2317
  get_missing_docker_commands() {
    return 0
  }

  run ensure_docker

  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}
