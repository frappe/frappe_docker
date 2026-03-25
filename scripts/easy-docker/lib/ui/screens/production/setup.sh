#!/usr/bin/env bash

get_setup_display_label() {
  local setup_type="${1}"

  case "${setup_type}" in
  development)
    printf 'Development'
    ;;
  production | *)
    printf 'Production'
    ;;
  esac
}

show_setup_menu() {
  local setup_type="${1}"
  local setup_label=""
  local status_text=""

  render_main_screen 1 >&2

  setup_label="$(get_setup_display_label "${setup_type}")"
  status_text="$(printf "%s stack\n\nChoose whether to create a new stack or manage an existing one." "${setup_label}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "${setup_label} stack actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Create new stack" \
    "Manage existing stacks" \
    "Back" \
    "Exit and close easy-docker"
}

show_production_setup_menu() {
  show_setup_menu "production"
}

show_development_setup_menu() {
  show_setup_menu "development"
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

show_frappe_version_profile_menu() {
  local stack_name="${1}"
  local options_lines="${2:-}"
  local selected_label="${3:-}"
  local status_text=""
  local option_line=""
  local -a menu_options=()
  local -a gum_args=()

  render_main_screen 1 >&2

  status_text="$(printf "Create stack: %s\n\nSelect the Frappe branch profile from frappe.tsv.\nThis sets the stack default for branch suggestions." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  while IFS= read -r option_line; do
    if [ -z "${option_line}" ]; then
      continue
    fi
    menu_options+=("${option_line}")
  done <<EOF
${options_lines}
EOF

  if [ "${#menu_options[@]}" -eq 0 ]; then
    return 1
  fi

  gum_args=(
    --height 10
    --header "Frappe branch profile"
    --cursor.foreground 63
    --selected.foreground 45
  )
  if [ -n "${selected_label}" ]; then
    gum_args+=(--selected "${selected_label}")
  fi

  gum choose "${gum_args[@]}" "${menu_options[@]}" "Back"
}
