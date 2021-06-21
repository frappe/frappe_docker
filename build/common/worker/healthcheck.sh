#!/bin/bash
set -ea

function getRedisUrl() {
  cat ${1} | grep $2 | awk -v word=$2 '$word { gsub(/[",]/,"",$2); print $2}' | tr -d '\n' | sed 's|redis://||g'
}

COMMON_SITE_CONFIG_JSON='/home/frappe/frappe-bench/sites/common_site_config.json'

# Set DB Host and port
DB_HOST=$(cat $COMMON_SITE_CONFIG_JSON | awk '/db_host/ { gsub(/[",]/,"",$2); print $2}' | tr -d '\n')
DB_PORT=$(cat $COMMON_SITE_CONFIG_JSON | awk '/db_port/ { gsub(/[",]/,"",$2); print $2}' | tr -d '\n')
if [[ -z "$DB_PORT" ]]; then
  DB_PORT=3306
fi

# Set REDIS host:port
REDIS_CACHE=$(getRedisUrl "$COMMON_SITE_CONFIG_JSON" "redis_cache")
if [[ "$REDIS_CACHE" == *"/"* ]]; then
  REDIS_CACHE=$(echo $REDIS_CACHE | cut -f1 -d"/")
fi

REDIS_QUEUE=$(getRedisUrl "$COMMON_SITE_CONFIG_JSON" "redis_queue")
if [[ "$REDIS_QUEUE" == *"/"* ]]; then
  REDIS_QUEUE=$(echo $REDIS_QUEUE | cut -f1 -d"/")
fi

REDIS_SOCKETIO=$(getRedisUrl "$COMMON_SITE_CONFIG_JSON" "redis_socketio")
if [[ "$REDIS_SOCKETIO" == *"/"* ]]; then
  REDIS_SOCKETIO=$(echo $REDIS_SOCKETIO | cut -f1 -d"/")
fi

echo "Check $DB_HOST:$DB_PORT"
wait-for-it "$DB_HOST:$DB_PORT" -t 1
echo "Check $REDIS_CACHE"
wait-for-it "$REDIS_CACHE" -t 1
echo "Check $REDIS_QUEUE"
wait-for-it "$REDIS_QUEUE" -t 1
echo "Check $REDIS_SOCKETIO"
wait-for-it "$REDIS_SOCKETIO" -t 1

if [[ "$1" = "-p" ]] || [[ "$1" = "--ping-service" ]]; then
  echo "Check $2"
  wait-for-it "$2" -t 1
fi
