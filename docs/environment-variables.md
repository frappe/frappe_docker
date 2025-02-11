## Environment Variables

All of the commands are directly passed to container as per type of service. Only environment variables used in image are for `nginx-entrypoint.sh` command. They are as follows:

- `BACKEND`: Set to `{host}:{port}`, defaults to `0.0.0.0:8000`
- `SOCKETIO`: Set to `{host}:{port}`, defaults to `0.0.0.0:9000`
- `UPSTREAM_REAL_IP_ADDRESS`: Set Nginx config for [ngx_http_realip_module#set_real_ip_from](http://nginx.org/en/docs/http/ngx_http_realip_module.html#set_real_ip_from), defaults to `127.0.0.1`
- `UPSTREAM_REAL_IP_HEADER`: Set Nginx config for [ngx_http_realip_module#real_ip_header](http://nginx.org/en/docs/http/ngx_http_realip_module.html#real_ip_header), defaults to `X-Forwarded-For`
- `UPSTREAM_REAL_IP_RECURSIVE`: Set Nginx config for [ngx_http_realip_module#real_ip_recursive](http://nginx.org/en/docs/http/ngx_http_realip_module.html#real_ip_recursive) Set defaults to `off`
- `FRAPPE_SITE_NAME_HEADER`: Set proxy header `X-Frappe-Site-Name` and serve site named in the header, defaults to `$host`, i.e. find site name from host header. More details [below](#frappe_site_name_header)
- `PROXY_READ_TIMEOUT`: Upstream gunicorn service timeout, defaults to `120`
- `CLIENT_MAX_BODY_SIZE`: Max body size for uploads, defaults to `50m`

To bypass `nginx-entrypoint.sh`, mount desired `/etc/nginx/conf.d/default.conf` and run `nginx -g 'daemon off;'` as container command.

## Configuration

We use environment variables to configure our setup. docker-compose uses variables from the `environment:` section of the services defined within and the`.env` file, if present. Variables defined in the `.env` file are referenced via `${VARIABLE_NAME}` within the docker-compose `.yml` file. `example.env` contains a non-exhaustive list of possible configuration variables. To get started, copy `example.env` to `.env`.

### `FRAPPE_VERSION`

Frappe framework release. You can find all releases [here](https://github.com/frappe/frappe/releases).

### `DB_PASSWORD`

Password for MariaDB (or Postgres) database.

### `DB_HOST`

Hostname for MariaDB (or Postgres) database. Set only if external service for database is used or the container can not be reached by its service name (db) by other containers.

### `DB_PORT`

Port for MariaDB (3306) or Postgres (5432) database. Set only if external service for database is used.

### `REDIS_CACHE`

Hostname for redis server to store cache. Set only if external service for redis is used or the container can not be reached by its service name (redis-cache) by other containers.

### `REDIS_QUEUE`

Hostname for redis server to store queue data and socketio. Set only if external service for redis is used or the container can not be reached by its service name (redis-queue) by other containers.

### `ERPNEXT_VERSION`

ERPNext [release](https://github.com/frappe/erpnext/releases). This variable is required if you use ERPNext override.

### `LETSENCRYPT_EMAIL`

Email that used to register https certificate. This one is required only if you use HTTPS override.

### `FRAPPE_SITE_NAME_HEADER`

This environment variable is not required. Default value is `$$host` which resolves site by host. For example, if your host is `example.com`, site's name should be `example.com`, or if host is `127.0.0.1` (local debugging), it should be `127.0.0.1` This variable allows to override described behavior. Let's say you create site named `mysite` and do want to access it by `127.0.0.1` host. Than you would set this variable to `mysite`.

There is other variables not mentioned here. They're somewhat internal and you don't have to worry about them except you want to change main compose file.
