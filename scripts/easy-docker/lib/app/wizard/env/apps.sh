#!/usr/bin/env bash

csv_contains_value() {
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

append_csv_unique() {
  local result_var="${1}"
  local csv_values="${2}"
  local value="${3}"
  local updated_csv="${csv_values}"

  if [ -z "${value}" ]; then
    printf -v "${result_var}" "%s" "${updated_csv}"
    return 0
  fi

  if csv_contains_value "${updated_csv}" "${value}"; then
    printf -v "${result_var}" "%s" "${updated_csv}"
    return 0
  fi

  if [ -z "${updated_csv}" ]; then
    updated_csv="${value}"
  else
    updated_csv="${updated_csv},${value}"
  fi

  printf -v "${result_var}" "%s" "${updated_csv}"
}

lines_contains_line() {
  local lines="${1}"
  local target_line="${2}"
  local line=""

  while IFS= read -r line; do
    if [ -z "${line}" ]; then
      continue
    fi
    if [ "${line}" = "${target_line}" ]; then
      return 0
    fi
  done <<EOF
${lines}
EOF

  return 1
}

append_line_unique() {
  local result_var="${1}"
  local lines="${2}"
  local new_line="${3}"

  if [ -z "${new_line}" ]; then
    printf -v "${result_var}" "%s" "${lines}"
    return 0
  fi

  if lines_contains_line "${lines}" "${new_line}"; then
    printf -v "${result_var}" "%s" "${lines}"
    return 0
  fi

  if [ -z "${lines}" ]; then
    printf -v "${result_var}" "%s" "${new_line}"
  else
    printf -v "${result_var}" "%s\n%s" "${lines}" "${new_line}"
  fi
}

build_predefined_apps_metadata_json_object() {
  local result_var="${1}"
  local predefined_csv="${2}"
  local branch_lines="${3}"
  local app_id=""
  local app_branch=""
  local predefined_json_entries=""
  local branch_json_entries=""
  local escaped_app_id=""
  local escaped_branch=""
  local entry_json=""
  local line=""
  local -a predefined_ids=()

  if [ -n "${predefined_csv}" ]; then
    IFS=',' read -r -a predefined_ids <<<"${predefined_csv}"
    for app_id in "${predefined_ids[@]}"; do
      if [ -z "${app_id}" ]; then
        continue
      fi

      escaped_app_id="$(json_escape_string "${app_id}")"
      entry_json="$(printf '        "%s"' "${escaped_app_id}")"
      if [ -z "${predefined_json_entries}" ]; then
        predefined_json_entries="${entry_json}"
      else
        predefined_json_entries="${predefined_json_entries}"$',\n'"${entry_json}"
      fi
    done
  fi

  while IFS= read -r line; do
    if [ -z "${line}" ]; then
      continue
    fi

    app_id="${line%%|*}"
    app_branch="${line#*|}"
    if [ -z "${app_id}" ] || [ -z "${app_branch}" ]; then
      continue
    fi

    escaped_app_id="$(json_escape_string "${app_id}")"
    escaped_branch="$(json_escape_string "${app_branch}")"
    entry_json="$(printf '        "%s": "%s"' "${escaped_app_id}" "${escaped_branch}")"
    if [ -z "${branch_json_entries}" ]; then
      branch_json_entries="${entry_json}"
    else
      branch_json_entries="${branch_json_entries}"$',\n'"${entry_json}"
    fi
  done <<EOF
${branch_lines}
EOF

  printf -v "${result_var}" '{\n      "predefined": [\n%s\n      ],\n      "predefined_branches": {\n%s\n      },\n      "custom": [\n      ]\n    }' "${predefined_json_entries}" "${branch_json_entries}"
}

get_predefined_branch_from_lines() {
  local lines="${1}"
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
  done <<EOF
${lines}
EOF

  return 1
}

choose_predefined_app_branch() {
  local result_var="${1}"
  local stack_dir="${2}"
  local app_id="${3}"
  local app_label="${4}"
  local repo_url="${5}"
  local preferred_branch="${6:-}"
  local branches_lines=""
  local branch=""
  local status_text=""
  local selection=""
  local default_hint=""
  local -a branch_options=()

  if ! get_predefined_app_branch_lines_by_id branches_lines "${app_id}"; then
    show_warning_and_wait "No branch list configured for ${app_label} (${app_id}) in apps.tsv." 3
    return 1
  fi

  while IFS= read -r branch; do
    if [ -z "${branch}" ]; then
      continue
    fi
    branch_options+=("${branch}")
  done <<EOF
${branches_lines}
EOF

  if [ "${#branch_options[@]}" -eq 0 ]; then
    show_warning_and_wait "No branches available for ${app_label} (${repo_url})." 3
    return 1
  fi

  if [ -n "${preferred_branch}" ]; then
    default_hint="$(printf "Suggested default: %s" "${preferred_branch}")"
  fi

  render_main_screen 1 >&2
  status_text="$(printf "Stack: %s\n\nSelect branch for %s (%s)\nRepo: %s\n%s" "${stack_dir##*/}" "${app_label}" "${app_id}" "${repo_url}" "${default_hint}")"
  render_box_message "${status_text}" "0 2" >&2

  if selection="$(
    gum choose \
      --height 16 \
      --header "Branch selection (${app_label})" \
      --cursor.foreground 63 \
      --selected.foreground 45 \
      "${branch_options[@]}" \
      "Back to app selection"
  )"; then
    :
  else
    return 2
  fi

  case "${selection}" in
  "Back to app selection" | "")
    return 2
    ;;
  *)
    printf -v "${result_var}" "%s" "${selection}"
    return 0
    ;;
  esac
}

