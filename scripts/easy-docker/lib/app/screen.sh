#!/usr/bin/env bash

ALT_SCREEN_ACTIVE=0
CURSOR_HIDDEN=0

stdout_is_terminal() {
  [ -t 1 ]
}

run_tput_quietly() {
  tput "$@" 2>/dev/null
}

enter_alt_screen() {
  if ! stdout_is_terminal || ! command_exists tput; then
    return 0
  fi

  if run_tput_quietly smcup; then
    ALT_SCREEN_ACTIVE=1
  fi

  if run_tput_quietly civis; then
    CURSOR_HIDDEN=1
  fi

  return 0
}

leave_alt_screen() {
  if command_exists tput; then
    if [ "${CURSOR_HIDDEN}" = "1" ]; then
      run_tput_quietly cnorm || true
    fi

    if [ "${ALT_SCREEN_ACTIVE}" = "1" ]; then
      run_tput_quietly rmcup || true
    fi
  fi

  CURSOR_HIDDEN=0
  ALT_SCREEN_ACTIVE=0

  return 0
}
