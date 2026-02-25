#!/usr/bin/env bash

command_exists() {
  command -v "${1}" >/dev/null 2>&1 || command -v "${1}.exe" >/dev/null 2>&1
}

run_with_privileges() {
  if command_exists sudo; then
    sudo "$@"
    return
  fi

  "$@"
}

copy_binary() {
  local source_path="${1}"
  local target_path="${2}"

  if command_exists install; then
    install -m 0755 "${source_path}" "${target_path}"
    return $?
  fi

  cp "${source_path}" "${target_path}" && chmod +x "${target_path}"
}

copy_binary_with_privileges() {
  local source_path="${1}"
  local target_path="${2}"

  if command_exists install; then
    run_with_privileges install -m 0755 "${source_path}" "${target_path}"
    return $?
  fi

  run_with_privileges cp "${source_path}" "${target_path}" &&
    run_with_privileges chmod +x "${target_path}"
}

detect_gum_platform() {
  local raw_os=""
  local raw_arch=""

  raw_os="$(uname -s 2>/dev/null || echo unknown)"
  raw_arch="$(uname -m 2>/dev/null || echo unknown)"

  case "${raw_os}" in
  Linux*)
    GUM_OS="Linux"
    ;;
  Darwin*)
    GUM_OS="Darwin"
    ;;
  MINGW* | MSYS* | CYGWIN* | Windows_NT)
    GUM_OS="Windows"
    ;;
  *)
    return 1
    ;;
  esac

  case "${raw_arch}" in
  x86_64 | amd64)
    GUM_ARCH="x86_64"
    ;;
  aarch64 | arm64)
    GUM_ARCH="arm64"
    ;;
  armv7l | armv7)
    GUM_ARCH="armv7"
    ;;
  *)
    return 1
    ;;
  esac

  return 0
}

get_os_aliases() {
  local os_name="${1}"
  local os_lower=""

  os_lower="$(printf '%s' "${os_name}" | tr '[:upper:]' '[:lower:]')"

  if [ "${os_lower}" = "${os_name}" ]; then
    printf '%s\n' "${os_name}"
    return
  fi

  printf '%s\n%s\n' "${os_name}" "${os_lower}"
}

get_arch_aliases() {
  case "${1}" in
  x86_64)
    printf '%s\n%s\n' "x86_64" "amd64"
    ;;
  arm64)
    printf '%s\n%s\n' "arm64" "aarch64"
    ;;
  armv7)
    printf '%s\n%s\n' "armv7" "armv7l"
    ;;
  *)
    printf '%s\n' "${1}"
    ;;
  esac
}

get_gum_asset_candidates() {
  local release_version="${1}"
  local os_alias=""
  local arch_alias=""
  local ext=""

  while IFS= read -r os_alias; do
    while IFS= read -r arch_alias; do
      for ext in tar.gz zip; do
        printf 'gum_%s_%s_%s.%s\n' "${release_version}" "${os_alias}" "${arch_alias}" "${ext}"
      done
    done < <(get_arch_aliases "${GUM_ARCH}")
  done < <(get_os_aliases "${GUM_OS}")
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

install_gum_from_github_release() {
  local release_version=""
  local asset_name=""
  local downloaded_asset_path=""
  local download_url=""
  local tmp_dir=""
  local extract_dir=""
  local target_dir=""
  local gum_binary_path=""
  local target_binary_name="gum"

  if ! command_exists curl; then
    return 1
  fi

  if ! detect_gum_platform; then
    echo "Unsupported platform for automatic GitHub fallback."
    return 1
  fi

  release_version="$(
    curl -fsSL "https://api.github.com/repos/charmbracelet/gum/releases/latest" |
      sed -n 's/.*"tag_name":[[:space:]]*"v\([^"]*\)".*/\1/p' |
      head -n 1
  )"

  if [ -z "${release_version}" ]; then
    return 1
  fi

  tmp_dir="$(mktemp -d)"
  extract_dir="${tmp_dir}/extract"

  while IFS= read -r asset_name; do
    download_url="https://github.com/charmbracelet/gum/releases/download/v${release_version}/${asset_name}"
    if curl -fsSL "${download_url}" -o "${tmp_dir}/${asset_name}"; then
      downloaded_asset_path="${tmp_dir}/${asset_name}"
      break
    fi
  done < <(get_gum_asset_candidates "${release_version}")

  if [ -z "${downloaded_asset_path}" ]; then
    rm -rf "${tmp_dir}"
    return 1
  fi

  if ! extract_gum_asset "${downloaded_asset_path}" "${extract_dir}"; then
    rm -rf "${tmp_dir}"
    return 1
  fi

  gum_binary_path="$(find_gum_binary "${extract_dir}" || true)"

  if [ -z "${gum_binary_path}" ]; then
    rm -rf "${tmp_dir}"
    return 1
  fi

  if [[ "${gum_binary_path}" == *.exe ]]; then
    target_binary_name="gum.exe"
  fi

  if [ "${GUM_OS}" != "Windows" ] && [ -w "/usr/local/bin" ]; then
    target_dir="/usr/local/bin"
    if copy_binary "${gum_binary_path}" "${target_dir}/${target_binary_name}"; then
      rm -rf "${tmp_dir}"
      return 0
    fi
  fi

  if [ "${GUM_OS}" != "Windows" ] && command_exists sudo; then
    if copy_binary_with_privileges "${gum_binary_path}" "/usr/local/bin/${target_binary_name}"; then
      rm -rf "${tmp_dir}"
      return 0
    fi
  fi

  target_dir="${HOME}/.local/bin"
  mkdir -p "${target_dir}"
  if copy_binary "${gum_binary_path}" "${target_dir}/${target_binary_name}"; then
    rm -rf "${tmp_dir}"
    return 0
  fi

  rm -rf "${tmp_dir}"
  return 1
}

