#!/usr/bin/env bash

is_valid_stack_site_name() {
  local site_name="${1}"

  if [ -z "${site_name}" ]; then
    return 1
  fi

  case "${site_name}" in
  *[!A-Za-z0-9._-]*)
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

is_safe_stack_site_cleanup_name() {
  local site_name="${1}"

  if ! is_valid_stack_site_name "${site_name}"; then
    return 1
  fi

  case "${site_name}" in
  "." | ".." | "/" | "")
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

shell_quote_site_command_arg() {
  local raw_value="${1}"

  printf "'%s'" "$(printf '%s' "${raw_value}" | sed "s/'/'\"'\"'/g")"
}

get_stack_primary_site_name_suggestion() {
  local stack_dir="${1}"
  local env_path=""
  local site_domains=""
  local primary_domain=""

  env_path="$(get_stack_env_path "${stack_dir}")"
  site_domains="$(get_env_file_key_value "${env_path}" "SITE_DOMAINS" || true)"
  primary_domain="${site_domains%%,*}"
  primary_domain="${primary_domain%% *}"

  if [ -n "${primary_domain}" ]; then
    printf '%s\n' "${primary_domain}"
    return 0
  fi

  printf '%s.localhost\n' "${stack_dir##*/}"
  return 0
}

get_stack_database_id() {
  local stack_dir="${1}"

  get_metadata_string_field "${stack_dir}/metadata.json" "database_id"
}

get_stack_redis_id() {
  local stack_dir="${1}"

  get_metadata_string_field "${stack_dir}/metadata.json" "redis_id"
}

get_stack_database_root_password() {
  local stack_dir="${1}"
  local env_path=""
  local db_password=""

  env_path="$(get_stack_env_path "${stack_dir}")"
  db_password="$(get_env_file_key_value "${env_path}" "DB_PASSWORD" || true)"
  if [ -z "${db_password}" ]; then
    db_password="123"
  fi

  printf '%s\n' "${db_password}"
  return 0
}

get_stack_database_root_username() {
  local stack_dir="${1}"
  local database_id=""

  database_id="$(get_stack_database_id "${stack_dir}" || true)"
  case "${database_id}" in
  mariadb)
    printf 'root\n'
    return 0
    ;;
  postgres)
    printf 'postgres\n'
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

stack_site_bootstrap_supports_database() {
  local stack_dir="${1}"
  local database_id=""

  database_id="$(get_stack_database_id "${stack_dir}" || true)"
  case "${database_id}" in
  mariadb | postgres)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

stack_supports_single_site_management() {
  local stack_dir="${1}"
  local stack_topology=""

  stack_topology="$(get_stack_topology "${stack_dir}" || true)"
  case "${stack_topology}" in
  single-host)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}
