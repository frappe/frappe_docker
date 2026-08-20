#!/usr/bin/env bash

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
