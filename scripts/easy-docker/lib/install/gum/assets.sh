#!/usr/bin/env bash

get_gum_checksums_path() {
  local gum_lib_dir=""

  gum_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  printf '%s/../../../config/gum-checksums.tsv\n' "${gum_lib_dir}"
}

get_pinned_gum_version() {
  local checksums_path=""
  local release_version=""

  checksums_path="$(get_gum_checksums_path)"
  if [ ! -f "${checksums_path}" ]; then
    return 1
  fi

  release_version="$(
    awk -F '\t' '
      /^[[:space:]]*#/ { next }
      NF < 3 { next }
      {
        print $1
        exit
      }
    ' "${checksums_path}"
  )"
  if [ -z "${release_version}" ]; then
    return 1
  fi

  printf '%s\n' "${release_version}"
}

get_pinned_gum_asset_checksum() {
  local release_version="${1}"
  local asset_name="${2}"
  local checksums_path=""
  local expected_checksum=""

  checksums_path="$(get_gum_checksums_path)"
  if [ ! -f "${checksums_path}" ]; then
    return 1
  fi

  expected_checksum="$(
    awk -F '\t' -v release_version="${release_version}" -v asset_name="${asset_name}" '
      /^[[:space:]]*#/ { next }
      NF < 3 { next }
      $1 == release_version && $2 == asset_name {
        print $3
        exit
      }
    ' "${checksums_path}"
  )"
  if [ -z "${expected_checksum}" ]; then
    return 1
  fi

  printf '%s\n' "${expected_checksum}"
}

sha256_verification_available() {
  command_exists sha256sum ||
    command_exists shasum ||
    command_exists openssl ||
    command_exists certutil
}

compute_file_sha256() {
  local file_path="${1}"
  local hash_input_path="${file_path}"

  if command_exists sha256sum; then
    sha256sum "${file_path}" | awk '{print tolower($1)}'
    return $?
  fi

  if command_exists shasum; then
    shasum -a 256 "${file_path}" | awk '{print tolower($1)}'
    return $?
  fi

  if command_exists openssl; then
    openssl dgst -sha256 -r "${file_path}" | awk '{print tolower($1)}'
    return $?
  fi

  if command_exists certutil; then
    if command_exists cygpath; then
      hash_input_path="$(cygpath -w "${file_path}" 2>/dev/null || printf '%s' "${file_path}")"
    fi

    certutil -hashfile "${hash_input_path}" SHA256 2>/dev/null |
      awk 'NR == 2 { gsub(/ /, "", $0); print tolower($0); exit }'
    return $?
  fi

  return 1
}

verify_file_sha256() {
  local file_path="${1}"
  local expected_checksum="${2}"
  local actual_checksum=""

  actual_checksum="$(compute_file_sha256 "${file_path}" || true)"
  if [ -z "${actual_checksum}" ]; then
    return 1
  fi

  if [ "${actual_checksum}" != "$(printf '%s' "${expected_checksum}" | tr '[:upper:]' '[:lower:]')" ]; then
    return 1
  fi

  return 0
}

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
