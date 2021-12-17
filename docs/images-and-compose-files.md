# Images

There's 4 images that you can find in `/build` directory:

- `bench`. It is used for development. [Learn more how to start development](../development/README.md).
- `nginx`. This image contains JS and CSS assets. Container using this image also routes incoming requests using [nginx](https://www.nginx.com).
- `socketio`. Container using this image processes realtime websocket requests using [Socket.IO](https://socket.io).
- `worker`. Multi-purpose Python backend. Runs [Werkzeug server](https://werkzeug.palletsprojects.com/en/2.0.x/) with [gunicorn](https://gunicorn.org), queues (via `bench worker`), or schedule (via `bench schedule`).

> `nginx`, `socketio` and `worker` images — everything we need to be able to run all processes that Frappe framework requires (take a look at [Bench Procfile reference](https://frappeframework.com/docs/v13/user/en/bench/resources/bench-procfile)). We follow [Docker best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#decouple-applications) and split these processes to different containers.

> ERPNext images don't have their own Dockerfiles. We use [multi-stage builds](https://docs.docker.com/develop/develop-images/multistage-build/) and [Docker Buildx](https://docs.docker.com/engine/reference/commandline/buildx/) to reuse as much things as possible and make are builds more efficient.

# Compose files

After building the images we have to run the containers. The best and simplest way to do this is to use [compose files](https://docs.docker.com/compose/compose-file/).

We have one main compose file, `compose.yaml`. Services described, networking, volumes are also handled there.

Services that the file contains:

- `configurator`. Updates `common_site_config.json` so Frappe knows how to access db and redis. It is executed on every `docker-compose up` (and exited immediately). Other services start after this container exits successfully.
- `backend`. [Werkzeug server](https://werkzeug.palletsprojects.com/en/2.0.x/).
- `db`. [MariaDB](https://mariadb.com), can be overwritten with [Postgres](https://www.postgresql.org) if you also use `overrides/compose.postgres.yaml`.
- `redis`. [Redis](https://redis.io) server with cache, [Socket.IO](https://socket.io) and queues data.
- `frontend`. [nginx](https://www.nginx.com) server that serves JS/CSS assets and routes incoming requests.
- `proxy`. [Traefik](https://traefik.io/traefik/) proxy. It is here for complicated setups or HTTPS override (with `overrides/compose.https.yaml`).
- `websocket`. Node server that runs [Socket.IO](https://socket.io).
- `queue-short`, `queue-default`, `queue-long`. Python servers that run job queues using [rq](https://python-rq.org).
- `scheduler`. Python server that runs tasks on schedule using [schedule](https://schedule.readthedocs.io/en/stable/).

Also, we have several [overrides](https://docs.docker.com/compose/extends/).

- `overrides/compose.erpnext.yaml`. Replaces all Frappe images with ERPNext ones. ERPNext images are built on top of Frappe ones, so it is safe to replace them.
- `overrides/compose.https.yaml`. Automatically sets up Let's Encrypt certificate and redirects all requests to directed to http, to https.
- `overrides/compose.postgres.yaml`. Replaces `db` service's image from MariaDB to Postgres. Note that ERPNext currently doesn't support Postgres.

It is quite simple to run overrides. All we need to do is to specify compose files that should be used by docker-compose. For example, we want ERPNext:

```bash
# Point to main compose file (compose.yaml) and add one more.
docker-compose -f compose.yaml -f overrides/compose.erpnext.yaml
```

That's it! Of course, we also have to setup `.env` before all of that, but that's not the point.
