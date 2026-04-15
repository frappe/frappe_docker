#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_gum_modules
}

teardown() {
  easy_docker_test_end
}

@test "should_use_github_fallback rejects non-interactive terminals" {
  local script_path=""
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"
  script_path="${EASY_DOCKER_TEST_TMPDIR}/run-should-use-github-fallback"
  easy_docker_test_write_executable "${script_path}" \
    "source \"${repo_root}/scripts/easy-docker/lib/install/gum/ensure.sh\"" \
    'should_use_github_fallback'

  run "${script_path}" </dev/null

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"GitHub fallback prompt requires an interactive terminal."* ]]
}

@test "ensure_gum succeeds immediately when gum is already installed" {
  # shellcheck disable=SC2317
  command_exists() {
    [ "${1}" = "gum" ]
  }

  run ensure_gum 0

  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}

@test "ensure_gum stops with manual guidance when fallback is disabled" {
  # shellcheck disable=SC2317
  command_exists() {
    return 1
  }

  # shellcheck disable=SC2317
  install_gum_with_package_manager() {
    echo "Package manager installation did not succeed."
    return 1
  }

  run ensure_gum 1

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"gum is not installed. Trying package manager installation..."* ]]
  [[ "${output}" == *"Package manager installation did not succeed."* ]]
  [[ "${output}" == *"Installation fallback is disabled."* ]]
  [[ "${output}" == *"Install gum manually:"* ]]
}

@test "ensure_gum succeeds when github fallback installs gum" {
  gum_installed=0

  # shellcheck disable=SC2317
  command_exists() {
    if [ "${1}" = "gum" ] && [ "${gum_installed}" -eq 1 ]; then
      return 0
    fi
    return 1
  }

  # shellcheck disable=SC2317
  install_gum_with_package_manager() {
    echo "Package manager installation did not succeed."
    return 1
  }

  # shellcheck disable=SC2317
  should_use_github_fallback() {
    return 0
  }

  # shellcheck disable=SC2317
  install_gum_from_github_release() {
    gum_installed=1
    return 0
  }

  run ensure_gum 0

  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Trying pinned GitHub release fallback..."* ]]
  [[ "${output}" == *"gum was installed successfully."* ]]
}

@test "ensure_gum aborts when github fallback is declined" {
  # shellcheck disable=SC2317
  command_exists() {
    return 1
  }

  # shellcheck disable=SC2317
  install_gum_with_package_manager() {
    echo "No supported package manager was found."
    return 1
  }

  # shellcheck disable=SC2317
  should_use_github_fallback() {
    return 1
  }

  run ensure_gum 0

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"GitHub fallback was not selected."* ]]
  [[ "${output}" == *"Install gum manually:"* ]]
}
