#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_screen_modules_with_tty_stdout
}

teardown() {
  easy_docker_test_end
}

@test "enter_alt_screen suppresses tput stderr when terminfo is unavailable" {
  easy_docker_test_write_bin_command tput \
    'echo '"'"'tput: unknown terminal "xterm-256color"'"'"' >&2' \
    'exit 1'
  easy_docker_test_prepend_bin_dir

  run enter_alt_screen
  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}

@test "enter_alt_screen and leave_alt_screen track successful terminal state" {
  local log_file=""
  local expected_log=""

  log_file="${EASY_DOCKER_TEST_TMPDIR}/tput.log"

  easy_docker_test_write_bin_command tput \
    "printf '%s\\n' \"\${1:-}\" >>\"${log_file}\"" \
    'exit 0'
  easy_docker_test_prepend_bin_dir

  enter_alt_screen
  [ "${ALT_SCREEN_ACTIVE}" = "1" ]
  [ "${CURSOR_HIDDEN}" = "1" ]

  leave_alt_screen
  [ "${ALT_SCREEN_ACTIVE}" = "0" ]
  [ "${CURSOR_HIDDEN}" = "0" ]

  expected_log=$'smcup\ncivis\ncnorm\nrmcup'

  run cat "${log_file}"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${expected_log}" ]
}
