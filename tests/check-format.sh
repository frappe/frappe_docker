#!/bin/bash

echo "Checking bash scripts with shellcheck" >&2

shellcheck --check-sourced --severity=style --color=always --exclude=SC2164,SC2086,SC2012,SC2016 \
  build/common/worker/docker-entrypoint.sh \
  build/common/worker/healthcheck.sh \
  build/common/worker/install_app.sh \
  build/erpnext-nginx/install_app.sh \
  build/frappe-nginx/docker-entrypoint.sh \
  build/frappe-socketio/docker-entrypoint.sh
