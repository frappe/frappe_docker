# Images

There are 3 images that you can find in `/images` directory:

- `bench`. It is used for development. [Learn more how to start development](development.md).
- `production`.
  - Multi-purpose Python backend. Runs [Werkzeug server](https://werkzeug.palletsprojects.com/en/2.0.x/) with [gunicorn](https://gunicorn.org), queues (via `bench worker`), or schedule (via `bench schedule`).
  - Contains JS and CSS assets and routes incoming requests using [nginx](https://www.nginx.com).
  - Processes realtime websocket requests using [Socket.IO](https://socket.io).
- `custom`. It is used to build bench using `apps.json` file set with `--apps_path` during bench initialization. `apps.json` is a json array. e.g. `[{"url":"{{repo_url}}","branch":"{{repo_branch}}"}]`

Image has everything we need to be able to run all processes that Frappe framework requires (take a look at [Bench Procfile reference](https://frappeframework.com/docs/v14/user/en/bench/resources/bench-procfile)). We follow [Docker best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#decouple-applications) and split these processes to different containers.

> We use [multi-stage builds](https://docs.docker.com/develop/develop-images/multistage-build/) and [Docker Buildx](https://docs.docker.com/engine/reference/commandline/buildx/) to reuse as much things as possible and make our builds more efficient.

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
- `queue-short`, `queue-long`. Python servers that run job queues using [rq](https://python-rq.org).
- `scheduler`. Python server that runs tasks on schedule using [schedule](https://schedule.readthedocs.io/en/stable/).

## Overrides

We have several [overrides](https://docs.docker.com/compose/extends/):

- `overrides/compose.proxy.yaml`. Adds traefik proxy to setup.
- `overrides/compose.noproxy.yaml`. Publishes `frontend` ports directly without any proxy.
- `overrides/compose.https.yaml`. Automatically sets up Let's Encrypt certificate and redirects all requests to directed to http, to https.
- `overrides/compose.mariadb.yaml`. Adds `db` service and sets its image to MariaDB.
- `overrides/compose.postgres.yaml`. Adds `db` service and sets its image to Postgres. Note that ERPNext currently doesn't support Postgres.
- `overrides/compose.redis.yaml`. Adds `redis` service and sets its image to `redis`.

It is quite simple to run overrides. All we need to do is to specify compose files that should be used by docker-compose. For example, we want ERPNext:

```bash
# Point to main compose file (compose.yaml) and add one more.
docker-compose -f compose.yaml -f overrides/compose.redis.yaml config
```

⚠ Make sure to use docker-compose v2 (run `docker-compose -v` to check). If you want to use v1 make sure the correct `$`-signs as they get duplicated by the `config` command!

That's it! Of course, we also have to setup `.env` before all of that, but that's not the point.

Check [environment variables](environment-variables.md) for more.
