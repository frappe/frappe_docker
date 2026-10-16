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

parse_predefined_app_catalog_entry() {
  local entry="${1}"
  local app_id_var="${2}"
  local app_label_var="${3}"
  local app_repo_var="${4}"
  local app_default_branch_var="${5}"
  local app_branches_csv_var="${6}"
  local parsed_app_id=""
  local parsed_app_label=""
  local parsed_app_repo=""
  local parsed_app_default_branch=""
  local parsed_app_branches_csv=""

  IFS='|' read -r parsed_app_id parsed_app_label parsed_app_repo parsed_app_default_branch parsed_app_branches_csv <<<"${entry}"
  printf -v "${app_id_var}" "%s" "${parsed_app_id}"
  printf -v "${app_label_var}" "%s" "${parsed_app_label}"
  printf -v "${app_repo_var}" "%s" "${parsed_app_repo}"
  printf -v "${app_default_branch_var}" "%s" "${parsed_app_default_branch}"
  printf -v "${app_branches_csv_var}" "%s" "${parsed_app_branches_csv}"
}

get_predefined_app_field_by_field() {
  local lookup_field="${1}"
  local lookup_value="${2}"
  local result_field="${3}"
  local entry=""
  local app_id=""
  local app_label=""
  local app_repo=""
  local app_default_branch=""
  local app_branches_csv=""
  local lookup_candidate=""
  local result_value=""

  trim_predefined_catalog_field lookup_value "${lookup_value}"
  if [ -z "${lookup_value}" ]; then
    return 1
  fi

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    parse_predefined_app_catalog_entry "${entry}" app_id app_label app_repo app_default_branch app_branches_csv

    case "${lookup_field}" in
    id)
      lookup_candidate="${app_id}"
      ;;
    label)
      lookup_candidate="${app_label}"
      ;;
    *)
      return 1
      ;;
    esac

    trim_predefined_catalog_field lookup_candidate "${lookup_candidate}"
    if [ "${lookup_candidate}" != "${lookup_value}" ]; then
      continue
    fi

    case "${result_field}" in
    id)
      result_value="${app_id}"
      ;;
    label)
      result_value="${app_label}"
      ;;
    repo)
      result_value="${app_repo}"
      ;;
    default_branch)
      result_value="${app_default_branch}"
      ;;
    branches_csv)
      result_value="${app_branches_csv}"
      ;;
    *)
      return 1
      ;;
    esac

    printf '%s\n' "${result_value}"
    return 0
  done < <(get_predefined_apps_catalog_entries)

  return 1
}

get_predefined_app_id_by_label() {
  local label="${1}"
  get_predefined_app_field_by_field "label" "${label}" "id"
}

get_predefined_app_repo_by_id() {
  local app_id_lookup="${1}"
  get_predefined_app_field_by_field "id" "${app_id_lookup}" "repo"
}

get_predefined_app_label_by_id() {
  local app_id_lookup="${1}"
  get_predefined_app_field_by_field "id" "${app_id_lookup}" "label"
}

get_predefined_app_default_branch_by_id() {
  local app_id_lookup="${1}"
  get_predefined_app_field_by_field "id" "${app_id_lookup}" "default_branch"
}

get_predefined_app_branch_lines_by_id() {
  local result_var="${1}"
  local app_id_lookup="${2}"
  local app_branches_csv=""
  local branch=""
  local branch_lines=""
  local -a branches=()

  app_branches_csv="$(get_predefined_app_field_by_field "id" "${app_id_lookup}" "branches_csv" || true)"
  if [ -z "${app_branches_csv}" ]; then
    return 1
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
}

predefined_app_catalog_has_id() {
  local app_id_lookup="${1}"

  if [ -z "${app_id_lookup}" ]; then
    return 1
  fi

  get_predefined_app_field_by_field "id" "${app_id_lookup}" "id" >/dev/null 2>&1
}

predefined_app_catalog_has_label() {
  local app_label_lookup="${1}"

  if [ -z "${app_label_lookup}" ]; then
    return 1
  fi

  get_predefined_app_field_by_field "label" "${app_label_lookup}" "label" >/dev/null 2>&1
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
