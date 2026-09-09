#!/usr/bin/env bash

EASY_DOCKER_SITE_ERROR_DETAIL=""
EASY_DOCKER_SITE_ERROR_LOG_PATH=""

load_easy_docker_site_modules() {
  local site_dir=""
  site_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/site"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/metadata.sh
  source "${site_dir}/metadata.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/bootstrap.sh
  source "${site_dir}/bootstrap.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/backup.sh
  source "${site_dir}/backup.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/apps.sh
  source "${site_dir}/apps.sh"
}

load_easy_docker_site_modules
