#!/usr/bin/env bash

get_gum_asset_candidates() {
  local release_version="${1}"
  local gum_os="${2}"
  local gum_arch="${3}"
  local os_alias=""
  local arch_alias=""
  local ext=""

  while IFS= read -r os_alias; do
    while IFS= read -r arch_alias; do
      for ext in tar.gz zip; do
        printf 'gum_%s_%s_%s.%s\n' "${release_version}" "${os_alias}" "${arch_alias}" "${ext}"
      done
    done < <(get_arch_aliases "${gum_arch}")
  done < <(get_os_aliases "${gum_os}")
}

extract_gum_asset() {
  local asset_path="${1}"
  local extract_dir="${2}"

  mkdir -p "${extract_dir}"

  case "${asset_path}" in
  *.tar.gz)
    if ! command_exists tar; then
      echo "tar is required to extract gum tar.gz assets."
      return 1
    fi
    tar -xzf "${asset_path}" -C "${extract_dir}"
    ;;
  *.zip)
    if ! command_exists unzip; then
      echo "unzip is required to extract gum zip assets."
      return 1
    fi
    unzip -q "${asset_path}" -d "${extract_dir}"
    ;;
  *)
    return 1
    ;;
  esac
}

find_gum_binary() {
  local search_dir="${1}"
  local found_path=""

  found_path="$(
    find "${search_dir}" -type f \( -name "gum" -o -name "gum.exe" \) 2>/dev/null |
      head -n 1
  )"

  if [ -n "${found_path}" ]; then
    printf '%s\n' "${found_path}"
    return 0
  fi

  return 1
}

fetch_latest_gum_release_version() {
  local api_payload=""
  local tag_name=""

  api_payload="$(curl -fsSL "https://api.github.com/repos/charmbracelet/gum/releases/latest")" || return 1

  if command_exists jq; then
    tag_name="$(printf '%s' "${api_payload}" | jq -r '.tag_name // empty')"
  else
    tag_name="$(printf '%s' "${api_payload}" | sed -n 's/.*"tag_name":[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
  fi

  tag_name="${tag_name#v}"
  if [ -z "${tag_name}" ]; then
    return 1
  fi

  printf '%s\n' "${tag_name}"
}
