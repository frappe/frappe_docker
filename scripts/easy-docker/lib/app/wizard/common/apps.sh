#!/usr/bin/env bash

trim_predefined_catalog_field() {
  local result_var="${1}"
  local value="${2}"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"

  printf -v "${result_var}" "%s" "${value}"
}

is_valid_predefined_app_id() {
  local value="${1}"

  if [ -z "${value}" ]; then
    return 1
  fi

  case "${value}" in
  *[!a-z0-9._-]*)
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

generate_predefined_app_id_from_label() {
  local result_var="${1}"
  local app_label="${2}"
  local generated_id=""

  generated_id="$(
    printf '%s' "${app_label}" |
      tr '[:upper:]' '[:lower:]' |
      sed -E 's/[[:space:]]+/_/g; s/[^a-z0-9._-]+/_/g; s/_+/_/g; s/^_+//; s/_+$//'
  )"

  if ! is_valid_predefined_app_id "${generated_id}"; then
    return 1
  fi

  printf -v "${result_var}" "%s" "${generated_id}"
  return 0
}

is_valid_predefined_app_repo() {
  local value="${1}"

  if [ -z "${value}" ]; then
    return 1
  fi

  case "${value}" in
  https://* | http://* | ssh://* | git://* | git@*:* | file://*)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

is_valid_predefined_app_branch() {
  local value="${1}"

  if [ -z "${value}" ]; then
    return 1
  fi

  case "${value}" in
  *[!A-Za-z0-9._/-]* | .* | *..* | */ | /*)
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

csv_contains_branch() {
  local csv_values="${1}"
  local value="${2}"

  case ",${csv_values}," in
  *,"${value}",*)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

normalize_predefined_branches_csv() {
  local result_csv_var="${1}"
  local branches_csv_raw="${2}"
  local branch_token=""
  local normalized_csv=""
  local -a raw_tokens=()

  IFS=',' read -r -a raw_tokens <<<"${branches_csv_raw}"
  for branch_token in "${raw_tokens[@]}"; do
    trim_predefined_catalog_field branch_token "${branch_token}"
    if [ -z "${branch_token}" ]; then
      continue
    fi

    if ! is_valid_predefined_app_branch "${branch_token}"; then
      return 1
    fi

    if csv_contains_branch "${normalized_csv}" "${branch_token}"; then
      continue
    fi

    if [ -z "${normalized_csv}" ]; then
      normalized_csv="${branch_token}"
    else
      normalized_csv="${normalized_csv},${branch_token}"
    fi
  done

  if [ -z "${normalized_csv}" ]; then
    return 1
  fi

  printf -v "${result_csv_var}" "%s" "${normalized_csv}"
  return 0
}

get_predefined_apps_catalog_path() {
  local repo_root=""

  repo_root="$(get_easy_docker_repo_root)"
  printf '%s/scripts/easy-docker/config/apps.tsv\n' "${repo_root}"
}

get_predefined_apps_catalog_entries() {
  local catalog_path=""
  local raw_line=""
  local line=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""
  local normalized_branches_csv=""
  local first_branch=""
  local extra=""
  local seen_ids=","
  local seen_labels=","

  catalog_path="$(get_predefined_apps_catalog_path)"
  if [ ! -f "${catalog_path}" ]; then
    return 1
  fi

  while IFS= read -r raw_line || [ -n "${raw_line}" ]; do
    trim_predefined_catalog_field line "${raw_line}"
    if [ -z "${line}" ]; then
      continue
    fi

    case "${line}" in
    \#*)
      continue
      ;;
    esac

    if [[ "${line}" == *$'\t'* ]]; then
      IFS=$'\t' read -r app_id app_label app_repo app_default_branch app_branches_csv extra <<<"${line}"
    else
      # Backward compatibility for older catalog rows.
      IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv extra <<<"${line}"
    fi
    trim_predefined_catalog_field app_id "${app_id}"
    trim_predefined_catalog_field app_label "${app_label}"
    trim_predefined_catalog_field app_repo "${app_repo}"
    trim_predefined_catalog_field app_default_branch "${app_default_branch}"
    trim_predefined_catalog_field app_branches_csv "${app_branches_csv}"
    trim_predefined_catalog_field extra "${extra}"

    if [ -n "${extra}" ] || [ -z "${app_id}" ] || [ -z "${app_label}" ] || [ -z "${app_repo}" ] || [ -z "${app_branches_csv}" ]; then
      return 1
    fi

    if ! is_valid_predefined_app_id "${app_id}"; then
      return 1
    fi

    if ! is_valid_predefined_app_repo "${app_repo}"; then
      return 1
    fi

    if ! normalize_predefined_branches_csv normalized_branches_csv "${app_branches_csv}"; then
      return 1
    fi

    if [ -z "${app_default_branch}" ]; then
      first_branch="${normalized_branches_csv%%,*}"
      app_default_branch="${first_branch}"
    fi

    if ! is_valid_predefined_app_branch "${app_default_branch}"; then
      return 1
    fi

    if ! csv_contains_branch "${normalized_branches_csv}" "${app_default_branch}"; then
      return 1
    fi

    case "${seen_ids}" in
    *,"${app_id}",*)
      return 1
      ;;
    esac
    case "${seen_labels}" in
    *,"${app_label}",*)
      return 1
      ;;
    esac

    seen_ids="${seen_ids}${app_id},"
    seen_labels="${seen_labels}${app_label},"

    printf '%s|%s|%s|%s|%s\n' "${app_id}" "${app_label}" "${app_repo}" "${app_default_branch}" "${normalized_branches_csv}"
  done <"${catalog_path}"
}

get_predefined_app_labels_lines() {
  local entry=""
  local app_label=""

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    app_label="${entry#*|}"
    app_label="${app_label%%|*}"
    printf '%s\n' "${app_label}"
  done < <(get_predefined_apps_catalog_entries)
}

get_predefined_app_id_by_label() {
  local label="${1}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv <<<"${entry}"
    if [ "${app_label}" = "${label}" ]; then
      printf '%s\n' "${app_id}"
      return 0
    fi
  done < <(get_predefined_apps_catalog_entries)

  return 1
}

get_predefined_app_repo_by_id() {
  local app_id_lookup="${1}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv <<<"${entry}"
    if [ "${app_id}" = "${app_id_lookup}" ]; then
      printf '%s\n' "${app_repo}"
      return 0
    fi
  done < <(get_predefined_apps_catalog_entries)

  return 1
}

get_predefined_app_label_by_id() {
  local app_id_lookup="${1}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv <<<"${entry}"
    if [ "${app_id}" = "${app_id_lookup}" ]; then
      printf '%s\n' "${app_label}"
      return 0
    fi
  done < <(get_predefined_apps_catalog_entries)

  return 1
}

get_predefined_app_default_branch_by_id() {
  local app_id_lookup="${1}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv <<<"${entry}"
    if [ "${app_id}" = "${app_id_lookup}" ]; then
      printf '%s\n' "${app_default_branch}"
      return 0
    fi
  done < <(get_predefined_apps_catalog_entries)

  return 1
}

get_predefined_app_branch_lines_by_id() {
  local result_var="${1}"
  local app_id_lookup="${2}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""
  local branch=""
  local branch_lines=""
  local -a branches=()

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv <<<"${entry}"
    if [ "${app_id}" != "${app_id_lookup}" ]; then
      continue
    fi

    IFS=',' read -r -a branches <<<"${app_branches_csv}"
    for branch in "${branches[@]}"; do
      trim_predefined_catalog_field branch "${branch}"
      if [ -z "${branch}" ]; then
        continue
      fi
      if [ -z "${branch_lines}" ]; then
        branch_lines="${branch}"
      else
        branch_lines="${branch_lines}"$'\n'"${branch}"
      fi
    done

    if [ -z "${branch_lines}" ]; then
      return 1
    fi

    printf -v "${result_var}" "%s" "${branch_lines}"
    return 0
  done < <(get_predefined_apps_catalog_entries)

  return 1
}

predefined_app_catalog_has_id() {
  local app_id_lookup="${1}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""

  if [ -z "${app_id_lookup}" ]; then
    return 1
  fi

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv <<<"${entry}"
    if [ "${app_id}" = "${app_id_lookup}" ]; then
      return 0
    fi
  done < <(get_predefined_apps_catalog_entries || true)

  return 1
}

predefined_app_catalog_has_label() {
  local app_label_lookup="${1}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""

  if [ -z "${app_label_lookup}" ]; then
    return 1
  fi

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r app_id app_label app_repo app_default_branch app_branches_csv <<<"${entry}"
    if [ "${app_label}" = "${app_label_lookup}" ]; then
      return 0
    fi
  done < <(get_predefined_apps_catalog_entries || true)

  return 1
}

append_predefined_app_catalog_entry() {
  local app_id="${1}"
  local app_label="${2}"
  local app_repo="${3}"
  local app_default_branch="${4}"
  local app_branches_csv="${5}"
  local normalized_branches_csv=""
  local first_branch=""
  local catalog_path=""
  local catalog_tmp_path=""
  local last_char=""

  if ! get_predefined_apps_catalog_entries >/dev/null 2>&1; then
    return 1
  fi

  trim_predefined_catalog_field app_id "${app_id}"
  trim_predefined_catalog_field app_label "${app_label}"
  trim_predefined_catalog_field app_repo "${app_repo}"
  trim_predefined_catalog_field app_default_branch "${app_default_branch}"
  trim_predefined_catalog_field app_branches_csv "${app_branches_csv}"

  if ! is_valid_predefined_app_id "${app_id}"; then
    return 1
  fi
  if [ -z "${app_label}" ]; then
    return 1
  fi
  if ! is_valid_predefined_app_repo "${app_repo}"; then
    return 1
  fi
  if ! normalize_predefined_branches_csv normalized_branches_csv "${app_branches_csv}"; then
    return 1
  fi

  if [ -z "${app_default_branch}" ]; then
    first_branch="${normalized_branches_csv%%,*}"
    app_default_branch="${first_branch}"
  fi
  if ! is_valid_predefined_app_branch "${app_default_branch}"; then
    return 1
  fi
  if ! csv_contains_branch "${normalized_branches_csv}" "${app_default_branch}"; then
    return 1
  fi

  if predefined_app_catalog_has_id "${app_id}"; then
    return 1
  fi
  if predefined_app_catalog_has_label "${app_label}"; then
    return 1
  fi

  catalog_path="$(get_predefined_apps_catalog_path)"
  catalog_tmp_path="${catalog_path}.tmp"
  if [ ! -f "${catalog_path}" ]; then
    return 1
  fi

  if ! cp -- "${catalog_path}" "${catalog_tmp_path}"; then
    rm -f -- "${catalog_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if [ -s "${catalog_tmp_path}" ]; then
    if command_exists tail; then
      last_char="$(tail -c 1 "${catalog_tmp_path}" 2>/dev/null || true)"
      if [ -n "${last_char}" ]; then
        if ! printf '\n' >>"${catalog_tmp_path}"; then
          rm -f -- "${catalog_tmp_path}" >/dev/null 2>&1 || true
          return 1
        fi
      fi
    else
      if ! printf '\n' >>"${catalog_tmp_path}"; then
        rm -f -- "${catalog_tmp_path}" >/dev/null 2>&1 || true
        return 1
      fi
    fi
  fi

  if ! printf '%s\t%s\t%s\t%s\t%s\n' "${app_id}" "${app_label}" "${app_repo}" "${app_default_branch}" "${normalized_branches_csv}" >>"${catalog_tmp_path}"; then
    rm -f -- "${catalog_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! mv -- "${catalog_tmp_path}" "${catalog_path}"; then
    rm -f -- "${catalog_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  return 0
}

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

get_metadata_apps_predefined_branch_lines() {
  local metadata_path="${1}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  awk '
    /"apps"[[:space:]]*:[[:space:]]*{/ {
      in_apps = 1
    }
    in_apps && /"predefined_branches"[[:space:]]*:[[:space:]]*{/ {
      in_predefined_branches = 1
      next
    }
    in_predefined_branches && /}/ {
      in_predefined_branches = 0
      next
    }
    in_predefined_branches {
      if (match($0, /"([^"]+)"[[:space:]]*:[[:space:]]*"([^"]+)"/, parts)) {
        print parts[1] "|" parts[2]
      }
    }
  ' "${metadata_path}"
}

get_metadata_apps_predefined_branch_for_id() {
  local metadata_path="${1}"
  local app_id_lookup="${2}"
  local line=""
  local app_id=""
  local app_branch=""

  while IFS= read -r line; do
    if [ -z "${line}" ]; then
      continue
    fi

    app_id="${line%%|*}"
    app_branch="${line#*|}"
    if [ "${app_id}" = "${app_id_lookup}" ] && [ -n "${app_branch}" ]; then
      printf '%s\n' "${app_branch}"
      return 0
    fi
  done < <(get_metadata_apps_predefined_branch_lines "${metadata_path}" || true)

  return 1
}

build_stack_apps_json_content_from_metadata_apps() {
  local result_var="${1}"
  local stack_dir="${2}"
  local metadata_path=""
  local preset_apps_csv=""
  local custom_apps_lines=""
  local predefined_branch=""
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
  preset_branch="$(get_stack_frappe_branch "${stack_dir}" || true)"
  if [ -z "${preset_branch}" ]; then
    preset_branch="$(get_default_frappe_branch)"
  fi

  if [ -n "${preset_apps_csv}" ]; then
    IFS=',' read -r -a preset_apps <<<"${preset_apps_csv}"
    for app in "${preset_apps[@]}"; do
      url="$(get_predefined_app_repo_by_id "${app}" || true)"
      if [ -z "${url}" ]; then
        return 1
      fi

      predefined_branch="$(get_metadata_apps_predefined_branch_for_id "${metadata_path}" "${app}" || true)"
      if [ -z "${predefined_branch}" ]; then
        predefined_branch="${preset_branch}"
      fi

      escaped_url="$(json_escape_string "${url}")"
      escaped_branch="$(json_escape_string "${predefined_branch}")"
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
      prev = ""
    }
    function flush_prev() {
      if (prev != "") {
        print prev
        prev = ""
      }
    }
    {
      if (!in_top_level_apps && $0 ~ /^  "apps"[[:space:]]*:/) {
        flush_prev()
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
        flush_prev()
        print "  \"apps\": " apps_object ","
        inserted = 1
      }

      if (!inserted && $0 ~ /^}/) {
        if (prev != "") {
          if (prev !~ /,[[:space:]]*$/) {
            prev = prev ","
          }
          print prev
          prev = ""
        }
        print "  \"apps\": " apps_object
        inserted = 1
        print $0
        next
      }

      flush_prev()
      prev = $0
    }
    END {
      flush_prev()
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

persist_stack_metadata_wizard_object() {
  local stack_dir="${1}"
  local wizard_json_object="${2}"
  local metadata_path=""
  local metadata_tmp_path=""

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ -z "${wizard_json_object}" ]; then
    return 1
  fi

  if ! awk -v wizard_object="${wizard_json_object}" '
    BEGIN {
      in_top_level_wizard = 0
      wizard_depth = 0
      inserted = 0
      prev = ""
    }
    function flush_prev() {
      if (prev != "") {
        print prev
        prev = ""
      }
    }
    {
      if (!in_top_level_wizard && $0 ~ /^  "wizard"[[:space:]]*:/) {
        flush_prev()
        print "  \"wizard\": " wizard_object
        in_top_level_wizard = 1
        inserted = 1
        if ($0 ~ /{/) {
          wizard_depth += gsub(/{/, "{", $0)
          wizard_depth -= gsub(/}/, "}", $0)
        } else {
          wizard_depth = 0
        }
        if (wizard_depth <= 0) {
          in_top_level_wizard = 0
        }
        next
      }

      if (in_top_level_wizard) {
        wizard_depth += gsub(/{/, "{", $0)
        wizard_depth -= gsub(/}/, "}", $0)
        if (wizard_depth <= 0) {
          in_top_level_wizard = 0
        }
        next
      }

      if (!inserted && $0 ~ /^}/) {
        if (prev != "") {
          if (prev !~ /,[[:space:]]*$/) {
            prev = prev ","
          }
          print prev
          prev = ""
        }
        print "  \"wizard\": " wizard_object
        inserted = 1
        print $0
        next
      }

      flush_prev()
      prev = $0
    }
    END {
      flush_prev()
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
