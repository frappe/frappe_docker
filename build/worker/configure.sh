#!/bin/bash

set -e
set -x

CUR_DIR="$(pwd)"
cd /home/frappe/frappe-bench/sites

if [[ ! -f common_site_config.json ]]; then
  echo "{}" >common_site_config.json
fi

bench set-config --global --parse socketio_port "${SOCKETIO_PORT}"
bench set-config --global db_host "${DB_HOST}"
bench set-config --global --parse db_port "${DB_PORT}"
bench set-config --global redis_cache "redis://${REDIS_CACHE}"
bench set-config --global redis_queue "redis://${REDIS_QUEUE}"
bench set-config --global redis_socketio "redis://${REDIS_SOCKETIO}"

cd "$CUR_DIR"
exec "$@"
