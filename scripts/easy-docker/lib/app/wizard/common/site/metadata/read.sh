#!/usr/bin/env bash

get_metadata_site_string_field() {
  local metadata_path="${1}"
  local field_name="${2}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  awk -v field_name="${field_name}" '
    /"site"[[:space:]]*:[[:space:]]*{/ {
      in_site = 1
      site_depth = 1
      next
    }
    in_site {
      if (match($0, "\"" field_name "\"[[:space:]]*:[[:space:]]*\"([^\"]*)\"", parts)) {
        print parts[1]
        exit
      }

      line = $0
      open_count = gsub(/{/, "{", line)
      close_count = gsub(/}/, "}", line)
      site_depth += open_count - close_count
      if (site_depth <= 0) {
        exit
      }
    }
  ' "${metadata_path}"
}

get_metadata_site_apps_installed_lines() {
  local metadata_path="${1}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  awk '
    /"site"[[:space:]]*:[[:space:]]*{/ {
      in_site = 1
      site_depth = 1
      next
    }
    in_site && /"apps_installed"[[:space:]]*:[[:space:]]*\[/ {
      in_apps_installed = 1
      next
    }
    in_apps_installed && /\]/ {
      in_apps_installed = 0
      next
    }
    in_apps_installed {
      if (match($0, /"([^"]+)"/, parts)) {
        print parts[1]
      }
    }
    in_site {
      line = $0
      open_count = gsub(/{/, "{", line)
      close_count = gsub(/}/, "}", line)
      site_depth += open_count - close_count
      if (site_depth <= 0) {
        exit
      }
    }
  ' "${metadata_path}"
}

get_stack_site_name() {
  local stack_dir="${1}"

  get_metadata_site_string_field "${stack_dir}/metadata.json" "name"
}

get_stack_site_last_error() {
  local stack_dir="${1}"

  get_metadata_site_string_field "${stack_dir}/metadata.json" "last_error"
}

get_stack_site_created_at() {
  local stack_dir="${1}"

  get_metadata_site_string_field "${stack_dir}/metadata.json" "created_at"
}

get_stack_site_last_backup_at() {
  local stack_dir="${1}"

  get_metadata_site_string_field "${stack_dir}/metadata.json" "last_backup_at"
}

get_stack_site_apps_installed_lines() {
  local stack_dir="${1}"

  get_metadata_site_apps_installed_lines "${stack_dir}/metadata.json"
}

stack_has_site_record() {
  local stack_dir="${1}"
  local site_name=""

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if [ -n "${site_name}" ]; then
    return 0
  fi

  return 1
}

stack_has_site_configured() {
  local stack_dir="${1}"
  local site_name=""
  local last_error=""

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  last_error="$(get_stack_site_last_error "${stack_dir}" || true)"

  if [ -n "${site_name}" ] && [ -z "${last_error}" ]; then
    return 0
  fi

  return 1
}

get_stack_site_menu_entry() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_name=""

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if [ -z "${site_name}" ]; then
    return 1
  fi

  printf -v "${result_var}" "%s" "${site_name}"
  return 0
}
