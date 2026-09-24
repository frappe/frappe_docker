#!/usr/bin/env bash

show_tools_menu() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Tools\n\nManage helper wizards for easy-docker.\nUse this area to maintain the app catalog shown in app selection.")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 9 \
    --header "Tools - App Catalog Utilities" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Add Apps for App Selection" \
    "Back to main menu" \
    "Exit and close easy-docker"
}

prompt_tools_apps_catalog_input() {
  local field_label="${1}"
  local help_text="${2}"
  local placeholder="${3:-}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Tools\n\nAdd Apps for App Selection\nThis wizard updates scripts/easy-docker/config/apps.tsv used by app selection.\n\n%s\nType /back or press Ctrl+C to cancel." "${help_text}")"
  render_box_message "${status_text}" "0 2" >&2

  gum input \
    --header "${field_label}" \
    --prompt "value> " \
    --placeholder "${placeholder}"
}

show_tools_apps_default_branch_menu() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Tools\n\nAdd Apps for App Selection\nSelect the default branch from the configured branch list.\nUse Ctrl+C or choose Back to return.")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 14 \
    --header "Default Branch - Choose from List" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "$@" \
    "Back"
}
