#!/usr/bin/env bash

detect_jq_platform() {
  local raw_os=""
  local raw_arch=""
  local jq_os=""
  local jq_arch=""

  raw_os="$(uname -s 2>/dev/null || echo unknown)"
  raw_arch="$(uname -m 2>/dev/null || echo unknown)"

  case "${raw_os}" in
  Linux*)
    jq_os="linux"
    ;;
  Darwin*)
    jq_os="macos"
    ;;
  MINGW* | MSYS* | CYGWIN* | Windows_NT)
    jq_os="windows"
    ;;
  *)
    return 1
    ;;
  esac

  case "${raw_arch}" in
  x86_64 | amd64)
    jq_arch="amd64"
    ;;
  aarch64 | arm64)
    jq_arch="arm64"
    ;;
  armv7l | armv7)
    jq_arch="armhf"
    ;;
  *)
    return 1
    ;;
  esac

  if [ "${jq_os}" = "windows" ] && [ "${jq_arch}" != "amd64" ]; then
    return 1
  fi

  if [ "${jq_os}" = "macos" ] && [ "${jq_arch}" = "armhf" ]; then
    return 1
  fi

  printf '%s %s\n' "${jq_os}" "${jq_arch}"
  return 0
}
