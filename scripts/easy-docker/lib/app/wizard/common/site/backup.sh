#!/usr/bin/env bash

load_easy_docker_site_backup_modules() {
  local backup_dir=""
  backup_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/backup"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/backup/lifecycle.sh
  source "${backup_dir}/lifecycle.sh"
}

load_easy_docker_site_backup_modules
