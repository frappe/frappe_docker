#!/usr/bin/env bash

load_easy_docker_wizard_flow_modules() {
  local wizard_dir=""
  wizard_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/single_host.sh
  source "${wizard_dir}/flows/single_host.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/manage.sh
  source "${wizard_dir}/flows/manage.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/navigation.sh
  source "${wizard_dir}/flows/navigation.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/flows/setup.sh
  source "${wizard_dir}/flows/setup.sh"
}

load_easy_docker_wizard_flow_modules
