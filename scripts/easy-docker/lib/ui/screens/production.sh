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

show_stack_topology_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack created: %s\nDirectory: %s\n\nChoose the deployment topology.\n\n- Single-host: easiest setup on one server.\n- Split services: separate app and infra stacks for more control." "${stack_name}" "${stack_dir}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Topology" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Single-host (recommended)" \
    "Split services" \
    "Abort wizard to main menu"
}

show_single_host_proxy_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSingle-host setup (step 1/3)\nChoose the proxy mode.\n\n- Traefik and nginx-proxy run inside compose.\n- Caddy is external and uses the no-proxy compose mode." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 11 \
    --header "Single-host: proxy mode" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Traefik (HTTP, built-in proxy)" \
    "Traefik (HTTPS + Let's Encrypt)" \
    "nginx-proxy (HTTP)" \
    "nginx-proxy + acme-companion (HTTPS)" \
    "Caddy (external reverse proxy)" \
    "No reverse proxy (direct :8080)" \
    "Back to topology selection"
}

show_single_host_database_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSingle-host setup (step 2/3)\nChoose the database service." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Single-host: database" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "MariaDB (recommended)" \
    "PostgreSQL" \
    "Back to topology selection"
}

show_single_host_redis_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSingle-host setup (step 3/3)\nChoose whether Redis services should be included." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Single-host: redis" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Include Redis (recommended)" \
    "Skip Redis (experienced users only)" \
    "Back to topology selection"
}

show_custom_modular_apps_multi_select() {
  local stack_dir="${1}"
  local options_lines="${2:-}"
  local selected_labels_csv="${3:-}"
  local stack_name=""
  local status_text=""
  local option_line=""
  local -a menu_options=()
  local -a gum_args=()

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nApps\nUse Space to toggle apps from apps.tsv. Press Enter to continue to branch selection per app.\nUse Ctrl+C to go back." "${stack_name}")"
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
    --no-limit
    --height 14
    --header "Apps"
    --cursor.foreground 63
    --selected.foreground 45
  )
  if [ -n "${selected_labels_csv}" ]; then
    gum_args+=(--selected "${selected_labels_csv}")
  fi

  gum choose "${gum_args[@]}" "${menu_options[@]}"
}

prompt_single_host_env_value() {
  local stack_dir="${1}"
  local variable_name="${2}"
  local guidance_text="${3}"
  local placeholder="${4:-}"
  local render_context="${5:-1}"
  local input_feedback="${6:-}"
  local stack_name=""
  local status_text=""

  if [ "${render_context}" = "1" ]; then
    render_main_screen 1 >&2

    stack_name="${stack_dir##*/}"
    guidance_text="${guidance_text//\\n/$'\n'}"
    status_text="$(printf "Stack: %s\n\nConfigure %s\n\n%s" "${stack_name}" "${variable_name}" "${guidance_text}")"
    render_box_message "${status_text}" "0 2" >&2
  fi

  if [ -n "${input_feedback}" ]; then
    gum style --foreground 214 "${input_feedback}" >&2
  fi

  gum input \
    --header "${variable_name}" \
    --prompt "value> " \
    --placeholder "${placeholder}"
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
  local status_text=""

  render_main_screen 1 >&2

  status_text="$(printf "Manage stack\n\nStack: %s\nDirectory: %s\n\nChoose an action for this stack." "${stack_name}" "${stack_dir}")"

  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 7 \
    --header "Stack actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Apps" \
    "Docker" \
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
    "Generate apps.json" \
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
    --height 7 \
    --header "Stack docker actions" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Generate docker compose from env" \
    "Back" \
    "Exit and close easy-docker"
}
