#!/usr/bin/env bats

setup() {
  ROOT_DIR="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
  MAIN_SCRIPT="${ROOT_DIR}/scripts/easy-docker/main.sh"

  SYSTEM_BASH="$(command -v bash)"
  SYSTEM_CAT="$(command -v cat)"
  SYSTEM_CHMOD="$(command -v chmod)"
  SYSTEM_DIRNAME="$(command -v dirname)"
  SYSTEM_ENV="$(command -v env)"
  SYSTEM_MKDIR="$(command -v mkdir)"
  SYSTEM_MKTEMP="$(command -v mktemp)"
  SYSTEM_RM="$(command -v rm)"

  TEST_TMPDIR="$("${SYSTEM_MKTEMP}" -d)"
  STUB_BIN="${TEST_TMPDIR}/bin"
  "${SYSTEM_MKDIR}" -p "${STUB_BIN}"

  write_passthrough_stub cat "${SYSTEM_CAT}"
  write_passthrough_stub dirname "${SYSTEM_DIRNAME}"
}

teardown() {
  if [ -n "${TEST_TMPDIR:-}" ] && [ -d "${TEST_TMPDIR}" ]; then
    "${SYSTEM_RM}" -rf "${TEST_TMPDIR}"
  fi
}

write_stub() {
  local name="$1"
  shift

  {
    printf '#!%s\n' "${SYSTEM_BASH}"
    printf '%s\n' "$@"
  } >"${STUB_BIN}/${name}"
  "${SYSTEM_CHMOD}" +x "${STUB_BIN}/${name}"
}

write_passthrough_stub() {
  local name="$1"
  local target="$2"

  {
    printf '#!%s\n' "${SYSTEM_BASH}"
    printf 'exec "%s" "$@"\n' "${target}"
  } >"${STUB_BIN}/${name}"
  "${SYSTEM_CHMOD}" +x "${STUB_BIN}/${name}"
}

@test "help prints usage and exits cleanly" {
  run "${SYSTEM_ENV}" "PATH=${STUB_BIN}" "${SYSTEM_BASH}" "${MAIN_SCRIPT}" --help

  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage: bash easy-docker.sh [options]"* ]]
  [[ "${output}" == *"--no-installation-fallback"* ]]
}

@test "unknown option is rejected before startup" {
  run "${SYSTEM_ENV}" "PATH=${STUB_BIN}" "${SYSTEM_BASH}" "${MAIN_SCRIPT}" --definitely-unknown

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"Unknown option: --definitely-unknown"* ]]
  [[ "${output}" == *"Usage: bash easy-docker.sh [options]"* ]]
}

@test "missing gum fails without interactive fallback when disabled" {
  run "${SYSTEM_ENV}" "PATH=${STUB_BIN}" "${SYSTEM_BASH}" "${MAIN_SCRIPT}" --no-installation-fallback

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"gum is not installed. Trying package manager installation..."* ]]
  [[ "${output}" == *"No supported package manager was found."* ]]
  [[ "${output}" == *"Installation fallback is disabled."* ]]
  [[ "${output}" == *"Install gum manually:"* ]]
}

@test "missing docker stops after gum dependency succeeds" {
  write_stub gum 'exit 0'

  run "${SYSTEM_ENV}" "PATH=${STUB_BIN}" "${SYSTEM_BASH}" "${MAIN_SCRIPT}" --no-installation-fallback

  [ "${status}" -eq 1 ]
  [[ "${output}" == *"docker is not installed."* ]]
  [[ "${output}" == *"Install Docker first:"* ]]
}
