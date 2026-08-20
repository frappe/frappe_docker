#!/usr/bin/env bash

load_easy_docker_app_modules() {
  local app_dir=""
  app_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common.sh
  source "${app_dir}/wizard/common.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/env.sh
  source "${app_dir}/wizard/env.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/single_host.sh
  source "${app_dir}/wizard/single_host.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows.sh
  source "${app_dir}/wizard/flows.sh"
}

load_easy_docker_app_modules
