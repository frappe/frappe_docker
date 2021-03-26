List of environment variables for containers

### frappe-worker and erpnext-worker

Following environment variables are set into sites volume as `common_site_config.json`. It means once the file is created in volume, the variables won't have any effect, you need to edit the common_site_config.json to update the configuration

- `DB_HOST`: MariaDB host, domain name or ip address.
- `DB_PORT`: MariaDB port.
- `REDIS_CACHE`: Redis cache host, domain name or ip address.
- `REDIS_QUEUE`: Redis queue host, domain name or ip address.
- `REDIS_SOCKETIO`: Redis queue host, domain name or ip address.
- `SOCKETIO_PORT: `: Port on which the SocketIO should start.
- `WORKER_CLASS`: Optionally set gunicorn worker-class. Supports gevent only, defaults to gthread.

### frappe-nginx and erpnext-nginx

These variables are set on every container start. Change in these variables will reflect on every container start.

- `FRAPPE_PY`: Gunicorn host to reverse proxy. Default: 0.0.0.0
- `FRAPPE_PY_PORT`: Gunicorn port to reverse proxy. Default: 8000
- `FRAPPE_SOCKETIO`: SocketIO host to reverse proxy. Default: 0.0.0.0
- `SOCKETIO_PORT`: SocketIO port to reverse proxy. Default: 9000
- `HTTP_TIMEOUT`: Nginx http timeout. Default: 120
- `UPSTREAM_REAL_IP_ADDRESS `: The trusted address (or ip range) of upstream proxy servers. If set, this will tell nginx to trust the X-Forwarded-For header from these proxy servers in determining the real IP address of connecting clients. Default: 127.0.0.1
- `UPSTREAM_REAL_IP_RECURSIVE`: When set to `on`, this will tell nginx to not just look to the last upstream proxy server in determining the real IP address. Default: off
- `UPSTREAM_REAL_IP_HEADER`: Set this to the header name sent by your upstream proxy server to indicate the real IP of connecting clients. Default: X-Forwarded-For
- `FRAPPE_SITE_NAME_HEADER`: NGINX `X-Frappe-Site-Name` header in the HTTP request which matches a site name. Default: `$host`
- `HTTP_HOST`: NGINX `Host` header in the HTTP request which matches a site name. Default: `$http_host`
- `SKIP_NGINX_TEMPLATE_GENERATION`: When set to `1`, this will not generate a default NGINX configuration. The config file must be mounted inside the container (`/etc/nginx/conf.d`) by the user in this case. Default: `0`

### frappe-socketio

This container takes configuration from `common_site_config.json` which is already created by erpnext gunicorn container. It doesn't use any environment variables.
