#!/usr/bin/env bash

load_ui_screen_modules() {
  local screens_dir=""
  screens_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/screens"

  # shellcheck source=scripts/easy-docker/lib/ui/screens/base.sh
  source "${screens_dir}/base.sh"
  # shellcheck source=scripts/easy-docker/lib/ui/screens/production.sh
  source "${screens_dir}/production.sh"
  # shellcheck source=scripts/easy-docker/lib/ui/screens/environment.sh
  source "${screens_dir}/environment.sh"
}

load_ui_screen_modules
