#!/usr/bin/env bash

load_easy_docker_wizard_env_modules() {
  local wizard_dir=""
  wizard_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/env/validation.sh
  source "${wizard_dir}/env/validation.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/env/apps.sh
  source "${wizard_dir}/env/apps.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/env/collect.sh
  source "${wizard_dir}/env/collect.sh"
}

load_easy_docker_wizard_env_modules
