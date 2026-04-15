#!/usr/bin/env bash

easy_docker_test_repo_root() {
  local helper_dir=""

  helper_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  (cd "${helper_dir}/../.." && pwd)
}

easy_docker_test_begin() {
  EASY_DOCKER_TEST_TMPDIR="$(mktemp -d)"
  export EASY_DOCKER_TEST_TMPDIR
  unset EASY_DOCKER_REPO_ROOT_OVERRIDE
}

easy_docker_test_end() {
  if [ -n "${EASY_DOCKER_TEST_TMPDIR:-}" ] && [ -d "${EASY_DOCKER_TEST_TMPDIR}" ]; then
    rm -rf "${EASY_DOCKER_TEST_TMPDIR}"
  fi
}

easy_docker_test_bin_dir() {
  printf '%s/bin\n' "${EASY_DOCKER_TEST_TMPDIR}"
}

easy_docker_test_write_executable() {
  local target_path="${1}"
  local system_bash=""
  shift

  system_bash="$(command -v bash)"
  mkdir -p "$(dirname "${target_path}")"

  {
    printf '#!%s\n' "${system_bash}"
    printf '%s\n' "$@"
  } >"${target_path}"
  chmod +x "${target_path}"
}

easy_docker_test_write_bin_command() {
  local command_name="${1}"
  local target_path=""
  shift

  target_path="$(easy_docker_test_bin_dir)/${command_name}"
  easy_docker_test_write_executable "${target_path}" "$@"
}

easy_docker_test_prepend_bin_dir() {
  PATH="$(easy_docker_test_bin_dir):${PATH}"
  export PATH
}

easy_docker_test_source_common_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  # shellcheck source=scripts/easy-docker/lib/core/commands.sh
  source "${repo_root}/scripts/easy-docker/lib/core/commands.sh"
  # shellcheck source=scripts/easy-docker/lib/core/messages.sh
  source "${repo_root}/scripts/easy-docker/lib/core/messages.sh"
}

easy_docker_test_source_core_render_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/core.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/core.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/render.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/compose/render.sh"
}

easy_docker_test_source_docker_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/checks/docker.sh
  source "${repo_root}/scripts/easy-docker/lib/checks/docker.sh"
}

easy_docker_test_source_gum_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/install/gum/package_manager.sh
  source "${repo_root}/scripts/easy-docker/lib/install/gum/package_manager.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/github_release.sh
  source "${repo_root}/scripts/easy-docker/lib/install/gum/github_release.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/ensure.sh
  source "${repo_root}/scripts/easy-docker/lib/install/gum/ensure.sh"
}

easy_docker_test_create_repo_sandbox() {
  local sandbox_name="${1}"
  local sandbox_root=""

  sandbox_root="${EASY_DOCKER_TEST_TMPDIR}/repo-${sandbox_name}"
  mkdir -p "${sandbox_root}/.easy-docker/stacks" "${sandbox_root}/overrides"
  printf '%s\n' "${sandbox_root}"
}

easy_docker_test_override_repo_root() {
  EASY_DOCKER_REPO_ROOT_OVERRIDE="${1}"
  export EASY_DOCKER_REPO_ROOT_OVERRIDE
}

easy_docker_test_stack_dir() {
  local stack_name="${1}"

  printf '%s/.easy-docker/stacks/%s\n' "${EASY_DOCKER_REPO_ROOT_OVERRIDE}" "${stack_name}"
}

easy_docker_test_install_docker_stub() {
  local log_file=""

  log_file="${EASY_DOCKER_TEST_TMPDIR}/docker.invocations"

  # shellcheck disable=SC2016
  easy_docker_test_write_bin_command docker \
    'set -euo pipefail' \
    "log_file=\"${log_file}\"" \
    'printf '"'"'%s\n'"'"' "docker $*" >>"${log_file}"' \
    'if [ "${1:-}" != "compose" ]; then' \
    '  echo "unexpected docker subcommand: ${1:-}" >&2' \
    '  exit 64' \
    'fi' \
    'if [ "${!#}" != "config" ]; then' \
    '  echo "expected docker compose config invocation" >&2' \
    '  exit 65' \
    'fi' \
    'printf '"'"'invocation=%s\n'"'"' "docker $*"' \
    'printf '"'"'erpnext=%s\n'"'"' "${ERPNEXT_VERSION:-}"'

  easy_docker_test_prepend_bin_dir
}
