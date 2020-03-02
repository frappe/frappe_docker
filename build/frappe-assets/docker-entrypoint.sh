#!/bin/bash

## Thanks
# https://serverfault.com/a/919212
##

set -e

rsync -a --delete /var/www/html/assets/js /assets
rsync -a --delete /var/www/html/assets/css /assets
rsync -a --delete /var/www/html/assets/frappe /assets

chmod -R 755 /assets

if [[ -z "$FRAPPE_PY" ]]; then
    export FRAPPE_PY=0.0.0.0
fi

if [[ -z "$FRAPPE_PY_PORT" ]]; then
    export FRAPPE_PY_PORT=8000
fi

if [[ -z "$FRAPPE_SOCKETIO" ]]; then
    export FRAPPE_SOCKETIO=0.0.0.0
fi

if [[ -z "$SOCKETIO_PORT" ]]; then
    export SOCKETIO_PORT=9000
fi

envsubst '${API_HOST}
    ${API_PORT}
    ${FRAPPE_PY}
    ${FRAPPE_PY_PORT}
    ${FRAPPE_SOCKETIO}
    ${SOCKETIO_PORT}' \
    < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec "$@"
