#!/usr/bin/env bash

ALT_SCREEN_ACTIVE=0

enter_alt_screen() {
  if [ -t 1 ] && command_exists tput; then
    tput smcup || true
    tput civis || true
    ALT_SCREEN_ACTIVE=1
  fi
}

leave_alt_screen() {
  if [ "${ALT_SCREEN_ACTIVE}" = "1" ] && command_exists tput; then
    tput cnorm || true
    tput rmcup || true
    ALT_SCREEN_ACTIVE=0
  fi
}
