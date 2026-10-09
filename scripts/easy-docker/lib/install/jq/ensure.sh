#!/usr/bin/env bash

should_use_jq_github_fallback() {
  local answer=""

  if [ ! -t 0 ]; then
    echo "GitHub fallback prompt requires an interactive terminal."
    return 1
  fi

  printf "Use GitHub binary fallback for jq? [y/N]: "
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

ensure_jq() {
  local disable_installation_fallback="${1:-0}"

  if get_easy_docker_jq_command >/dev/null 2>&1; then
    return 0
  fi

  echo "jq is not installed. Trying package manager installation..."

  if install_jq_with_package_manager; then
    hash -r
  fi

  if get_easy_docker_jq_command >/dev/null 2>&1; then
    echo "jq was installed successfully."
    return 0
  fi

  if [ "${disable_installation_fallback}" = "1" ]; then
    echo "Installation fallback is disabled."
    print_manual_jq_install_guidance
    return 1
  fi

  if should_use_jq_github_fallback; then
    echo "Trying pinned GitHub release fallback..."
    if install_jq_from_github_release; then
      hash -r
    fi
  else
    echo "GitHub fallback was not selected."
    print_manual_jq_install_guidance
    return 1
  fi

  if get_easy_docker_jq_command >/dev/null 2>&1; then
    echo "jq was installed successfully."
    return 0
  fi

  echo "Automatic installation failed."
  print_manual_jq_install_guidance
  return 1
}
