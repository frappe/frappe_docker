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
  su frappe -c "node /home/frappe/frappe-bench/apps/frappe/socketio.js"

elif [ "$1" = 'doctor' ]; then

  su frappe -c "node /home/frappe/frappe-bench/apps/frappe/health.js"

else

  exec su frappe -c "$@"

fi
