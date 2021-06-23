#!/bin/bash
set -ea

function getUrl() {
  grep "$2" "$1" | awk -v word="$2" '$word { gsub(/[",]/,"",$2); print $2}' | tr -d '\n'
}

COMMON_SITE_CONFIG_JSON='/home/frappe/frappe-bench/sites/common_site_config.json'

# Set DB Host and port
DB_HOST=$(getUrl "${COMMON_SITE_CONFIG_JSON}" "db_host")
DB_PORT=$(getUrl "${COMMON_SITE_CONFIG_JSON}" "db_port")
if [[ -z "${DB_PORT}" ]]; then
  DB_PORT=3306
fi

# Set REDIS host:port
REDIS_CACHE=$(getUrl "${COMMON_SITE_CONFIG_JSON}" "redis_cache" | sed 's|redis://||g')
if [[ "${REDIS_CACHE}" == *"/"* ]]; then
  REDIS_CACHE=$(echo ${REDIS_CACHE} | cut -f1 -d"/")
fi

REDIS_QUEUE=$(getUrl "${COMMON_SITE_CONFIG_JSON}" "redis_queue" | sed 's|redis://||g')
if [[ "${REDIS_QUEUE}" == *"/"* ]]; then
  REDIS_QUEUE=$(echo ${REDIS_QUEUE} | cut -f1 -d"/")
fi

REDIS_SOCKETIO=$(getUrl "${COMMON_SITE_CONFIG_JSON}" "redis_socketio" | sed 's|redis://||g')
if [[ "${REDIS_SOCKETIO}" == *"/"* ]]; then
  REDIS_SOCKETIO=$(echo ${REDIS_SOCKETIO} | cut -f1 -d"/")
fi

echo "Check ${DB_HOST}:${DB_PORT}"
wait-for-it "${DB_HOST}:${DB_PORT}" -t 1
echo "Check ${REDIS_CACHE}"
wait-for-it "${REDIS_CACHE}" -t 1
echo "Check ${REDIS_QUEUE}"
wait-for-it "${REDIS_QUEUE}" -t 1
echo "Check ${REDIS_SOCKETIO}"
wait-for-it "${REDIS_SOCKETIO}" -t 1

if [[ "$1" = "-p" || "$1" = "--ping-service" ]]; then
  echo "Check $2"
  wait-for-it "$2" -t 1
fi
