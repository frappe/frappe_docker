#!/usr/bin/env bash

trim_frappe_catalog_field() {
  local result_var="${1}"
  local value="${2}"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"

  printf -v "${result_var}" "%s" "${value}"
}

is_valid_frappe_catalog_id() {
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

is_valid_frappe_branch_name() {
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

get_frappe_versions_catalog_path() {
  local repo_root=""

  repo_root="$(get_easy_docker_repo_root)"
  printf '%s/scripts/easy-docker/config/frappe.tsv\n' "${repo_root}"
}

get_frappe_versions_catalog_entries() {
  local catalog_path=""
  local raw_line=""
  local line=""
  local version_id=""
  local version_label=""
  local frappe_branch=""
  local extra=""
  local seen_ids=","
  local seen_labels=","

  catalog_path="$(get_frappe_versions_catalog_path)"
  if [ ! -f "${catalog_path}" ]; then
    return 1
  fi

  while IFS= read -r raw_line || [ -n "${raw_line}" ]; do
    trim_frappe_catalog_field line "${raw_line}"
    if [ -z "${line}" ]; then
      continue
    fi

    case "${line}" in
    \#*)
      continue
      ;;
    esac

    if [[ "${line}" == *$'\t'* ]]; then
      IFS=$'\t' read -r version_id version_label frappe_branch extra <<<"${line}"
    else
      IFS='|' read -r version_id version_label frappe_branch extra <<<"${line}"
    fi

    trim_frappe_catalog_field version_id "${version_id}"
    trim_frappe_catalog_field version_label "${version_label}"
    trim_frappe_catalog_field frappe_branch "${frappe_branch}"
    trim_frappe_catalog_field extra "${extra}"

    if [ -n "${extra}" ] || [ -z "${version_id}" ] || [ -z "${version_label}" ] || [ -z "${frappe_branch}" ]; then
      return 1
    fi

    if ! is_valid_frappe_catalog_id "${version_id}"; then
      return 1
    fi

    if ! is_valid_frappe_branch_name "${frappe_branch}"; then
      return 1
    fi

    case "${seen_ids}" in
    *,"${version_id}",*)
      return 1
      ;;
    esac
    case "${seen_labels}" in
    *,"${version_label}",*)
      return 1
      ;;
    esac

    seen_ids="${seen_ids}${version_id},"
    seen_labels="${seen_labels}${version_label},"

    printf '%s|%s|%s\n' "${version_id}" "${version_label}" "${frappe_branch}"
  done <"${catalog_path}"
}

get_frappe_version_branch_by_label() {
  local label_lookup="${1}"
  local entry=""
  local version_id=""
  local version_label=""
  local frappe_branch=""

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r version_id version_label frappe_branch <<<"${entry}"
    if [ "${version_label}" = "${label_lookup}" ]; then
      printf '%s\n' "${frappe_branch}"
      return 0
    fi
  done < <(get_frappe_versions_catalog_entries)

  return 1
}

get_frappe_version_label_by_branch() {
  local branch_lookup="${1}"
  local entry=""
  local version_id=""
  local version_label=""
  local frappe_branch=""

  while IFS= read -r entry; do
    if [ -z "${entry}" ]; then
      continue
    fi

    IFS='|' read -r version_id version_label frappe_branch <<<"${entry}"
    if [ "${frappe_branch}" = "${branch_lookup}" ]; then
      printf '%s\n' "${version_label}"
      return 0
    fi
  done < <(get_frappe_versions_catalog_entries)

  return 1
}
