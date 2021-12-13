#!/bin/bash

# TODO: Set config dynamically, so changes in compose file have affect

set -e

function create_common_site_config() {
  if [[ ! -f common_site_config.json ]]; then
    config=$(
      cat <<EOF
{
    "db_host": "${DB_HOST}",
    "db_port": ${DB_PORT},
    "redis_cache": "redis://${REDIS_CACHE}",
    "redis_queue": "redis://${REDIS_QUEUE}",
    "redis_socketio": "redis://${REDIS_SOCKETIO}",
    "socketio_port": ${SOCKETIO_PORT}
}
EOF
    )
    echo "$config" >/home/frappe/frappe-bench/sites/common_site_config.json
  fi
}

create_common_site_config
exec "$@"
