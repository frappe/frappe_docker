#!/usr/bin/env bash

is_valid_git_repo_source() {
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

is_valid_git_branch_name() {
  local value="${1}"

  if [ -z "${value}" ]; then
    return 1
  fi

  if [[ "${value}" =~ [[:space:]] ]]; then
    return 1
  fi

  case "${value}" in
  -* | *..* | *~* | *^* | *:* | *\?* | *\[* | *\\* | */ | /* | *.)
    return 1
    ;;
  esac

  if [[ "${value}" == *"@{"* ]]; then
    return 1
  fi

  return 0
}

get_predefined_app_repo_url() {
  local app_name="${1}"

  case "${app_name}" in
  erpnext)
    printf 'https://github.com/frappe/erpnext\n'
    ;;
  crm)
    printf 'https://github.com/frappe/crm\n'
    ;;
  *)
    return 1
    ;;
  esac
}

prompt_custom_git_apps_data() {
  local result_apps_entries_var="${1}"
  local result_metadata_custom_var="${2}"
  local stack_dir="${3}"
  local app_index=1
  local app_count=0
  local repo_value=""
  local branch_value=""
  local repo_feedback=""
  local branch_feedback=""
  local repo_render_context=1
  local branch_render_context=1
  local prompt_status=0
  local escaped_repo=""
  local escaped_branch=""
  local apps_entry=""
  local metadata_entry=""
  local built_apps_entries=""
  local built_metadata_custom_entries=""

  while true; do
    if [ -n "${repo_feedback}" ]; then
      repo_render_context=0
    else
      repo_render_context=1
    fi

    repo_value="$(prompt_single_host_env_value "${stack_dir}" "CUSTOM_APP_${app_index}_REPO" "Enter git repository URL for custom app #${app_index}.\nType /done when finished or /back to return." "https://github.com/frappe/erpnext" "${repo_render_context}" "${repo_feedback}")"
    prompt_status=$?
    repo_feedback=""
    if [ "${prompt_status}" -ne 0 ]; then
      return 2
    fi
    repo_value="$(printf '%s' "${repo_value}" | tr -d '\r\n')"

    case "${repo_value}" in
    /back | /BACK | /Back | /cancel | /CANCEL | /Cancel)
      return 2
      ;;
    /done | /DONE | /Done)
      if [ "${app_count}" -eq 0 ]; then
        repo_feedback="At least one custom app is required when 'Custom Git app(s)' is selected."
        continue
      fi
      break
      ;;
    esac

    if ! is_valid_git_repo_source "${repo_value}"; then
      repo_feedback="Invalid git repository URL for custom app #${app_index}."
      continue
    fi

    branch_feedback=""
    while true; do
      if [ -n "${branch_feedback}" ]; then
        branch_render_context=0
      else
        branch_render_context=1
      fi

      branch_value="$(prompt_single_host_env_value "${stack_dir}" "CUSTOM_APP_${app_index}_BRANCH" "Enter git branch for custom app #${app_index}.\nType /back to return." "main" "${branch_render_context}" "${branch_feedback}")"
      prompt_status=$?
      branch_feedback=""
      if [ "${prompt_status}" -ne 0 ]; then
        return 2
      fi
      branch_value="$(printf '%s' "${branch_value}" | tr -d '\r\n')"

      case "${branch_value}" in
      /back | /BACK | /Back | /cancel | /CANCEL | /Cancel)
        return 2
        ;;
      esac

      if ! is_valid_git_branch_name "${branch_value}"; then
        branch_feedback="Invalid git branch for custom app #${app_index}."
        continue
      fi

      break
    done

    escaped_repo="$(json_escape_string "${repo_value}")"
    escaped_branch="$(json_escape_string "${branch_value}")"
    apps_entry="$(printf '  {"url": "%s", "branch": "%s"}' "${escaped_repo}" "${escaped_branch}")"
    metadata_entry="$(printf '        {"repo": "%s", "branch": "%s"}' "${escaped_repo}" "${escaped_branch}")"

    if [ -z "${built_apps_entries}" ]; then
      built_apps_entries="${apps_entry}"
    else
      built_apps_entries="${built_apps_entries}"$',\n'"${apps_entry}"
    fi

    if [ -z "${built_metadata_custom_entries}" ]; then
      built_metadata_custom_entries="${metadata_entry}"
    else
      built_metadata_custom_entries="${built_metadata_custom_entries}"$',\n'"${metadata_entry}"
    fi

    app_count=$((app_count + 1))
    app_index=$((app_index + 1))
  done

  printf -v "${result_apps_entries_var}" "%s" "${built_apps_entries}"
  printf -v "${result_metadata_custom_var}" "%s" "${built_metadata_custom_entries}"
  return 0
}

prompt_custom_modular_apps_data() {
  local result_apps_metadata_var="${1}"
  local stack_dir="${2}"
  local back_option_label="${3:-Back to topology selection}"
  local selection_raw=""
  local selection=""
  local preset_apps_csv=""
  local has_custom_apps=0
  local prompt_status=0
  local preset_app=""
  local preset_repo_url=""
  local preset_branch=""
  local escaped_url=""
  local escaped_branch=""
  local apps_entry=""
  local metadata_predefined_entry=""
  local custom_apps_entries=""
  local metadata_custom_entries=""
  local apps_entries=""
  local metadata_predefined_entries=""
  local built_apps_metadata_json_object=""
  local -a selections=()
  local -a preset_apps=()

  while true; do
    selection_raw="$(show_custom_modular_apps_multi_select "${stack_dir}" "${back_option_label}" || true)"
    prompt_status=$?
    if [ "${prompt_status}" -ne 0 ]; then
      return 2
    fi

    if [ -z "${selection_raw}" ]; then
      show_warning_message "Select at least one app option."
      continue
    fi

    preset_apps_csv=""
    has_custom_apps=0
    custom_apps_entries=""
    metadata_custom_entries=""
    apps_entries=""
    metadata_predefined_entries=""

    mapfile -t selections <<<"${selection_raw}"
    for selection in "${selections[@]}"; do
      case "${selection}" in
      "ERPNext")
        if [ -z "${preset_apps_csv}" ]; then
          preset_apps_csv="erpnext"
        else
          preset_apps_csv="${preset_apps_csv},erpnext"
        fi
        ;;
      "CRM")
        if [ -z "${preset_apps_csv}" ]; then
          preset_apps_csv="crm"
        else
          preset_apps_csv="${preset_apps_csv},crm"
        fi
        ;;
      "Custom Git app(s)")
        has_custom_apps=1
        ;;
      "${back_option_label}")
        if [ "${#selections[@]}" -eq 1 ]; then
          return 2
        fi
        show_warning_message "Do not combine '${back_option_label}' with app selections."
        preset_apps_csv=""
        has_custom_apps=0
        break
        ;;
      *)
        show_warning_message "Unknown app selection: ${selection}"
        preset_apps_csv=""
        has_custom_apps=0
        break
        ;;
      esac
    done

    if [ -z "${preset_apps_csv}" ] && [ "${has_custom_apps}" -eq 0 ]; then
      show_warning_message "Select at least one app (ERPNext, CRM, or Custom Git app)."
      continue
    fi

    preset_branch="$(get_default_frappe_branch)"
    if [ -n "${preset_apps_csv}" ]; then
      IFS=',' read -r -a preset_apps <<<"${preset_apps_csv}"
      for preset_app in "${preset_apps[@]}"; do
        preset_repo_url="$(get_predefined_app_repo_url "${preset_app}" || true)"
        if [ -z "${preset_repo_url}" ]; then
          continue
        fi

        escaped_url="$(json_escape_string "${preset_repo_url}")"
        escaped_branch="$(json_escape_string "${preset_branch}")"
        apps_entry="$(printf '  {"url": "%s", "branch": "%s"}' "${escaped_url}" "${escaped_branch}")"
        metadata_predefined_entry="$(printf '        "%s"' "${preset_app}")"

        if [ -z "${apps_entries}" ]; then
          apps_entries="${apps_entry}"
        else
          apps_entries="${apps_entries}"$',\n'"${apps_entry}"
        fi

        if [ -z "${metadata_predefined_entries}" ]; then
          metadata_predefined_entries="${metadata_predefined_entry}"
        else
          metadata_predefined_entries="${metadata_predefined_entries}"$',\n'"${metadata_predefined_entry}"
        fi
      done
    fi

    if [ "${has_custom_apps}" -eq 1 ]; then
      if ! prompt_custom_git_apps_data custom_apps_entries metadata_custom_entries "${stack_dir}"; then
        prompt_status=$?
        return "${prompt_status}"
      fi

      if [ -n "${custom_apps_entries}" ]; then
        if [ -z "${apps_entries}" ]; then
          apps_entries="${custom_apps_entries}"
        else
          apps_entries="${apps_entries}"$',\n'"${custom_apps_entries}"
        fi
      fi
    fi

    if [ -z "${apps_entries}" ]; then
      show_warning_message "No apps selected. Please choose at least one app."
      continue
    fi

    built_apps_metadata_json_object="$(printf '{\n      "predefined": [\n%s\n      ],\n      "custom": [\n%s\n      ]\n    }' "${metadata_predefined_entries}" "${metadata_custom_entries}")"

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

  if ! prompt_custom_modular_apps_data apps_metadata_json_object "${stack_dir}" "Back"; then
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
