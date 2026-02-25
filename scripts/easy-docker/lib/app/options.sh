#!/usr/bin/env bash

print_usage() {
  cat <<'USAGE'
Usage: bash easy-docker.sh [options]

Options:
  --no-installation-fallback  Disable installation fallback prompt
  -h, --help                  Show this help
USAGE
}

parse_cli_options() {
  local result_var="${1}"
  local disable_installation_fallback=0
  shift

  while [ "$#" -gt 0 ]; do
    case "$1" in
    --no-installation-fallback)
      disable_installation_fallback=1
      ;;
    -h | --help)
      print_usage
      return 2
      ;;
    *)
      echo "Unknown option: $1"
      print_usage
      return 1
      ;;
    esac
    shift
  done

  printf -v "${result_var}" "%s" "${disable_installation_fallback}"
  return 0
}
