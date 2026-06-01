#!/usr/bin/env bash

get_jq_checksums_path() {
  local jq_lib_dir=""

  jq_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  printf '%s/../../../config/jq-checksums.tsv\n' "${jq_lib_dir}"
}

get_pinned_jq_version() {
  local checksums_path=""
  local release_version=""

  checksums_path="$(get_jq_checksums_path)"
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

get_pinned_jq_asset_checksum() {
  local release_version="${1}"
  local asset_name="${2}"
  local checksums_path=""
  local expected_checksum=""

  checksums_path="$(get_jq_checksums_path)"
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

sha256_verification_available_for_jq() {
  command_exists sha256sum ||
    command_exists shasum ||
    command_exists openssl ||
    command_exists certutil
}

compute_file_sha256_for_jq() {
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

verify_file_sha256_for_jq() {
  local file_path="${1}"
  local expected_checksum="${2}"
  local actual_checksum=""

  actual_checksum="$(compute_file_sha256_for_jq "${file_path}" || true)"
  if [ -z "${actual_checksum}" ]; then
    return 1
  fi

  if [ "${actual_checksum}" != "$(printf '%s' "${expected_checksum}" | tr '[:upper:]' '[:lower:]')" ]; then
    return 1
  fi

  return 0
}

get_jq_asset_candidates() {
  local jq_os="${1}"
  local jq_arch="${2}"

  case "${jq_os}:${jq_arch}" in
  linux:amd64)
    printf '%s\n%s\n' "jq-linux-amd64" "jq-linux64"
    ;;
  linux:arm64)
    printf '%s\n' "jq-linux-arm64"
    ;;
  linux:armhf)
    printf '%s\n' "jq-linux-armhf"
    ;;
  macos:amd64)
    printf '%s\n%s\n' "jq-macos-amd64" "jq-osx-amd64"
    ;;
  macos:arm64)
    printf '%s\n' "jq-macos-arm64"
    ;;
  windows:amd64)
    printf '%s\n%s\n' "jq-windows-amd64.exe" "jq-win64.exe"
    ;;
  esac
}
