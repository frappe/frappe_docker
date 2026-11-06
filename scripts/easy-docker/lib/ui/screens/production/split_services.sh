#!/usr/bin/env bash

show_split_services_data_mode_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSplit-services setup (step 1/5)\nApplication Services run the Frappe image, workers, scheduler, and frontend.\nData Services provide the database and Redis layer.\n\nChoose how the data layer should be handled." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 9 \
    --header "Data Services" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Managed Data Services" \
    "External Data Services" \
    "Back to topology selection"
}

show_split_services_database_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSplit-services setup (step 2/5)\nChoose the database engine for the data layer.\nMariaDB is the default choice for most users.\nPostgreSQL is available if that is the database you want to run with this stack." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Data Services: database engine" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "MariaDB (recommended)" \
    "PostgreSQL" \
    "Back to topology selection"
}

show_split_services_redis_mode_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSplit-services setup (step 3/5)\nChoose how Redis should be handled.\nManaged Redis keeps the Redis services inside the generated stack.\nExternal Redis uses endpoints you provide manually.\nChoose no Redis services only if you know you want to handle Redis yourself." "${stack_name}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 9 \
    --header "Redis Services" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Managed Redis Services" \
    "External Redis Services" \
    "No Redis Services" \
    "Back to topology selection"
}

show_split_services_proxy_mode_menu() {
  local stack_dir="${1}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSplit-services setup (step 4/5)\nChoose the reverse proxy mode.\nThe reverse proxy is optional and can stay outside the stack if you already manage it elsewhere." "${stack_name}")"
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

show_split_services_summary_menu() {
  local stack_dir="${1}"
  local data_mode_label="${2}"
  local database_label="${3}"
  local redis_label="${4}"
  local proxy_label="${5}"
  local stack_name=""
  local status_text=""

  render_main_screen 1 >&2

  stack_name="${stack_dir##*/}"
  status_text="$(printf "Stack: %s\n\nSplit-services setup (step 5/5)\nReview the selected layout before the stack files are written.\n\nApplication Services: managed in this stack\nData Services: %s\nDatabase engine: %s\nRedis Services: %s\nReverse Proxy: %s" "${stack_name}" "${data_mode_label}" "${database_label}" "${redis_label}" "${proxy_label}")"
  render_box_message "${status_text}" "0 2" >&2

  gum choose \
    --height 8 \
    --header "Split-services summary" \
    --cursor.foreground 63 \
    --selected.foreground 45 \
    "Yes, write stack files" \
    "Back to topology selection" \
    "Abort wizard to main menu"
}
