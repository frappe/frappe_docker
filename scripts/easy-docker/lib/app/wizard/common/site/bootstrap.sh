#!/usr/bin/env bash

load_easy_docker_site_bootstrap_modules() {
  local bootstrap_dir=""
  bootstrap_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bootstrap"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/bootstrap/validation.sh
  source "${bootstrap_dir}/validation.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/bootstrap/runtime.sh
  source "${bootstrap_dir}/runtime.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/bootstrap/errors.sh
  source "${bootstrap_dir}/errors.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/bootstrap/state.sh
  source "${bootstrap_dir}/state.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/bootstrap/lifecycle.sh
  source "${bootstrap_dir}/lifecycle.sh"
}

load_easy_docker_site_bootstrap_modules
