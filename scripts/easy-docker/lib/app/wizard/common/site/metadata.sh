#!/usr/bin/env bash

load_easy_docker_site_metadata_modules() {
  local metadata_dir=""
  metadata_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/metadata"

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/metadata/read.sh
  source "${metadata_dir}/read.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/metadata/write.sh
  source "${metadata_dir}/write.sh"
}

load_easy_docker_site_metadata_modules
