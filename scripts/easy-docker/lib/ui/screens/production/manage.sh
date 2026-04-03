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
    --height 12 \
    --header "${menu_header}" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Apps" \
    "Updates" \
    "Site" \
    "Start stack in Docker Compose" \
    "Restart stack in Docker Compose" \
    "Stop stack in Docker Compose" \
    "Delete stack" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_apps_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local frappe_branch="${3:-n/a}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack apps\n\nStack: %s\nDirectory: %s\nFrappe branch: %s\n\nChoose an app-related action for this stack." "${stack_name}" "${stack_dir}" "${frappe_branch}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Stack apps actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Select apps and branches" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_updates_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local frappe_branch="${3:-n/a}"
  local custom_image_ref="${4:-n/a}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack updates\n\nStack: %s\nDirectory: %s\nFrappe branch: %s\nCustom image: %s\n\nChoose an update-related action for this stack." "${stack_name}" "${stack_dir}" "${frappe_branch}" "${custom_image_ref}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 9 \
    --header "Stack update actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Update selected app branches" \
    "Set next custom image tag" \
    "Build updated image" \
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
  local last_backup_at="${6:-}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage existing site\n\nStack: %s\nDirectory: %s\nSite: %s\nCreated at: %s\nInstalled apps: %s\nLast backup: %s" "${stack_name}" "${stack_dir}" "${site_name}" "${created_at:-n/a}" "${installed_apps}" "${last_backup_at:-n/a}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 10 \
    --header "Site details" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Manage apps on this site" \
    "Migrate site now" \
    "Backup site now" \
    "Delete site" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_site_apps_menu() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage site apps\n\nStack: %s\nDirectory: %s\nSite: %s\n\nInstall or uninstall apps for this existing site." "${stack_name}" "${stack_dir}" "${site_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 9 \
    --header "Site app actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Install app on this site" \
    "Uninstall app from this site" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_site_app_selection() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local action_label="${4}"
  local app_lines="${5:-}"
  local status_text=""
  local app_name=""
  local -a menu_options=()

  render_main_screen 1 >&2

  status_text="$(printf "%s\n\nStack: %s\nDirectory: %s\nSite: %s\n\nSelect one app." "${action_label}" "${stack_name}" "${stack_dir}" "${site_name}")"
  render_box_message "${status_text}" "0 2" >&2

  while IFS= read -r app_name; do
    if [ -z "${app_name}" ]; then
      continue
    fi
    menu_options+=("${app_name}")
  done <<EOF
${app_lines}
EOF

  if [ "${#menu_options[@]}" -eq 0 ]; then
    return 1
  fi

  gum choose \
    --height 12 \
    --header "${action_label}" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "${menu_options[@]}" \
    "Back" \
    "Exit and close easy-docker"
}

show_manage_stack_site_app_uninstall_confirmation() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local app_name="${4}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Uninstall app from site\n\nStack: %s\nDirectory: %s\nSite: %s\nApp: %s\n\nThis removes the app from the site. frappe itself cannot be removed here." "${stack_name}" "${stack_dir}" "${site_name}" "${app_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Confirm uninstall app" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Yes" \
    "No" \
    "Exit and close easy-docker"
}

show_manage_stack_site_migrate_confirmation() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Migrate site\n\nStack: %s\nDirectory: %s\nSite: %s\n\nRun bench migrate for this existing site now?" "${stack_name}" "${stack_dir}" "${site_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Confirm migrate site" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Yes" \
    "No" \
    "Exit and close easy-docker"
}

show_manage_stack_site_delete_confirmation() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local site_name="${3}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Delete site\n\nStack: %s\nDirectory: %s\nSite: %s\n\nAll site data and the site database will be permanently deleted." "${stack_name}" "${stack_dir}" "${site_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Confirm delete site" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Yes" \
    "No" \
    "Exit and close easy-docker"
}

show_manage_stack_delete_confirmation() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Delete stack\n\nStack: %s\nDirectory: %s\n\nThis will permanently remove the stack directory, Docker containers, networks, volumes, and configured custom image." "${stack_name}" "${stack_dir}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Confirm delete stack" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Yes" \
    "No" \
    "Exit and close easy-docker"
}

prompt_manage_stack_delete_keyword() {
  local stack_name="${1}"
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Delete stack\n\nStack: %s\n\nFinal confirmation required.\nType delete to permanently remove the stack and all its data.\nType /back or press Ctrl+C to cancel." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum input \
    --header "Type delete to confirm" \
    --prompt "confirm> " \
    --placeholder "delete"
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
