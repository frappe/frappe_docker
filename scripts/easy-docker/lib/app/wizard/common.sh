#!/usr/bin/env bash

load_easy_docker_wizard_common_modules() {
  local wizard_dir=""
  wizard_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/constants.sh
  source "${wizard_dir}/common/constants.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/core.sh
  source "${wizard_dir}/common/core.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/helpers.sh
  source "${wizard_dir}/common/helpers.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose.sh
  source "${wizard_dir}/common/compose.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/apps.sh
  source "${wizard_dir}/common/apps.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/ux.sh
  source "${wizard_dir}/common/ux.sh"
}

load_easy_docker_wizard_common_modules
