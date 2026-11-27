#!/usr/bin/env bash

jq_check_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/easy-docker/lib/install/jq/load.sh
source "${jq_check_dir}/../install/jq/load.sh"
