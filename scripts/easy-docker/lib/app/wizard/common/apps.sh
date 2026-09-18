#!/usr/bin/env bash

load_easy_docker_wizard_app_modules() {
  local apps_dir=""
  apps_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/apps"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/apps/catalog.sh
  source "${apps_dir}/catalog.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/apps/metadata.sh
  source "${apps_dir}/metadata.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/apps/persistence.sh
  source "${apps_dir}/persistence.sh"
}

load_easy_docker_wizard_app_modules
