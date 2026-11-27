#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_jq_modules
}

teardown() {
  easy_docker_test_end
}

@test "ensure_jq fails when jq is not installed" {
  # shellcheck disable=SC2317
  get_easy_docker_jq_command() {
    return 1
  }

  # shellcheck disable=SC2317
  install_jq_with_package_manager() {
    echo "No supported package manager was found."
    return 1
  }

  run ensure_jq 1

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"jq is not installed. Trying package manager installation..."* ]]
  [[ "${output}" == *"No supported package manager was found."* ]]
  [[ "${output}" == *"Installation fallback is disabled."* ]]
  [[ "${output}" == *"Install jq first:"* ]]
}

@test "ensure_jq succeeds when jq is installed" {
  # shellcheck disable=SC2317
  get_easy_docker_jq_command() {
    printf '%s\n' "jq"
  }

  run ensure_jq 0

  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}

@test "ensure_jq succeeds when only jq.exe is installed" {
  # shellcheck disable=SC2317
  get_easy_docker_jq_command() {
    printf '%s\n' "jq.exe"
  }

  run ensure_jq 0

  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}

@test "should_use_jq_github_fallback rejects non-interactive terminals" {
  local script_path=""
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"
  script_path="${EASY_DOCKER_TEST_TMPDIR}/run-should-use-jq-github-fallback"
  easy_docker_test_write_executable "${script_path}" \
    "source \"${repo_root}/scripts/easy-docker/lib/install/jq/ensure.sh\"" \
    'should_use_jq_github_fallback'

  run "${script_path}" </dev/null

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"GitHub fallback prompt requires an interactive terminal."* ]]
}

@test "ensure_jq succeeds when github fallback installs jq" {
  jq_installed=0

  # shellcheck disable=SC2317
  get_easy_docker_jq_command() {
    if [ "${jq_installed}" -eq 1 ]; then
      printf '%s\n' "jq"
      return 0
    fi

    return 1
  }

  # shellcheck disable=SC2317
  install_jq_with_package_manager() {
    echo "Package manager installation did not succeed."
    return 1
  }

  # shellcheck disable=SC2317
  should_use_jq_github_fallback() {
    return 0
  }

  # shellcheck disable=SC2317
  install_jq_from_github_release() {
    jq_installed=1
    return 0
  }

  run ensure_jq 0

  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Trying pinned GitHub release fallback..."* ]]
  [[ "${output}" == *"jq was installed successfully."* ]]
}

@test "ensure_jq aborts when github fallback is declined" {
  # shellcheck disable=SC2317
  get_easy_docker_jq_command() {
    return 1
  }

  # shellcheck disable=SC2317
  install_jq_with_package_manager() {
    echo "No supported package manager was found."
    return 1
  }

  # shellcheck disable=SC2317
  should_use_jq_github_fallback() {
    return 1
  }

  run ensure_jq 0

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"GitHub fallback was not selected."* ]]
  [[ "${output}" == *"Install jq first:"* ]]
}
