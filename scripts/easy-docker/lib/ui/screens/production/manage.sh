#!/usr/bin/env bash

show_manage_stacks_menu() {
  local setup_type="${1}"
  shift
  local stack_count="${#}"
  local setup_label=""
  local status_text=""

  render_main_screen 1 >&2

  setup_label="$(get_setup_display_label "${setup_type}")"
  if [ "${stack_count}" -eq 1 ]; then
    status_text="$(printf "Manage existing %s stacks\n\n1 stack found. Select a stack." "${setup_label}")"
  else
    status_text="$(printf "Manage existing %s stacks\n\n%s stacks found. Select a stack." "${setup_label}" "${stack_count}")"
  fi

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 14 \
    --header "Existing stacks" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "$@" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stacks_placeholder() {
  local setup_type="${1}"
  local setup_label=""
  local status_text=""

  render_main_screen 1 >&2

  setup_label="$(get_setup_display_label "${setup_type}")"
  status_text="$(printf "Manage existing %s stacks\n\nNo stacks found in .easy-docker/stacks yet." "${setup_label}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 7 \
    --header "Manage stacks actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_actions_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local stack_runtime_status="${3:-Unknown}"
  local menu_header=""
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack\n\nStack: %s\nDirectory: %s\nRuntime status: %s\n\nChoose an action for this stack." "${stack_name}" "${stack_dir}" "${stack_runtime_status}")"

  render_box_message "${status_text}" "0 2" >&2

  menu_header="$(printf "Stack actions | %s" "${stack_runtime_status}")"

  gum choose \
    --height 10 \
    --header "${menu_header}" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Apps" \
    "Docker" \
    "Site" \
    "Start stack in Docker Compose" \
    "Stop stack in Docker Compose" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_apps_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack apps\n\nStack: %s\nDirectory: %s\n\nChoose an app-related action for this stack." "${stack_name}" "${stack_dir}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Stack apps actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Regenerate apps.json from metadata" \
    "Select apps and branches" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_docker_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack docker\n\nStack: %s\nDirectory: %s\n\nChoose a docker-related action for this stack." "${stack_name}" "${stack_dir}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Stack docker actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Build custom image" \
    "Generate docker compose from env" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_site_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local existing_site_entry="${3:-}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack site\n\nStack: %s\nDirectory: %s\n\nCreate a new site or select an existing site for this stack." "${stack_name}" "${stack_dir}")"
  render_box_message "${status_text}" "0 2" >&2

  if [ -n "${existing_site_entry}" ]; then
    gum choose \
      --height 10 \
      --header "Stack site actions" \
      --cursor.foreground 63 \
      --selected.foreground 45 \
      "Create new site" \
      "${existing_site_entry}" \
      "Back" \
      "Exit and close easy-docker"
    return 0
  fi

  gum choose \
    --height 8 \
    --header "Stack site actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Create new site" \
    "Back" \
    "Exit and close easy-docker"
}

prompt_stack_site_name() {
  local stack_name="${1}"
  local placeholder="${2:-}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack site\n\nStack: %s\n\nEnter the site name for the first site.\nType /back or press Ctrl+C to cancel." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum input \
    --header "Site name" \
    --prompt "site> " \
    --placeholder "${placeholder}"
}

prompt_stack_site_admin_password() {
  local stack_name="${1}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack site\n\nStack: %s\n\nEnter the Administrator password for the new site.\nType /back or press Ctrl+C to cancel." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum input \
    --header "Administrator password" \
    --prompt "password> " \
    --password
}

show_manage_stack_site_details() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local created_at="${4:-}"
  local installed_apps="${5:-None}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage existing site\n\nStack: %s\nDirectory: %s\nSite: %s\nCreated at: %s\nInstalled apps: %s" "${stack_name}" "${stack_dir}" "${site_name}" "${created_at:-n/a}" "${installed_apps}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Site details" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Back" \
    "Exit and close easy-docker"
}

show_missing_custom_image_start_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local image_ref="${3}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Custom image missing\n\nStack: %s\nDirectory: %s\nImage: %s\n\nBuild the custom image now before starting the stack?" "${stack_name}" "${stack_dir}" "${image_ref}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Missing custom image" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Build custom image now" \
    "Back" \
    "Exit and close easy-docker"
}
