#!/usr/bin/env bash

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
  local disable_installation_fallback="${1:-0}"

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

  if [ "${disable_installation_fallback}" = "1" ]; then
    echo "Installation fallback is disabled."
    print_manual_gum_install_guidance
    return 1
  fi

  if should_use_github_fallback; then
    echo "Trying GitHub release fallback..."
    if install_gum_from_github_release; then
      hash -r
    fi
  else
    echo "GitHub fallback was not selected."
    print_manual_gum_install_guidance
    return 1
  fi

  if command_exists gum; then
    echo "gum was installed successfully."
    return 0
  fi

  echo "Automatic installation failed."
  print_manual_gum_install_guidance
  return 1
}
