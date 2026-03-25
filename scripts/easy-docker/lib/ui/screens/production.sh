#!/usr/bin/env bash

load_production_screen_modules() {
  local screen_dir=""
  screen_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # shellcheck source=scripts/easy-docker/lib/ui/screens/production/setup.sh
  source "${screen_dir}/production/setup.sh"
  # shellcheck source=scripts/easy-docker/lib/ui/screens/production/topology.sh
  source "${screen_dir}/production/topology.sh"
  # shellcheck source=scripts/easy-docker/lib/ui/screens/production/manage.sh
  source "${screen_dir}/production/manage.sh"
}

load_production_screen_modules
