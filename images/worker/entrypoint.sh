#!/bin/bash

set -e

# Link Frappe's node_modules/ to make Website Theme work
if test -d /home/frappe/frappe-bench/sites/assets/frappe/node_modules; then
  ln -sfn /home/frappe/frappe-bench/sites/assets/frappe/node_modules /home/frappe/frappe-bench/apps/frappe/node_modules
fi

exec "$@"