install_gum_with_package_manager() {
  local pm_attempted=0

  if command_exists brew; then
    pm_attempted=1
    if brew install gum; then
      return 0
    fi
  fi

  if command_exists apt-get; then
    pm_attempted=1
    if run_with_privileges apt-get update && run_with_privileges apt-get install -y gum; then
      return 0
    fi
  fi

  if command_exists dnf; then
    pm_attempted=1
    if run_with_privileges dnf install -y gum; then
      return 0
    fi
  fi

  if command_exists pacman; then
    pm_attempted=1
    if run_with_privileges pacman -Sy --noconfirm gum; then
      return 0
    fi
  fi

  if command_exists zypper; then
    pm_attempted=1
    if run_with_privileges zypper --non-interactive install gum; then
      return 0
    fi
  fi

  if command_exists winget; then
    pm_attempted=1
    if winget install --id Charmbracelet.Gum -e --accept-source-agreements --accept-package-agreements; then
      return 0
    fi
  fi

  if command_exists choco; then
    pm_attempted=1
    if choco install gum -y; then
      return 0
    fi
  fi

  if [ "${pm_attempted}" -eq 0 ]; then
    echo "No supported package manager was found."
  else
    echo "Package manager installation did not succeed."
  fi

  return 1
}

should_use_github_fallback() {
  local answer=""

  if [ ! -t 0 ]; then
    echo "GitHub fallback prompt requires an interactive terminal."
    return 1
  fi

  printf "Use GitHub binary fallback for gum? [y/N]: "
  read -r answer

  case "${answer}" in
  y | Y | yes | YES)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

ensure_gum() {
  local disable_github_binary_fallback="${1:-0}"

  if command_exists gum; then
    return 0
  fi

  echo "gum is not installed. Trying package manager installation..."

  if install_gum_with_package_manager; then
    hash -r
  fi

  if command_exists gum; then
    echo "gum was installed successfully."
    return 0
  fi

  if [ "${disable_github_binary_fallback}" = "1" ]; then
    echo "GitHub binary fallback is disabled."
    echo "Install gum manually: https://github.com/charmbracelet/gum#installation"
    echo "If installed into ~/.local/bin, add it to PATH first."
    exit 1
  fi

  if should_use_github_fallback; then
    echo "Trying GitHub release fallback..."
    if install_gum_from_github_release; then
      hash -r
    fi
  else
    echo "GitHub fallback was not selected."
    echo "Install gum manually: https://github.com/charmbracelet/gum#installation"
    echo "If installed into ~/.local/bin, add it to PATH first."
    exit 1
  fi

  if command_exists gum; then
    echo "gum was installed successfully."
    return 0
  fi

  echo "Automatic installation failed."
  echo "Install gum manually: https://github.com/charmbracelet/gum#installation"
  echo "If installed into ~/.local/bin, add it to PATH first."
  exit 1
}
