#!/usr/bin/env bash

prompt_tools_apps_catalog_value_with_back() {
  local result_var="${1}"
  local field_label="${2}"
  local help_text="${3}"
  local placeholder="${4:-}"
  local input_value=""
  local input_status=0

  input_value="$(prompt_tools_apps_catalog_input "${field_label}" "${help_text}" "${placeholder}")"
  input_status=$?
  if [ "${input_status}" -ne 0 ]; then
    return "${FLOW_ABORT_INPUT}"
  fi

  input_value="$(printf '%s' "${input_value}" | tr -d '\r\n')"
  case "${input_value}" in
  /back | /BACK | /Back)
    return "${FLOW_ABORT_INPUT}"
    ;;
  esac

  printf -v "${result_var}" "%s" "${input_value}"
  return "${FLOW_CONTINUE}"
}

prompt_tools_apps_default_branch_from_csv_with_back() {
  local result_var="${1}"
  local branches_csv="${2}"
  local selection=""
  local selection_status=0
  local branch=""
  local -a branch_options=()

  IFS=',' read -r -a branch_options <<<"${branches_csv}"
  if [ "${#branch_options[@]}" -eq 0 ]; then
    return 1
  fi

  selection="$(show_tools_apps_default_branch_menu "${branch_options[@]}")"
  selection_status=$?
  if [ "${selection_status}" -ne 0 ]; then
    return "${FLOW_ABORT_INPUT}"
  fi

  case "${selection}" in
  "" | "Back")
    return "${FLOW_ABORT_INPUT}"
    ;;
  esac

  branch="${selection}"
  if ! is_valid_predefined_app_branch "${branch}"; then
    return 1
  fi
  if ! csv_contains_branch "${branches_csv}" "${branch}"; then
    return 1
  fi

  printf -v "${result_var}" "%s" "${branch}"
  return "${FLOW_CONTINUE}"
}

run_add_app_catalog_entry_wizard() {
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_branches_csv=""
  local normalized_branches_csv=""
  local app_default_branch=""
  local input_status=0

  if ! get_predefined_apps_catalog_entries >/dev/null 2>&1; then
    show_warning_and_wait "Could not load scripts/easy-docker/config/apps.tsv. Check format before adding new entries." 3
    return 1
  fi

  while true; do
    if prompt_tools_apps_catalog_value_with_back \
      app_label \
      "App Label" \
      "Display name used in the app selection list." \
      "My Custom App"; then
      :
    else
      input_status=$?
      return "${input_status}"
    fi

    trim_predefined_catalog_field app_label "${app_label}"
    if [ -z "${app_label}" ]; then
      show_warning_and_wait "App label is required." 2
      continue
    fi

    if predefined_app_catalog_has_label "${app_label}"; then
      show_warning_and_wait "App label already exists in apps.tsv: ${app_label}" 2
      continue
    fi

    if ! generate_predefined_app_id_from_label app_id "${app_label}"; then
      show_warning_and_wait "Could not generate a valid app id from label. Use letters/numbers and simple separators." 2
      continue
    fi

    if predefined_app_catalog_has_id "${app_id}"; then
      show_warning_and_wait "Generated app id already exists (${app_id}). Choose a different label." 2
      continue
    fi

    break
  done

  while true; do
    if prompt_tools_apps_catalog_value_with_back \
      app_repo \
      "Repository URL" \
      "Git repository URL for this app." \
      "https://github.com/acme/my-custom-app"; then
      :
    else
      input_status=$?
      return "${input_status}"
    fi

    if ! is_valid_predefined_app_repo "${app_repo}"; then
      show_warning_and_wait "Invalid repository URL. Use https/http/ssh/git formats." 2
      continue
    fi

    break
  done

  while true; do
    if prompt_tools_apps_catalog_value_with_back \
      app_branches_csv \
      "Branches (CSV)" \
      "Comma-separated branches for selection. Example: version-15,version-16,develop" \
      "version-15,version-16,develop"; then
      :
    else
      input_status=$?
      return "${input_status}"
    fi

    if ! normalize_predefined_branches_csv normalized_branches_csv "${app_branches_csv}"; then
      show_warning_and_wait "Invalid branch list. Use a comma-separated list with valid branch names." 2
      continue
    fi

    break
  done

  while true; do
    if prompt_tools_apps_default_branch_from_csv_with_back app_default_branch "${normalized_branches_csv}"; then
      :
    else
      input_status=$?
      if [ "${input_status}" -eq "${FLOW_ABORT_INPUT}" ]; then
        return "${FLOW_ABORT_INPUT}"
      fi
      show_warning_and_wait "Could not select default branch from branch list." 2
      return "${input_status}"
    fi
    break
  done

  if ! append_predefined_app_catalog_entry "${app_id}" "${app_label}" "${app_repo}" "${app_default_branch}" "${normalized_branches_csv}"; then
    show_warning_and_wait "Could not append app entry to scripts/easy-docker/config/apps.tsv." 3
    return 1
  fi

  show_warning_and_wait "App added to apps.tsv: ${app_label} (${app_id})" 2
  return 0
}

handle_tools_flow() {
  local tools_action=""

  while true; do
    tools_action="$(show_tools_menu || true)"

    case "${tools_action}" in
    "Add Apps for App Selection")
      run_add_app_catalog_entry_wizard || true
      ;;
    "Back to main menu" | "")
      return "${FLOW_BACK_TO_MAIN}"
      ;;
    "Exit and close easy-docker")
      return "${FLOW_EXIT_APP}"
      ;;
    *)
      show_warning_and_wait "Unknown tools action: ${tools_action}"
      ;;
    esac
  done
}
