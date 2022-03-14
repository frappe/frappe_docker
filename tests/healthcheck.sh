#!/bin/bash
set -e

get_key() {
  jq -r ".$1" /home/frappe/frappe-bench/sites/common_site_config.json
}

get_redis_url() {
  URL=$(get_key "$1" | sed 's|redis://||g')
  if [[ ${URL} == *"/"* ]]; then
    URL=$(echo "${URL}" | cut -f1 -d"/")
  fi
  echo "$URL"
}

check_connection() {
  echo "Check $1"
  wait-for-it "$1" -t 1
}

check_connection "$(get_key db_host):$(get_key db_port)"
check_connection "$(get_redis_url redis_cache)"
check_connection "$(get_redis_url redis_queue)"
check_connection "$(get_redis_url redis_socketio)"

if [[ "$1" = -p || "$1" = --ping-service ]]; then
  check_connection "$2"
fi
