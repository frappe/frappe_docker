#!/bin/bash -ae

## Thanks
# https://serverfault.com/a/919212
##

rsync -a --delete /var/www/html/assets/* /assets

/rsync

touch /var/www/html/sites/.build -r "$(ls -td /assets/* | head -n 1)"

[[ -z "${FRAPPE_PY}" ]] && FRAPPE_PY='0.0.0.0'

[[ -z "${FRAPPE_PY_PORT}" ]] && FRAPPE_PY_PORT='8000'

[[ -z "${FRAPPE_SOCKETIO}" ]] && FRAPPE_SOCKETIO='0.0.0.0'

[[ -z "${SOCKETIO_PORT}" ]] && SOCKETIO_PORT='9000'

[[ -z "${HTTP_TIMEOUT}" ]] && HTTP_TIMEOUT='120'

[[ -z "${UPSTREAM_REAL_IP_ADDRESS}" ]] && UPSTREAM_REAL_IP_ADDRESS='127.0.0.1'

[[ -z "${UPSTREAM_REAL_IP_RECURSIVE}" ]] && UPSTREAM_REAL_IP_RECURSIVE='off'

[[ -z "${UPSTREAM_REAL_IP_HEADER}" ]] && UPSTREAM_REAL_IP_HEADER='X-Forwarded-For'

[[ -z "${FRAPPE_SITE_NAME_HEADER}" ]] && FRAPPE_SITE_NAME_HEADER="\$host"

[[ -z "${HTTP_HOST}" ]] && HTTP_HOST="\$http_host"

[[ -z "${SKIP_NGINX_TEMPLATE_GENERATION}" ]] && SKIP_NGINX_TEMPLATE_GENERATION='0'

if [[ ${SKIP_NGINX_TEMPLATE_GENERATION} == 1 ]]; then
  echo "Skipping default NGINX template generation. Please mount your own NGINX config file inside /etc/nginx/conf.d"
else
  echo "Generating default template"
  envsubst '${FRAPPE_PY}
        ${FRAPPE_PY_PORT}
        ${FRAPPE_SOCKETIO}
        ${SOCKETIO_PORT}
        ${HTTP_TIMEOUT}
        ${UPSTREAM_REAL_IP_ADDRESS}
        ${UPSTREAM_REAL_IP_RECURSIVE}
        ${FRAPPE_SITE_NAME_HEADER}
        ${HTTP_HOST}
        ${UPSTREAM_REAL_IP_HEADER}' \
    </etc/nginx/conf.d/default.conf.template >/etc/nginx/conf.d/default.conf
fi

echo "Waiting for frappe-python to be available on ${FRAPPE_PY} port ${FRAPPE_PY_PORT}"
timeout 10 bash -c 'until printf "" 2>>/dev/null >>/dev/tcp/$0/$1; do sleep 1; done' ${FRAPPE_PY} ${FRAPPE_PY_PORT}
echo "Frappe-python available on ${FRAPPE_PY} port ${FRAPPE_PY_PORT}"
echo "Waiting for frappe-socketio to be available on ${FRAPPE_SOCKETIO} port ${SOCKETIO_PORT}"
timeout 10 bash -c 'until printf "" 2>>/dev/null >>/dev/tcp/$0/$1; do sleep 1; done' ${FRAPPE_SOCKETIO} ${SOCKETIO_PORT}
echo "Frappe-socketio available on ${FRAPPE_SOCKETIO} port ${SOCKETIO_PORT}"

exec "$@"
