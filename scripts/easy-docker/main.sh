#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/easy-docker/lib/core/commands.sh
source "${SCRIPT_DIR}/lib/core/commands.sh"
# shellcheck source=scripts/easy-docker/lib/core/messages.sh
source "${SCRIPT_DIR}/lib/core/messages.sh"
# shellcheck source=scripts/easy-docker/lib/install/gum/load.sh
source "${SCRIPT_DIR}/lib/install/gum/load.sh"
# shellcheck source=scripts/easy-docker/lib/checks/docker.sh
source "${SCRIPT_DIR}/lib/checks/docker.sh"
# shellcheck source=scripts/easy-docker/lib/ui/screens.sh
source "${SCRIPT_DIR}/lib/ui/screens.sh"
# shellcheck source=scripts/easy-docker/lib/app/screen.sh
source "${SCRIPT_DIR}/lib/app/screen.sh"
# shellcheck source=scripts/easy-docker/lib/app/options.sh
source "${SCRIPT_DIR}/lib/app/options.sh"
# shellcheck source=scripts/easy-docker/lib/app/run.sh
source "${SCRIPT_DIR}/lib/app/run.sh"

disable_installation_fallback=0
if parse_cli_options disable_installation_fallback "$@"; then
  :
else
  parse_status=$?
  if [ "${parse_status}" -eq 2 ]; then
    exit 0
  fi
  exit "${parse_status}"
fi

if ! ensure_gum "${disable_installation_fallback}"; then
  exit 1
fi

if ! ensure_docker; then
  exit 1
fi

trap 'leave_alt_screen; exit 0' INT TERM
trap 'leave_alt_screen' EXIT

run_easy_docker_app
