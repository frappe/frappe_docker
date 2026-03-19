# Container Architecture

## One image, many containers

There is no single "bench container" in Frappe Docker. The classic `bench` CLI that manages everything in a bare-metal setup is **decomposed into separate processes**, each running in its own container — all from the same image.

```
frappe-custom:v16  (one image)
    │
    ├── configurator   bench set-config ...   (runs once, then exits)
    ├── backend        gunicorn :8000         (HTTP API / page rendering)
    ├── websocket      node socketio.js :9000 (realtime / socket.io)
    ├── queue-short    bench worker --queue short,default
    ├── queue-long     bench worker --queue long,default,short
    ├── scheduler      bench schedule         (Frappe's internal cron)
    └── frontend       nginx-entrypoint.sh    (nginx reverse proxy)
```

External services (not from the Frappe image):

| Service | Image | Role |
|---|---|---|
| `db` | `mariadb:11.8` | Persistent relational storage |
| `redis-cache` | `redis:6.2-alpine` | Page/session cache (no persistence) |
| `redis-queue` | `redis:6.2-alpine` | Background job queue (persistent volume) |
| `cron` | `mcuadros/ofelia` | Docker-native cron for scheduled backups |

## Request flow

```
Browser → :8090
    └─► frontend (nginx)
            ├─► backend:8000    HTTP/REST, page rendering
            └─► websocket:9000  realtime events (socket.io)

backend / workers
    ├─► MariaDB:3306      persistent data
    ├─► redis-cache:6379  caching
    └─► redis-queue:6379  job queue
```

## The configurator

`configurator` is the most non-obvious piece. It runs **before all other services**, writes connection addresses into `common_site_config.json` (the shared `sites` volume), and then exits with code 0.

All other Frappe containers depend on it via:

```yaml
depends_on:
  configurator:
    condition: service_completed_successfully
```

This is how override files inject infrastructure addresses. For example:

```yaml
# overrides/compose.mariadb.yaml
services:
  configurator:
    environment:
      DB_HOST: db        # MariaDB container name

# overrides/compose.redis.yaml
services:
  configurator:
    environment:
      REDIS_CACHE: redis-cache:6379
      REDIS_QUEUE: redis-queue:6379
```

Without the mariadb/redis overrides the `.env` values `DB_HOST` and `REDIS_CACHE` remain empty — Frappe starts but immediately fails to connect.

## Why `compose.assets-volume.yaml` is mandatory for ERPNext

The base `compose.yaml` mounts only the `sites` volume. ERPNext requires compiled JS/CSS bundles to be accessible from **all** service containers at `/home/frappe/frappe-bench/sites/assets`.

`compose.assets-volume.yaml` adds a shared `assets` volume mounted to that path in every service. Without it nginx returns 404 for all static files.

> The `compose.yaml` source contains an explicit comment: `# ERPNext requires local assets access (Frappe does not)`.

## Redis: two instances, different durability

| Instance | Purpose | Persistence |
|---|---|---|
| `redis-cache` | Page/session/query cache | None — ephemeral |
| `redis-queue` | Background job queue | `redis-queue-data` volume |

Jobs in the queue must survive restarts, so only `redis-queue` uses a persistent volume.
