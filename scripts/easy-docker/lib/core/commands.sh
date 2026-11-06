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
