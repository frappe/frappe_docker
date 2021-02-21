#!/bin/bash

function checkConfigExists() {
  COUNTER=0
  while [[ ! -e /home/frappe/frappe-bench/sites/common_site_config.json ]] && [[ $COUNTER -le 30 ]] ; do
      sleep 1
      let COUNTER=COUNTER+1
      echo "config file not created, retry $COUNTER"
  done

  if [[ ! -e /home/frappe/frappe-bench/sites/common_site_config.json ]]; then
    echo "timeout: config file not created"
    exit 1
  fi
}

if [ "$1" = 'start' ]; then
  checkConfigExists
  node /home/frappe/frappe-bench/apps/frappe/socketio.js

elif [ "$1" = 'doctor' ]; then

  node /home/frappe/frappe-bench/apps/frappe/health.js

else

  exec -c "$@"

fi
