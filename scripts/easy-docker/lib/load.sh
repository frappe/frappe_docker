#!/usr/bin/env bash

load_easy_docker_modules() {
  local lib_dir=""
  lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/core/commands.sh
  source "${lib_dir}/core/commands.sh"
  # shellcheck source=scripts/easy-docker/lib/core/messages.sh
  source "${lib_dir}/core/messages.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/load.sh
  source "${lib_dir}/install/gum/load.sh"
  # shellcheck source=scripts/easy-docker/lib/checks/docker.sh
  source "${lib_dir}/checks/docker.sh"
  # shellcheck source=scripts/easy-docker/lib/ui/screens.sh
  source "${lib_dir}/ui/screens.sh"
  # shellcheck source=scripts/easy-docker/lib/app/screen.sh
  source "${lib_dir}/app/screen.sh"
  # shellcheck source=scripts/easy-docker/lib/app/options.sh
  source "${lib_dir}/app/options.sh"
  # shellcheck source=scripts/easy-docker/lib/app/run.sh
  source "${lib_dir}/app/run.sh"
}

load_easy_docker_modules
