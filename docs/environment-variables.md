List of environment variables for containers

### frappe-worker and erpnext-worker

Following environment variables are set into sites volume as `common_site_config.json`. It means once the file is created in volume, the variables won't have any effect, you need to edit the common_site_config.json to update the configuration

- `DB_HOST`: MariaDB host, domain name or ip address.
- `DB_PORT`: MariaDB port.
- `REDIS_CACHE`: Redis cache host, domain name or ip address.
- `REDIS_QUEUE`: Redis queue host, domain name or ip address.
- `REDIS_SOCKETIO`: Redis queue host, domain name or ip address.
- `SOCKETIO_PORT: `: Port on which the SocketIO should start.

### frappe-nginx and erpnext-nginx

These variables are set on every container start. Change in these variables will reflect on every container start.

- `FRAPPE_PY`: Gunicorn host to reverse proxy. Default: 0.0.0.0
- `FRAPPE_PY_PORT`: Gunicorn port to reverse proxy. Default: 8000
- `FRAPPE_SOCKETIO`: SocketIO host to reverse proxy. Default: 0.0.0.0
- `SOCKETIO_PORT`: SocketIO port to reverse proxy. Default: 9000
- `HTTP_TIMEOUT`: Nginx http timeout. Default: 120

### frappe-socketio

This container takes configuration from `common_site_config.json` which is already created by erpnext gunicorn container. It doesn't use any environment variables.
