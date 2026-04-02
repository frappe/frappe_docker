#!/usr/bin/env bash

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
  local apps_installed_lines="${4:-}"
  local last_action="${5:-}"
  local last_error="${6:-}"
  local error_log_path="${7:-}"
  local created_at="${8:-}"
  local updated_at="${9:-}"
  local last_backup_at="${10:-}"
  local apps_installed_json_array=""

  build_stack_site_apps_installed_json_array apps_installed_json_array "${apps_installed_lines}"

  printf -v "${result_var}" '{\n      "mode": "%s",\n      "name": "%s",\n      "apps_installed": %s,\n      "last_action": "%s",\n      "last_error": "%s",\n      "error_log_path": "%s",\n      "created_at": "%s",\n      "updated_at": "%s",\n      "last_backup_at": "%s"\n    }' \
    "$(json_escape_string "${site_mode}")" \
    "$(json_escape_string "${site_name}")" \
    "${apps_installed_json_array}" \
    "$(json_escape_string "${last_action}")" \
    "$(json_escape_string "${last_error}")" \
    "$(json_escape_string "${error_log_path}")" \
    "$(json_escape_string "${created_at}")" \
    "$(json_escape_string "${updated_at}")" \
    "$(json_escape_string "${last_backup_at}")"
}

persist_stack_site_metadata() {
  local stack_dir="${1}"
  local site_mode="${2:-single-site}"
  local site_name="${3:-}"
  local apps_installed_lines="${4:-}"
  local last_action="${5:-}"
  local last_error="${6:-}"
  local error_log_path="${7:-}"
  local created_at="${8:-}"
  local updated_at="${9:-}"
  local last_backup_at="${10-__KEEP_CURRENT__}"
  local metadata_path=""
  local metadata_tmp_path=""
  local site_json_object=""

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ "${last_backup_at}" = "__KEEP_CURRENT__" ]; then
    last_backup_at="$(get_metadata_site_string_field "${metadata_path}" "last_backup_at" || true)"
  fi

  build_stack_site_metadata_json_object site_json_object "${site_mode}" "${site_name}" "${apps_installed_lines}" "${last_action}" "${last_error}" "${error_log_path}" "${created_at}" "${updated_at}" "${last_backup_at}"

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
  persist_stack_site_metadata "${stack_dir}" "single-site" "${site_name}" "${apps_installed_lines}" "${last_action}" "${last_error}" "${error_log_path}" "${created_at}" "${updated_at}"
}

clear_stack_site_metadata() {
  local stack_dir="${1}"
  local updated_at=""

  updated_at="$(get_current_utc_timestamp)"
  persist_stack_site_metadata "${stack_dir}" "single-site" "" "" "delete-site" "" "" "" "${updated_at}" ""
}
