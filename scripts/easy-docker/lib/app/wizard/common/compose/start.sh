#!/usr/bin/env bash

load_easy_docker_compose_lifecycle_modules() {
  local lifecycle_dir=""
  lifecycle_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/start/start.sh
  source "${lifecycle_dir}/start.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/start/stop.sh
  source "${lifecycle_dir}/stop.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/start/restart.sh
  source "${lifecycle_dir}/restart.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/start/delete.sh
  source "${lifecycle_dir}/delete.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/start/status.sh
  source "${lifecycle_dir}/status.sh"
}

load_easy_docker_compose_lifecycle_modules
