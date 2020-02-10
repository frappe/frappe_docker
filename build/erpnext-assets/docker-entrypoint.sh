#!/bin/bash

## Thanks
# https://serverfault.com/a/919212
##

set -e

rsync -a --delete /var/www/html/assets/js /assets
rsync -a --delete /var/www/html/assets/css /assets
rsync -a --delete /var/www/html/assets/frappe /assets
rsync -a --delete /var/www/html/assets/erpnext /assets

chmod -R 755 /assets

if [[ -z "$ERPNEXT_PY" ]]; then
    export ERPNEXT_PY=0.0.0.0
fi

if [[ -z "$ERPNEXT_PY_PORT" ]]; then
    export ERPNEXT_PY_PORT=8000
fi

if [[ -z "$FRAPPE_SOCKETIO" ]]; then
    export FRAPPE_SOCKETIO=0.0.0.0
fi

if [[ -z "$FRAPPE_SOCKETIO_PORT" ]]; then
    export FRAPPE_SOCKETIO_PORT=9000
fi

envsubst '${API_HOST} ${API_PORT} ${ERPNEXT_PY} ${ERPNEXT_PY_PORT} ${FRAPPE_SOCKETIO} ${FRAPPE_SOCKETIO_PORT}' \
    < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec "$@"
