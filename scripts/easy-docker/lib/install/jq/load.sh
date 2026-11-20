#!/usr/bin/env bash

load_jq_install_modules() {
  local jq_lib_dir=""

  jq_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/install/jq/platform.sh
  source "${jq_lib_dir}/platform.sh"
  # shellcheck source=scripts/easy-docker/lib/install/jq/assets.sh
  source "${jq_lib_dir}/assets.sh"
  # shellcheck source=scripts/easy-docker/lib/install/jq/package_manager.sh
  source "${jq_lib_dir}/package_manager.sh"
  # shellcheck source=scripts/easy-docker/lib/install/jq/github_release.sh
  source "${jq_lib_dir}/github_release.sh"
  # shellcheck source=scripts/easy-docker/lib/install/jq/ensure.sh
  source "${jq_lib_dir}/ensure.sh"
}

load_jq_install_modules
