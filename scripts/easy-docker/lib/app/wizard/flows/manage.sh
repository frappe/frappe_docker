#!/usr/bin/env bash

load_easy_docker_manage_flow_modules() {
  local manage_dir=""
  manage_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/manage"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/manage/docker.sh
  source "${manage_dir}/docker.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/manage/prompts.sh
  source "${manage_dir}/prompts.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/manage/site.sh
  source "${manage_dir}/site.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/manage/stack.sh
  source "${manage_dir}/stack.sh"
}

load_easy_docker_manage_flow_modules
