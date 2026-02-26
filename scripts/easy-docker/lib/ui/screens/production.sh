#!/usr/bin/env bash

show_production_setup_menu() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Production setup\n\nChoose whether to create a new stack or manage an existing one.")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Production setup actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Create new stack" \
    "Manage existing stacks" \
    "Back to main menu" \
    "Exit and close easy-docker"
}

prompt_new_stack_name() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Create new stack\n\nEnter a stack name.\nType /cancel or press Ctrl+C to abort.")"

  render_box_message "${status_text}" "0 2" >&2

  gum input \
    --header "Stack name (/cancel to abort)" \
    --prompt "name> " \
    --placeholder "my-production-stack"
}

show_create_stack_created() {
  local stack_name="${1}"
  local env_path="${2}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Create new stack\n\nStack created: %s\nEnv file: %s" "${stack_name}" "${env_path}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 6 \
    --header "Create stack actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Continue stack wizard" \
    "Back to production setup"
}

show_manage_stacks_placeholder() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage existing stacks")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 7 \
    --header "Manage stacks actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Back to production setup" \
    "Back to main menu" \
    "Exit and close easy-docker"
}
