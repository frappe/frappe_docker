#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/easy-docker/lib/load.sh
source "${SCRIPT_DIR}/lib/load.sh"

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
