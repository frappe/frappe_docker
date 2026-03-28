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

get_stack_site_state() {
  local stack_dir="${1}"

  get_metadata_site_string_field "${stack_dir}/metadata.json" "state"
}

get_stack_site_created_at() {
  local stack_dir="${1}"

  get_metadata_site_string_field "${stack_dir}/metadata.json" "created_at"
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
  local site_state=""

  site_state="$(get_stack_site_state "${stack_dir}" || true)"
  case "${site_state}" in
  created | apps_installing | ready)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

get_stack_site_status_label() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_state=""
  local site_name=""
  local site_status_label=""

  site_state="$(get_stack_site_state "${stack_dir}" || true)"
  site_name="$(get_stack_site_name "${stack_dir}" || true)"

  case "${site_state}" in
  "")
    site_status_label="Not configured"
    ;;
  requested)
    site_status_label="Requested"
    ;;
  creating)
    site_status_label="Creating"
    ;;
  created)
    site_status_label="Created"
    ;;
  apps_installing)
    site_status_label="Installing apps"
    ;;
  ready)
    site_status_label="Ready"
    ;;
  failed)
    site_status_label="Failed"
    ;;
  *)
    site_status_label="${site_state}"
    ;;
  esac

  if [ -n "${site_name}" ]; then
    site_status_label="${site_status_label} (${site_name})"
  fi

  printf -v "${result_var}" "%s" "${site_status_label}"
  return 0
}

get_stack_site_menu_entry() {
  local result_var="${1}"
  local stack_dir="${2}"
  local site_name=""
  local site_status_label=""
  local menu_entry=""

  site_name="$(get_stack_site_name "${stack_dir}" || true)"
  if [ -z "${site_name}" ]; then
    return 1
  fi

  get_stack_site_status_label site_status_label "${stack_dir}"
  menu_entry="$(printf "%s | %s" "${site_name}" "${site_status_label}")"
  printf -v "${result_var}" "%s" "${menu_entry}"
  return 0
}
