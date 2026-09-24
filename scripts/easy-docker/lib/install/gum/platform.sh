#!/usr/bin/env bash

detect_gum_platform() {
  local raw_os=""
  local raw_arch=""
  local gum_os=""
  local gum_arch=""

  raw_os="$(uname -s 2>/dev/null || echo unknown)"
  raw_arch="$(uname -m 2>/dev/null || echo unknown)"

  case "${raw_os}" in
  Linux*)
    gum_os="Linux"
    ;;
  Darwin*)
    gum_os="Darwin"
    ;;
  MINGW* | MSYS* | CYGWIN* | Windows_NT)
    gum_os="Windows"
    ;;
  *)
    return 1
    ;;
  esac

  case "${raw_arch}" in
  x86_64 | amd64)
    gum_arch="x86_64"
    ;;
  aarch64 | arm64)
    gum_arch="arm64"
    ;;
  armv7l | armv7)
    gum_arch="armv7"
    ;;
  *)
    return 1
    ;;
  esac

  printf '%s %s\n' "${gum_os}" "${gum_arch}"
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
