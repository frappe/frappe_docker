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

build_stack_site_apps_installed_json_array() {
  local result_var="${1}"
  local apps_installed_lines="${2:-}"
  local app_name=""
  local escaped_app_name=""
  local entries_json=""

  while IFS= read -r app_name; do
    if [ -z "${app_name}" ]; then
      continue
    fi

    escaped_app_name="$(json_escape_string "${app_name}")"
    if [ -z "${entries_json}" ]; then
      entries_json="$(printf '        "%s"' "${escaped_app_name}")"
    else
      entries_json="${entries_json}"$',\n'"$(printf '        "%s"' "${escaped_app_name}")"
    fi
  done <<EOF
${apps_installed_lines}
EOF

  if [ -z "${entries_json}" ]; then
    printf -v "${result_var}" '[\n      ]'
  else
    printf -v "${result_var}" '[\n%s\n      ]' "${entries_json}"
  fi
}

build_stack_site_metadata_json_object() {
  local result_var="${1}"
  local site_mode="${2:-single-site}"
  local site_name="${3:-}"
  local site_state="${4:-not_created}"
  local apps_installed_lines="${5:-}"
  local last_action="${6:-}"
  local last_error="${7:-}"
  local error_log_path="${8:-}"
  local created_at="${9:-}"
  local updated_at="${10:-}"
  local apps_installed_json_array=""

  build_stack_site_apps_installed_json_array apps_installed_json_array "${apps_installed_lines}"

  printf -v "${result_var}" '{\n      "mode": "%s",\n      "name": "%s",\n      "state": "%s",\n      "apps_installed": %s,\n      "last_action": "%s",\n      "last_error": "%s",\n      "error_log_path": "%s",\n      "created_at": "%s",\n      "updated_at": "%s"\n    }' \
    "$(json_escape_string "${site_mode}")" \
    "$(json_escape_string "${site_name}")" \
    "$(json_escape_string "${site_state}")" \
    "${apps_installed_json_array}" \
    "$(json_escape_string "${last_action}")" \
    "$(json_escape_string "${last_error}")" \
    "$(json_escape_string "${error_log_path}")" \
    "$(json_escape_string "${created_at}")" \
    "$(json_escape_string "${updated_at}")"
}

persist_stack_site_metadata() {
  local stack_dir="${1}"
  local site_mode="${2:-single-site}"
  local site_name="${3:-}"
  local site_state="${4:-not_created}"
  local apps_installed_lines="${5:-}"
  local last_action="${6:-}"
  local last_error="${7:-}"
  local error_log_path="${8:-}"
  local created_at="${9:-}"
  local updated_at="${10:-}"
  local metadata_path=""
  local metadata_tmp_path=""
  local site_json_object=""

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  build_stack_site_metadata_json_object site_json_object "${site_mode}" "${site_name}" "${site_state}" "${apps_installed_lines}" "${last_action}" "${last_error}" "${error_log_path}" "${created_at}" "${updated_at}"

  if ! awk -v site_object="${site_json_object}" '
    BEGIN {
      in_site = 0
      inserted = 0
      site_depth = 0
      prev = ""
    }
    function flush_prev() {
      if (prev != "") {
        print prev
        prev = ""
      }
    }
    {
      if (!in_site && $0 ~ /^  "site"[[:space:]]*:[[:space:]]*{/) {
        in_site = 1
        site_depth = 1
        next
      }

      if (in_site) {
        line = $0
        open_count = gsub(/{/, "{", line)
        close_count = gsub(/}/, "}", line)
        site_depth += open_count - close_count
        if (site_depth <= 0) {
          in_site = 0
        }
        next
      }

      if (!inserted && $0 ~ /^}$/) {
        if (prev != "") {
          if (prev ~ /,$/) {
            print prev
          } else {
            print prev ","
          }
          prev = ""
        }
        print "  \"site\": " site_object
        print "}"
        inserted = 1
        next
      }

      flush_prev()
      prev = $0
    }
    END {
      if (!inserted) {
        if (prev != "") {
          if (prev ~ /,$/) {
            print prev
          } else {
            print prev ","
          }
        }
        print "  \"site\": " site_object
        print "}"
      } else if (prev != "") {
        print prev
      }
    }
  ' "${metadata_path}" >"${metadata_tmp_path}"; then
    rm -f -- "${metadata_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! mv -- "${metadata_tmp_path}" "${metadata_path}"; then
    rm -f -- "${metadata_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  return 0
}

mark_stack_site_failed() {
  local stack_dir="${1}"
  local site_name="${2:-}"
  local apps_installed_lines="${3:-}"
  local last_action="${4:-bootstrap-site}"
  local last_error="${5:-Unknown site bootstrap failure}"
  local error_log_path="${6:-}"
  local created_at="${7:-}"
  local updated_at=""

  updated_at="$(get_current_utc_timestamp)"
  persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "failed" "${apps_installed_lines}" "${last_action}" "${last_error}" "${error_log_path}" "${created_at}" "${updated_at}"
}

clear_stack_site_metadata() {
  local stack_dir="${1}"
  local updated_at=""

  updated_at="$(get_current_utc_timestamp)"
  persist_stack_site_metadata "${stack_dir}" "single-site" "" "not_created" "" "delete-site" "" "" "" "${updated_at}"
}
