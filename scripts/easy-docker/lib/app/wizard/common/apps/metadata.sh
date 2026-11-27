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

  if ! easy_docker_require_jq; then
    return 1
  fi

  easy_docker_run_jq -r '(.apps.predefined // []) | join(",")' "${metadata_path}"
}

get_metadata_apps_custom_lines() {
  local metadata_path="${1}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if ! easy_docker_require_jq; then
    return 1
  fi

  easy_docker_run_jq -r '(.apps.custom // [])[]? | select(has("repo") and has("branch")) | "\(.repo)|\(.branch)"' "${metadata_path}"
}

get_metadata_apps_predefined_branch_lines() {
  local metadata_path="${1}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if ! easy_docker_require_jq; then
    return 1
  fi

  easy_docker_run_jq -r '(.apps.predefined_branches // {}) | to_entries[]? | "\(.key)|\(.value)"' "${metadata_path}"
}

get_metadata_apps_predefined_branch_for_id() {
  local metadata_path="${1}"
  local app_id_lookup="${2}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if ! easy_docker_require_jq; then
    return 1
  fi

  # shellcheck disable=SC2016
  easy_docker_run_jq -r --arg app_id "${app_id_lookup}" '.apps.predefined_branches[$app_id] // empty' "${metadata_path}"
}

build_metadata_apps_json_object() {
  local result_var="${1}"
  local predefined_csv="${2}"
  local branch_lines="${3}"
  local custom_apps_lines="${4:-}"
  local app_id=""
  local app_branch=""
  local custom_repo=""
  local custom_branch=""
  local predefined_json_entries=""
  local branch_json_entries=""
  local custom_json_entries=""
  local escaped_app_id=""
  local escaped_branch=""
  local escaped_repo=""
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

  while IFS= read -r line; do
    if [ -z "${line}" ]; then
      continue
    fi

    custom_repo="${line%%|*}"
    custom_branch="${line#*|}"
    if [ -z "${custom_repo}" ] || [ -z "${custom_branch}" ]; then
      continue
    fi

    escaped_repo="$(json_escape_string "${custom_repo}")"
    escaped_branch="$(json_escape_string "${custom_branch}")"
    entry_json="$(printf '        {\n          "repo": "%s",\n          "branch": "%s"\n        }' "${escaped_repo}" "${escaped_branch}")"
    if [ -z "${custom_json_entries}" ]; then
      custom_json_entries="${entry_json}"
    else
      custom_json_entries="${custom_json_entries}"$',\n'"${entry_json}"
    fi
  done <<EOF
${custom_apps_lines}
EOF

  printf -v "${result_var}" '{\n      "predefined": [\n%s\n      ],\n      "predefined_branches": {\n%s\n      },\n      "custom": [\n%s\n      ]\n    }' "${predefined_json_entries}" "${branch_json_entries}" "${custom_json_entries}"
}

render_metadata_apps_json_object_from_metadata() {
  local result_var="${1}"
  local metadata_path="${2}"
  local predefined_csv=""
  local branch_lines=""
  local custom_lines=""
  local apps_json_object=""

  predefined_csv="$(get_metadata_apps_predefined_csv "${metadata_path}" || true)"
  branch_lines="$(get_metadata_apps_predefined_branch_lines "${metadata_path}" || true)"
  custom_lines="$(get_metadata_apps_custom_lines "${metadata_path}" || true)"
  build_metadata_apps_json_object apps_json_object "${predefined_csv}" "${branch_lines}" "${custom_lines}"
  printf -v "${result_var}" "%s" "${apps_json_object}"
}

build_stack_apps_json_content_from_metadata_apps() {
  local result_var="${1}"
  local stack_dir="${2}"
  local metadata_path=""
  local preset_apps_csv=""
  local custom_apps_lines=""
  local predefined_branch=""
  local preset_branch=""
  local catalog_default_branch=""
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

  if ! easy_docker_require_jq; then
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
        catalog_default_branch="$(get_predefined_app_default_branch_by_id "${app}" || true)"
        if [ -n "${catalog_default_branch}" ]; then
          predefined_branch="${catalog_default_branch}"
        else
          predefined_branch="${preset_branch}"
        fi
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
