#!/bin/bash

function configureEnv() {
  if [[ ! -f /home/frappe/frappe-bench/sites/common_site_config.json ]]; then

    if [[ -z "${MARIADB_HOST}" && -z "${POSTGRES_HOST}" ]]; then
      echo "MARIADB_HOST or POSTGRES_HOST is not set" >&2
      exit 1
    fi

    if [[ -z "${REDIS_CACHE}" ]]; then
      echo "REDIS_CACHE is not set" >&2
      exit 1
    fi

    if [[ -z "${REDIS_QUEUE}" ]]; then
      echo "REDIS_QUEUE is not set" >&2
      exit 1
    fi

    if [[ -z "${REDIS_SOCKETIO}" ]]; then
      echo "REDIS_SOCKETIO is not set" >&2
      exit 1
    fi

    if [[ -z "${SOCKETIO_PORT}" ]]; then
      echo "SOCKETIO_PORT is not set" >&2
      exit 1
    fi

    if [[ -z "${DB_PORT}" ]]; then
      export DB_PORT=3306
    fi

    export DB_HOST="${MARIADB_HOST:-$POSTGRES_HOST}"

    envsubst '${DB_HOST}
      ${DB_PORT}
      ${REDIS_CACHE}
      ${REDIS_QUEUE}
      ${REDIS_SOCKETIO}
      ${SOCKETIO_PORT}' </opt/frappe/common_site_config.json.template >/home/frappe/frappe-bench/sites/common_site_config.json
  fi
}

function checkConnection() {
  /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/check_connection.py
}

function checkConfigExists() {
  COUNTER=0
  while [[ ! -e /home/frappe/frappe-bench/sites/common_site_config.json && ${COUNTER} -le 30 ]]; do
    sleep 1
    ((COUNTER = COUNTER + 1))
    echo "config file not created, retry ${COUNTER}" >&2
  done

  if [[ ! -e /home/frappe/frappe-bench/sites/common_site_config.json ]]; then
    echo "timeout: config file not created" >&2
    exit 1
  fi
}

if [[ ! -e /home/frappe/frappe-bench/sites/apps.txt ]]; then
  find /home/frappe/frappe-bench/apps -mindepth 1 -maxdepth 1 -type d -printf '%f\n' |
    sort -r >/home/frappe/frappe-bench/sites/apps.txt
fi

# symlink node_modules
ln -sfn /home/frappe/frappe-bench/sites/assets/frappe/node_modules \
  /home/frappe/frappe-bench/apps/frappe/node_modules

case "$1" in

  start)
    configureEnv
    checkConnection

    [[ -z "${WORKERS}" ]] && WORKERS='2'

    [[ -z "${FRAPPE_PORT}" ]] && FRAPPE_PORT='8000'

    [[ -z "${WORKER_CLASS}" ]] && WORKER_CLASS='gthread'

    LOAD_CONFIG_FILE=""
    [[ "${WORKER_CLASS}" == "gevent" ]] &&
      LOAD_CONFIG_FILE="-c /home/frappe/frappe-bench/commands/gevent_patch.py"

    if [[ -n "${AUTO_MIGRATE}" ]]; then
      /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/auto_migrate.py
    fi

    /home/frappe/frappe-bench/env/bin/gunicorn ${LOAD_CONFIG_FILE} -b 0.0.0.0:${FRAPPE_PORT} \
      --worker-tmp-dir /dev/shm \
      --threads=4 \
      --workers ${WORKERS} \
      --worker-class=${WORKER_CLASS} \
      --log-file=- \
      -t 120 frappe.app:application --preload
    ;;

  worker)
    checkConfigExists
    checkConnection
    # default WORKER_TYPE=default

    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/worker.py
    ;;

  schedule)
    checkConfigExists
    checkConnection

    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/background.py

    ;;

  new)
    checkConfigExists
    checkConnection

    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/new.py
    exit
    ;;

  drop)
    checkConfigExists
    checkConnection

    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/drop.py
    exit
    ;;

  migrate)
    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/migrate.py
    exit
    ;;

  doctor)
    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/doctor.py "${@:2}"
    exit
    ;;

  backup)

    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/backup.py
    exit
    ;;

  console)
    if [[ -z "$2" ]]; then
      echo "Need to specify a sitename with the command:" >&2
      echo "console <sitename>" >&2
      exit 1
    fi

    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/console.py "$2"
    exit
    ;;

  push-backup)
    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/push_backup.py
    exit
    ;;

  restore-backup)
    /home/frappe/frappe-bench/env/bin/python /home/frappe/frappe-bench/commands/restore_backup.py
    exit
    ;;
  *)
    exec "$@"
    ;;
esac
