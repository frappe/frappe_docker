#!/bin/bash

export COMMON_SITE_CONFIG_JSON='/home/frappe/frappe-bench/sites/common_site_config.json'

# Set DB Host and port
export DB_HOST=`cat $COMMON_SITE_CONFIG_JSON | awk '/db_host/ { gsub(/[",]/,"",$2); print $2}' | tr -d '\n'`
export DB_PORT=`cat $COMMON_SITE_CONFIG_JSON | awk '/db_port/ { gsub(/[",]/,"",$2); print $2}' | tr -d '\n'`
if [[ -z "$DB_PORT" ]]; then
    export DB_PORT=3306
fi

# Set REDIS host:port
export REDIS_CACHE=`cat $COMMON_SITE_CONFIG_JSON | awk '/redis_cache/ { gsub(/[",]/,"",$2); print $2}' | tr -d '\n' | sed 's|redis://||g'`
if [[ "$REDIS_CACHE" == *"/"* ]]; then
  export REDIS_CACHE=`echo $REDIS_CACHE | cut -f1 -d"/"`
fi

export REDIS_QUEUE=`cat $COMMON_SITE_CONFIG_JSON | awk '/redis_queue/ { gsub(/[",]/,"",$2); print $2}' | tr -d '\n' | sed 's|redis://||g'`
if [[ "$REDIS_QUEUE" == *"/"* ]]; then
  export REDIS_QUEUE=`echo $REDIS_QUEUE | cut -f1 -d"/"`
fi

export REDIS_SOCKETIO=`cat $COMMON_SITE_CONFIG_JSON | awk '/redis_socketio/ { gsub(/[",]/,"",$2); print $2}' | tr -d '\n' | sed 's|redis://||g'`
if [[ "$REDIS_SOCKETIO" == *"/"* ]]; then
  export REDIS_SOCKETIO=`echo $REDIS_SOCKETIO | cut -f1 -d"/"`
fi

echo "Check $DB_HOST:$DB_PORT"
wait-for-it $DB_HOST:$DB_PORT -t 1
echo "Check $REDIS_CACHE"
wait-for-it $REDIS_CACHE -t 1
echo "Check $REDIS_QUEUE"
wait-for-it $REDIS_QUEUE -t 1
echo "Check $REDIS_SOCKETIO"
wait-for-it $REDIS_SOCKETIO -t 1

if [[ "$1" = "-p" ]] || [[ "$1" = "--ping-service" ]]; then
    echo "Check $2"
    wait-for-it $2 -t 1
fi
