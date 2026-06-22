# Architecture

## Executive View

The current runtime is a single-host Docker Compose demonstration stack. Frappe and ERPNext use the same application image and are separated into service roles.

## Runtime Components

- `frontend`: Nginx entry point exposed on port 8080.
- `backend`: Frappe/Gunicorn HTTP application.
- `websocket`: Socket.IO real-time channel.
- `queue-short` and `queue-long`: background workers.
- `scheduler`: periodic-job scheduler.
- `configurator`: generates shared site configuration.
- `create-site`: creates the demo site and installs ERPNext.
- `db`: MariaDB 11.8.
- `redis-cache` and `redis-queue`: cache and job queue.

## Runtime Flow

```text
Browser :8080 -> frontend -> backend -> MariaDB
                     |          |
                     |          +-> Redis cache/queue -> workers
                     +-> websocket -> Redis queue
```

## Persistence and Security

Named volumes provide local persistence for database, sites, and logs. They are not a backup or disaster-recovery strategy. The demo uses HTTP, default credentials, and unauthenticated Redis. No production secrets manager, identity provider, WAF, high-availability layer, or centralized observability stack is configured.

## Application Architecture

The running image contains 637 ERPNext and 305 Frappe DocType JSON definitions, 184 ERPNext report definitions, and a large standard application/test surface. The live site has no product-owned custom app. Configuration held only in the database is not a controlled software delivery model.

## Testing

Upstream tests cover infrastructure connectivity, endpoints, assets, file security headers, backup mechanics, HTTPS overrides, and PostgreSQL site creation. No product-specific tests validate the local business processes, permissions, approvals, accounting outcomes, or integrations.
