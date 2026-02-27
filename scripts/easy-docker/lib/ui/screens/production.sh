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

show_stack_topology_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack created: %s\nDirectory: %s\n\nChoose the deployment topology." "${stack_name}" "${stack_dir}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 9 \
    --header "Topology" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Single-host" \
    "Split services" \
    "Advanced" \
    "Abort wizard to main menu"
}

show_single_host_examples() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Single-host examples\n\n- One server, one compose project.\n- Local DB/Redis/Proxy with app services together.\n- Typical small production VM setup.")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 7 \
    --header "Single-host" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Use this topology" \
    "Back to topology selection"
}

show_split_services_examples() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Split services examples\n\n- DB in a separate stack/project.\n- Proxy in a separate stack/project.\n- One or more app stacks referencing shared infra.")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 7 \
    --header "Split services" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Use this topology" \
    "Back to topology selection"
}

show_advanced_examples() {
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Advanced examples\n\n- Managed external DB/Redis.\n- Multiple benches with custom images/tags.\n- GitOps-style rendered compose and custom networks/secrets.")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 7 \
    --header "Advanced" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Use this topology" \
    "Back to topology selection"
}

show_abort_wizard_prompt() {
  local stack_dir="${1}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Abort wizard\n\nStack directory:\n%s\n\nRollback created files before returning to main menu?" "${stack_dir}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Abort options" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Rollback files and return to main menu" \
    "Keep files and return to main menu" \
    "Back to topology selection"
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
