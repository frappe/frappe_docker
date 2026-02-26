#!/usr/bin/env bash

get_terminal_cols() {
  local cols="80"

  if command_exists tput; then
    cols="$(tput cols 2>/dev/null || printf "80")"
  fi

  if ! [[ "${cols}" =~ ^[0-9]+$ ]] || [ "${cols}" -le 0 ]; then
    cols="80"
  fi

  printf '%s\n' "${cols}"
}

get_box_wrap_width() {
  local cols=""
  local width=""

  cols="$(get_terminal_cols)"
  width="$((cols - 16))"

  if [ "${width}" -lt 12 ]; then
    width="12"
  fi

  printf '%s\n' "${width}"
}

wrap_box_text() {
  local raw_text="${1}"
  local wrap_width=""

  wrap_width="$(get_box_wrap_width)"

  if command_exists fold; then
    printf '%s' "${raw_text}" | fold -s -w "${wrap_width}"
    return
  fi

  printf '%s' "${raw_text}"
}

render_box_message() {
  local raw_text="${1}"
  local margin="${2:-0 2}"
  local padding="${3:-0 1}"
  local wrapped_text=""

  wrapped_text="$(wrap_box_text "${raw_text}")"

  gum style \
    --border rounded \
    --border-foreground 63 \
    --padding "${padding}" \
    --margin "${margin}" \
    --foreground 252 \
    "${wrapped_text}"
}

render_main_screen() {
  local clear_screen="${1:-0}"
  local header_text=""

  if [ "${clear_screen}" = "1" ]; then
    clear
  fi

  header_text="$(printf "Easy Frappe Docker\nManage Docker setups quickly and easily")"

  render_box_message "${header_text}" "1 2" "0 1"
}

show_main_menu() {
  gum choose \
    --height 7 \
    --header "Choose an action" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Production setup" \
    "Environment check" \
    "Exit"
}

show_warning_message() {
  local message="${1}"
  gum style --foreground 214 "${message}"
}