prompt_custom_modular_apps_data() {
  local result_apps_metadata_var="${1}"
  local stack_dir="${2}"
  local metadata_path=""
  local options_lines=""
  local selected_labels_csv=""
  local selection_raw=""
  local prompt_status=0
  local selected_predefined_csv=""
  local parsed_predefined_csv=""
  local selected_label=""
  local predefined_app_id=""
  local predefined_app_label=""
  local predefined_repo_url=""
  local selected_branch=""
  local preferred_branch=""
  local available_branch_lines=""
  local existing_branch_lines=""
  local selected_branch_lines=""
  local selected_app_count=0
  local built_apps_metadata_json_object=""
  local -a predefined_catalog_entries=()
  local -a selected_predefined_ids=()

  metadata_path="${stack_dir}/metadata.json"
  if [ -f "${metadata_path}" ]; then
    selected_predefined_csv="$(get_metadata_apps_predefined_csv "${metadata_path}" || true)"
    existing_branch_lines="$(get_metadata_apps_predefined_branch_lines "${metadata_path}" || true)"
  fi

  while true; do
    options_lines=""
    selected_labels_csv=""
    predefined_catalog_entries=()

    mapfile -t predefined_catalog_entries < <(get_predefined_apps_catalog_entries || true)
    for selected_label in "${predefined_catalog_entries[@]}"; do
      IFS='|' read -r predefined_app_id predefined_app_label predefined_repo_url _ _ <<<"${selected_label}"
      if [ -z "${predefined_app_id}" ] || [ -z "${predefined_app_label}" ]; then
        continue
      fi

      if [ -z "${options_lines}" ]; then
        options_lines="$(printf '%s' "${predefined_app_label}")"
      else
        options_lines="$(printf '%s\n%s' "${options_lines}" "${predefined_app_label}")"
      fi
    done

    if [ -n "${selected_predefined_csv}" ]; then
      IFS=',' read -r -a selected_predefined_ids <<<"${selected_predefined_csv}"
      for predefined_app_id in "${selected_predefined_ids[@]}"; do
        if [ -z "${predefined_app_id}" ]; then
          continue
        fi
        predefined_app_label="$(get_predefined_app_label_by_id "${predefined_app_id}" || true)"
        if [ -z "${predefined_app_label}" ]; then
          continue
        fi
        append_csv_unique selected_labels_csv "${selected_labels_csv}" "${predefined_app_label}"
      done
    fi

    if [ -z "${options_lines}" ]; then
      show_warning_and_wait "No apps available in catalog." 3
      return 1
    fi

    if selection_raw="$(show_custom_modular_apps_multi_select "${stack_dir}" "${options_lines}" "${selected_labels_csv}")"; then
      prompt_status=0
    else
      prompt_status=$?
    fi
    if [ "${prompt_status}" -ne 0 ]; then
      return 2
    fi

    if [ -z "${selection_raw}" ]; then
      show_warning_message "Select at least one app."
      continue
    fi

    parsed_predefined_csv=""

    while IFS= read -r selected_label; do
      if [ -z "${selected_label}" ]; then
        continue
      fi

      predefined_app_id="$(get_predefined_app_id_by_label "${selected_label}" || true)"
      if [ -z "${predefined_app_id}" ]; then
        continue
      fi
      append_csv_unique parsed_predefined_csv "${parsed_predefined_csv}" "${predefined_app_id}"
    done <<EOF
${selection_raw}
EOF

    selected_predefined_csv="${parsed_predefined_csv}"

    if [ -z "${selected_predefined_csv}" ]; then
      show_warning_message "Select at least one app."
      continue
    fi

    selected_branch_lines=""
    selected_app_count=0
    IFS=',' read -r -a selected_predefined_ids <<<"${selected_predefined_csv}"
    for predefined_app_id in "${selected_predefined_ids[@]}"; do
      if [ -z "${predefined_app_id}" ]; then
        continue
      fi

      predefined_app_label="$(get_predefined_app_label_by_id "${predefined_app_id}" || true)"
      if [ -z "${predefined_app_label}" ]; then
        predefined_app_label="${predefined_app_id}"
      fi
      predefined_repo_url="$(get_predefined_app_repo_by_id "${predefined_app_id}" || true)"
      if [ -z "${predefined_repo_url}" ]; then
        show_warning_and_wait "Missing repo URL for app '${predefined_app_id}'." 3
        continue 2
      fi

      preferred_branch="$(get_predefined_branch_from_lines "${existing_branch_lines}" "${predefined_app_id}" || true)"
      if [ -z "${preferred_branch}" ]; then
        preferred_branch="$(get_stack_frappe_branch "${stack_dir}" || true)"
      fi
      if [ -z "${preferred_branch}" ]; then
        preferred_branch="$(get_predefined_app_default_branch_by_id "${predefined_app_id}" || true)"
      fi
      if [ -z "${preferred_branch}" ]; then
        preferred_branch="$(get_default_frappe_branch)"
      fi

      available_branch_lines=""
      if get_predefined_app_branch_lines_by_id available_branch_lines "${predefined_app_id}"; then
        if [ -n "${preferred_branch}" ] && ! lines_contains_line "${available_branch_lines}" "${preferred_branch}"; then
          preferred_branch="$(get_predefined_app_default_branch_by_id "${predefined_app_id}" || true)"
        fi
      fi

      if choose_predefined_app_branch selected_branch "${stack_dir}" "${predefined_app_id}" "${predefined_app_label}" "${predefined_repo_url}" "${preferred_branch}"; then
        :
      else
        prompt_status=$?
        if [ "${prompt_status}" -eq 2 ]; then
          continue 2
        fi
        continue 2
      fi

      append_line_unique selected_branch_lines "${selected_branch_lines}" "${predefined_app_id}|${selected_branch}"
      selected_app_count=$((selected_app_count + 1))
    done

    if [ "${selected_app_count}" -eq 0 ]; then
      show_warning_message "No valid apps selected."
      continue
    fi

    build_predefined_apps_metadata_json_object built_apps_metadata_json_object "${selected_predefined_csv}" "${selected_branch_lines}"
    printf -v "${result_apps_metadata_var}" "%s" "${built_apps_metadata_json_object}"
    return 0
  done
}

update_stack_custom_modular_apps() {
  local stack_dir="${1}"
  local metadata_path=""
  local apps_metadata_json_object=""
  local prompt_status=0

  metadata_path="${stack_dir}/metadata.json"
  if [ ! -f "${metadata_path}" ]; then
    return 3
  fi

  if prompt_custom_modular_apps_data apps_metadata_json_object "${stack_dir}"; then
    :
  else
    prompt_status=$?
    return "${prompt_status}"
  fi

  if [ -z "${apps_metadata_json_object}" ]; then
    return 1
  fi

  if ! persist_stack_metadata_apps_object "${stack_dir}" "${apps_metadata_json_object}"; then
    return 1
  fi

  if ! persist_stack_apps_json_from_metadata_apps "${stack_dir}"; then
    return 1
  fi

  return 0
}
