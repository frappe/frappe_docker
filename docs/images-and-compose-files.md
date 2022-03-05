# Images

There's 4 images that you can find in `/images` directory:

- `bench`. It is used for development. [Learn more how to start development](../development/README.md).
- `nginx`. This image contains JS and CSS assets. Container using this image also routes incoming requests using [nginx](https://www.nginx.com).
- `socketio`. Container using this image processes realtime websocket requests using [Socket.IO](https://socket.io).
- `worker`. Multi-purpose Python backend. Runs [Werkzeug server](https://werkzeug.palletsprojects.com/en/2.0.x/) with [gunicorn](https://gunicorn.org), queues (via `bench worker`), or schedule (via `bench schedule`).

> `nginx`, `socketio` and `worker` images — everything we need to be able to run all processes that Frappe framework requires (take a look at [Bench Procfile reference](https://frappeframework.com/docs/v13/user/en/bench/resources/bench-procfile)). We follow [Docker best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#decouple-applications) and split these processes to different containers.

> ERPNext images don't have their own Dockerfiles. We use [multi-stage builds](https://docs.docker.com/develop/develop-images/multistage-build/) and [Docker Buildx](https://docs.docker.com/engine/reference/commandline/buildx/) to reuse as much things as possible and make our builds more efficient.

# Compose files

After building the images we have to run the containers. The best and simplest way to do this is to use [compose files](https://docs.docker.com/compose/compose-file/).

We have one main compose file, `compose.yaml`. Services described, networking, volumes are also handled there.

## Services

All services are described in `compose.yaml`

- `configurator`. Updates `common_site_config.json` so Frappe knows how to access db and redis. It is executed on every `docker-compose up` (and exited immediately). Other services start after this container exits successfully.
- `backend`. [Werkzeug server](https://werkzeug.palletsprojects.com/en/2.0.x/).
- `db`. Optional service that runs [MariaDB](https://mariadb.com) if you also use `overrides/compose.mariadb.yaml` or [Postgres](https://www.postgresql.org) if you also use `overrides/compose.postgres.yaml`.
- `redis`. Optional service that runs [Redis](https://redis.io) server with cache, [Socket.IO](https://socket.io) and queues data.
- `frontend`. [nginx](https://www.nginx.com) server that serves JS/CSS assets and routes incoming requests.
- `proxy`. [Traefik](https://traefik.io/traefik/) proxy. It is here for complicated setups or HTTPS override (with `overrides/compose.https.yaml`).
- `websocket`. Node server that runs [Socket.IO](https://socket.io).
- `queue-short`, `queue-default`, `queue-long`. Python servers that run job queues using [rq](https://python-rq.org).
- `scheduler`. Python server that runs tasks on schedule using [schedule](https://schedule.readthedocs.io/en/stable/).

## Overrides

We have several [overrides](https://docs.docker.com/compose/extends/):

- `overrides/compose.proxy.yaml`. Adds traefik proxy to setup.
- `overrides/compose.noproxy.yaml`. Publishes `frontend` ports directly without any proxy.
- `overrides/compose.erpnext.yaml`. Replaces all Frappe images with ERPNext ones. ERPNext images are built on top of Frappe ones, so it is safe to replace them.
- `overrides/compose.https.yaml`. Automatically sets up Let's Encrypt certificate and redirects all requests to directed to http, to https.
- `overrides/compose.mariadb.yaml`. Adds `db` service and sets its image to MariaDB.
- `overrides/compose.postgres.yaml`. Adds `db` service and sets its image to Postgres. Note that ERPNext currently doesn't support Postgres.
- `overrides/compose.redis.yaml`. Adds `redis` service and sets its image to `redis`.
- `overrides/compose.swarm.yaml`. Workaround override for generating swarm stack.

It is quite simple to run overrides. All we need to do is to specify compose files that should be used by docker-compose. For example, we want ERPNext:

```bash
# Point to main compose file (compose.yaml) and add one more.
docker-compose -f compose.yaml -f overrides/compose.erpnext.yaml config
```

That's it! Of course, we also have to setup `.env` before all of that, but that's not the point.

## Configuration

We use environment variables to configure our setup. docker-compose uses variables from `.env` file. To get started, copy `example.env` to `.env`.

### `FRAPPE_VERSION`

Frappe framework release. You can find all releases [here](https://github.com/frappe/frappe/releases).

### `DB_PASSWORD`

Password for MariaDB (or Postgres) database.

### `DB_HOST`

Hostname for MariaDB (or Postgres) database. Set only if external service for database is used.

### `DB_PORT`

Port for MariaDB (3306) or Postgres (5432) database. Set only if external service for database is used.

### `REDIS_CACHE`

Hostname for redis server to store cache. Set only if external service for redis is used.

### `REDIS_QUEUE`

Hostname for redis server to store queue data. Set only if external service for redis is used.

### `REDIS_SOCKETIO`

Hostname for redis server to store socketio data. Set only if external service for redis is used.

### `ERPNEXT_VERSION`

ERPNext [release](https://github.com/frappe/frappe/releases). This variable is required if you use ERPNext override.

### `LETSENCRYPT_EMAIL`

Email that used to register https certificate. This one is required only if you use HTTPS override.

### `FRAPPE_SITE_NAME_HEADER`

This environment variable is not required. Default value is `$$host` which resolves site by host. For example, if your host is `example.com`, site's name should be `example.com`, or if host is `127.0.0.1` (local debugging), it should be `127.0.0.1` This variable allows to override described behavior. Let's say you create site named `mysite` and do want to access it by `127.0.0.1` host. Than you would set this variable to `mysite`.

There is other variables not mentioned here. They're somewhat internal and you don't have to worry about them except you want to change main compose file.
