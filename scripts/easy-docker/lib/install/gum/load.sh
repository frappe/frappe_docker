#!/usr/bin/env bash

load_gum_install_modules() {
  local gum_lib_dir=""
  gum_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/install/gum/platform.sh
  source "${gum_lib_dir}/platform.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/assets.sh
  source "${gum_lib_dir}/assets.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/package_manager.sh
  source "${gum_lib_dir}/package_manager.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/github_release.sh
  source "${gum_lib_dir}/github_release.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/ensure.sh
  source "${gum_lib_dir}/ensure.sh"
}

load_gum_install_modules
