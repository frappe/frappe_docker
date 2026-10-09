#!/usr/bin/env bash

cleanup_jq_tmp_dir() {
  local tmp_dir="${1:-}"

  if [ -n "${tmp_dir}" ] && [ -d "${tmp_dir}" ]; then
    rm -rf "${tmp_dir}"
  fi
}

install_jq_from_github_release() {
  local release_version=""
  local checksums_path=""
  local jq_os=""
  local jq_arch=""
  local asset_name=""
  local asset_path=""
  local download_url=""
  local tmp_dir=""
  local target_dir=""
  local target_binary_name="jq"
  local expected_checksum=""

  if ! command_exists curl; then
    echo "curl is required for the GitHub fallback."
    return 1
  fi

  if ! read -r jq_os jq_arch < <(detect_jq_platform); then
    echo "Unsupported platform for automatic GitHub fallback."
    return 1
  fi

  release_version="$(get_pinned_jq_version || true)"
  if [ -z "${release_version}" ]; then
    echo "Could not determine the pinned jq release version."
    return 1
  fi

  checksums_path="$(get_jq_checksums_path)"
  if [ ! -f "${checksums_path}" ]; then
    echo "Pinned jq checksum file is missing: ${checksums_path}"
    return 1
  fi

  if ! sha256_verification_available_for_jq; then
    echo "A SHA256 verification tool is required for the GitHub fallback."
    return 1
  fi

  tmp_dir="$(mktemp -d 2>/dev/null || true)"
  if [ -z "${tmp_dir}" ] || [ ! -d "${tmp_dir}" ]; then
    echo "Failed to create temporary directory for jq installation."
    return 1
  fi

  while IFS= read -r asset_name; do
    expected_checksum="$(get_pinned_jq_asset_checksum "${release_version}" "${asset_name}" || true)"
    if [ -z "${expected_checksum}" ]; then
      continue
    fi

    asset_path="${tmp_dir}/${asset_name}"
    download_url="https://github.com/jqlang/jq/releases/download/jq-${release_version}/${asset_name}"

    if ! curl -fsSL "${download_url}" -o "${asset_path}"; then
      continue
    fi

    if ! verify_file_sha256_for_jq "${asset_path}" "${expected_checksum}"; then
      echo "Checksum verification failed for ${asset_name}."
      continue
    fi

    if [[ "${asset_name}" == *.exe ]]; then
      target_binary_name="jq.exe"
    else
      target_binary_name="jq"
    fi

    if [ "${jq_os}" != "windows" ] && [ -w "/usr/local/bin" ]; then
      target_dir="/usr/local/bin"
      if copy_binary "${asset_path}" "${target_dir}/${target_binary_name}"; then
        cleanup_jq_tmp_dir "${tmp_dir}"
        return 0
      fi
    fi

    if [ "${jq_os}" != "windows" ] && command_exists sudo; then
      if copy_binary_with_privileges "${asset_path}" "/usr/local/bin/${target_binary_name}"; then
        cleanup_jq_tmp_dir "${tmp_dir}"
        return 0
      fi
    fi

    if [ -n "${HOME:-}" ]; then
      target_dir="${HOME}/.local/bin"
      mkdir -p "${target_dir}"
      if copy_binary "${asset_path}" "${target_dir}/${target_binary_name}"; then
        cleanup_jq_tmp_dir "${tmp_dir}"
        return 0
      fi
    fi
  done < <(get_jq_asset_candidates "${jq_os}" "${jq_arch}")

  cleanup_jq_tmp_dir "${tmp_dir}"
  echo "No compatible, verified jq binary was installed from the pinned GitHub release."
  return 1
}
