#!/usr/bin/env bash

cleanup_gum_tmp_dir() {
  local tmp_dir="${1:-}"

  if [ -n "${tmp_dir}" ] && [ -d "${tmp_dir}" ]; then
    rm -rf "${tmp_dir}"
  fi
}

install_gum_from_github_release() {
  local release_version=""
  local asset_name=""
  local asset_path=""
  local download_url=""
  local tmp_dir=""
  local extract_dir=""
  local target_dir=""
  local gum_binary_path=""
  local target_binary_name="gum"
  local gum_os=""
  local gum_arch=""

  if ! command_exists curl; then
    echo "curl is required for the GitHub fallback."
    return 1
  fi

  if ! read -r gum_os gum_arch < <(detect_gum_platform); then
    echo "Unsupported platform for automatic GitHub fallback."
    return 1
  fi

  release_version="$(fetch_latest_gum_release_version || true)"
  if [ -z "${release_version}" ]; then
    echo "Could not determine latest gum release version."
    return 1
  fi

  tmp_dir="$(mktemp -d 2>/dev/null || true)"
  if [ -z "${tmp_dir}" ] || [ ! -d "${tmp_dir}" ]; then
    echo "Failed to create temporary directory for gum installation."
    return 1
  fi
  extract_dir="${tmp_dir}/extract"

  while IFS= read -r asset_name; do
    asset_path="${tmp_dir}/${asset_name}"
    download_url="https://github.com/charmbracelet/gum/releases/download/v${release_version}/${asset_name}"

    if ! curl -fsSL "${download_url}" -o "${asset_path}"; then
      continue
    fi

    rm -rf "${extract_dir}"
    mkdir -p "${extract_dir}"

    if ! extract_gum_asset "${asset_path}" "${extract_dir}"; then
      continue
    fi

    gum_binary_path="$(find_gum_binary "${extract_dir}" || true)"
    if [ -n "${gum_binary_path}" ]; then
      break
    fi
  done < <(get_gum_asset_candidates "${release_version}" "${gum_os}" "${gum_arch}")

  if [ -z "${gum_binary_path}" ]; then
    cleanup_gum_tmp_dir "${tmp_dir}"
    echo "No compatible gum binary was found in GitHub release assets."
    return 1
  fi

  if [[ "${gum_binary_path}" == *.exe ]]; then
    target_binary_name="gum.exe"
  fi

  if [ "${gum_os}" != "Windows" ] && [ -w "/usr/local/bin" ]; then
    target_dir="/usr/local/bin"
    if copy_binary "${gum_binary_path}" "${target_dir}/${target_binary_name}"; then
      cleanup_gum_tmp_dir "${tmp_dir}"
      return 0
    fi
  fi

  if [ "${gum_os}" != "Windows" ] && command_exists sudo; then
    if copy_binary_with_privileges "${gum_binary_path}" "/usr/local/bin/${target_binary_name}"; then
      cleanup_gum_tmp_dir "${tmp_dir}"
      return 0
    fi
  fi

  if [ -n "${HOME:-}" ]; then
    target_dir="${HOME}/.local/bin"
    mkdir -p "${target_dir}"
    if copy_binary "${gum_binary_path}" "${target_dir}/${target_binary_name}"; then
      cleanup_gum_tmp_dir "${tmp_dir}"
      return 0
    fi
  fi

  cleanup_gum_tmp_dir "${tmp_dir}"
  echo "Failed to install gum binary from GitHub release."
  return 1
}
