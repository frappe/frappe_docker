#!/usr/bin/env bash

persist_stack_apps_json_content() {
  local stack_dir="${1}"
  local apps_json_content="${2}"
  local apps_json_path=""
  local apps_json_tmp_path=""

  apps_json_path="${stack_dir}/apps.json"
  apps_json_tmp_path="${apps_json_path}.tmp"

  if ! printf '%s\n' "${apps_json_content}" >"${apps_json_tmp_path}"; then
    rm -f -- "${apps_json_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! mv -- "${apps_json_tmp_path}" "${apps_json_path}"; then
    rm -f -- "${apps_json_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  return 0
}

get_metadata_apps_predefined_csv() {
  local metadata_path="${1}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  awk '
    /"apps"[[:space:]]*:[[:space:]]*{/ {
      in_apps = 1
    }
    in_apps && /"predefined"[[:space:]]*:[[:space:]]*\[/ {
      in_predefined = 1
      next
    }
    in_predefined && /\]/ {
      in_predefined = 0
      next
    }
    in_predefined {
      if (match($0, /"([^"]+)"/, parts)) {
        if (csv == "") {
          csv = parts[1]
        } else {
          csv = csv "," parts[1]
        }
      }
    }
    END {
      if (csv != "") {
        print csv
      }
    }
  ' "${metadata_path}"
}

get_metadata_apps_custom_lines() {
  local metadata_path="${1}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  awk '
    /"apps"[[:space:]]*:[[:space:]]*{/ {
      in_apps = 1
    }
    in_apps && /"custom"[[:space:]]*:[[:space:]]*\[/ {
      in_custom = 1
      next
    }
    in_custom && /\]/ {
      in_custom = 0
      repo = ""
      branch = ""
      next
    }
    in_custom {
      if (match($0, /"repo"[[:space:]]*:[[:space:]]*"([^"]+)"/, repo_parts)) {
        repo = repo_parts[1]
      }
      if (match($0, /"branch"[[:space:]]*:[[:space:]]*"([^"]+)"/, branch_parts)) {
        branch = branch_parts[1]
      }
      if (repo != "" && branch != "") {
        print repo "|" branch
        repo = ""
        branch = ""
      }
    }
  ' "${metadata_path}"
}

build_stack_apps_json_content_from_metadata_apps() {
  local result_var="${1}"
  local stack_dir="${2}"
  local metadata_path=""
  local preset_apps_csv=""
  local custom_apps_lines=""
  local preset_branch=""
  local app=""
  local line=""
  local repo=""
  local branch=""
  local url=""
  local escaped_url=""
  local escaped_branch=""
  local entry_json=""
  local entries_json=""
  local -a preset_apps=()

  metadata_path="${stack_dir}/metadata.json"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  preset_apps_csv="$(get_metadata_apps_predefined_csv "${metadata_path}" || true)"
  custom_apps_lines="$(get_metadata_apps_custom_lines "${metadata_path}" || true)"
  preset_branch="$(get_default_frappe_branch)"

  if [ -n "${preset_apps_csv}" ]; then
    IFS=',' read -r -a preset_apps <<<"${preset_apps_csv}"
    for app in "${preset_apps[@]}"; do
      case "${app}" in
      erpnext)
        url="https://github.com/frappe/erpnext"
        ;;
      crm)
        url="https://github.com/frappe/crm"
        ;;
      *)
        continue
        ;;
      esac

      escaped_url="$(json_escape_string "${url}")"
      escaped_branch="$(json_escape_string "${preset_branch}")"
      entry_json="$(printf '  {"url": "%s", "branch": "%s"}' "${escaped_url}" "${escaped_branch}")"
      if [ -z "${entries_json}" ]; then
        entries_json="${entry_json}"
      else
        entries_json="${entries_json}"$',\n'"${entry_json}"
      fi
    done
  fi

  while IFS= read -r line; do
    if [ -z "${line}" ]; then
      continue
    fi

    repo="${line%%|*}"
    branch="${line#*|}"
    if [ -z "${repo}" ] || [ -z "${branch}" ]; then
      continue
    fi

    escaped_url="$(json_escape_string "${repo}")"
    escaped_branch="$(json_escape_string "${branch}")"
    entry_json="$(printf '  {"url": "%s", "branch": "%s"}' "${escaped_url}" "${escaped_branch}")"
    if [ -z "${entries_json}" ]; then
      entries_json="${entry_json}"
    else
      entries_json="${entries_json}"$',\n'"${entry_json}"
    fi
  done <<EOF
${custom_apps_lines}
EOF

  if [ -z "${entries_json}" ]; then
    printf -v "${result_var}" "[\n]\n"
  else
    printf -v "${result_var}" "[\n%s\n]\n" "${entries_json}"
  fi

  return 0
}

persist_stack_apps_json_from_metadata_apps() {
  local stack_dir="${1}"
  local apps_json_content=""

  if ! build_stack_apps_json_content_from_metadata_apps apps_json_content "${stack_dir}"; then
    return 1
  fi

  if ! persist_stack_apps_json_content "${stack_dir}" "${apps_json_content}"; then
    return 1
  fi

  return 0
}

persist_stack_metadata_apps_object() {
  local stack_dir="${1}"
  local apps_json_object="${2}"
  local metadata_path=""
  local metadata_tmp_path=""

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ -z "${apps_json_object}" ]; then
    return 1
  fi

  if ! awk -v apps_object="${apps_json_object}" '
    BEGIN {
      in_top_level_apps = 0
      apps_depth = 0
      inserted = 0
    }
    {
      if (!in_top_level_apps && $0 ~ /^  "apps"[[:space:]]*:/) {
        print "  \"apps\": " apps_object ","
        in_top_level_apps = 1
        inserted = 1
        if ($0 ~ /{/) {
          apps_depth += gsub(/{/, "{", $0)
          apps_depth -= gsub(/}/, "}", $0)
        } else {
          apps_depth = 0
        }
        if (apps_depth <= 0) {
          in_top_level_apps = 0
        }
        next
      }

      if (in_top_level_apps) {
        apps_depth += gsub(/{/, "{", $0)
        apps_depth -= gsub(/}/, "}", $0)
        if (apps_depth <= 0) {
          in_top_level_apps = 0
        }
        next
      }

      if (!inserted && $0 ~ /^  "wizard"[[:space:]]*:/) {
        print "  \"apps\": " apps_object ","
        inserted = 1
      }

      if (!inserted && $0 ~ /^}/) {
        print "  \"apps\": " apps_object
        inserted = 1
      }

      print
    }
    END {
      if (!inserted) {
        exit 2
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
