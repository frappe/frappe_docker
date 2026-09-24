#!/usr/bin/env bash

show_stack_topology_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack created: %s\nDirectory: %s\n\nChoose the deployment topology.\n\n- Single-host: easiest setup on one server.\n- Split services: separate application services, data services, and an optional reverse proxy." "${stack_name}" "${stack_dir}")"
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
  status_text="$(printf "Stack: %s\n\nChoose the reverse proxy mode.\n\n- Traefik and nginx-proxy run inside compose.\n- Caddy is external and uses the no-proxy compose mode." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 11 \
    --header "Reverse proxy mode" \
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
  status_text="$(printf "Stack: %s\n\nChoose the database engine." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Database engine" \
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
  status_text="$(printf "Stack: %s\n\nChoose whether Redis services should be included in this stack." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Redis services" \
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
  local selected_label=""
  local -a menu_options=()
  local -a selected_labels=()
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
    IFS=',' read -r -a selected_labels <<<"${selected_labels_csv}"
    for selected_label in "${selected_labels[@]}"; do
      trim_predefined_catalog_field selected_label "${selected_label}"
      if [ -z "${selected_label}" ]; then
        continue
      fi
      gum_args+=(--selected "${selected_label}")
    done
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
