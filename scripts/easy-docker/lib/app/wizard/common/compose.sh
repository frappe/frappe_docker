#!/usr/bin/env bash

EASY_DOCKER_BUILD_ERROR_DETAIL=""
# shellcheck disable=SC2034 # Read by manage flow after start_stack_with_compose_from_metadata fails.
EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

load_easy_docker_compose_modules() {
  local compose_dir=""
  compose_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/compose"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/render.sh
  source "${compose_dir}/render.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/start.sh
  source "${compose_dir}/start.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/build.sh
  source "${compose_dir}/build.sh"
}

load_easy_docker_compose_modules
