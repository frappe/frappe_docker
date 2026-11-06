---
title: Single Compose Setup
---

# Single Compose Setup

This reference describes the services and volumes in the disposable `pwd.yml` demo. For commands to run it, see [Getting started](../getting-started.md#1-quick-test-5-minutes). It is intended for short-lived evaluation, not production or development.

This setup is a very simple single compose file that does everything to start required services and a frappe-bench. It is used to start play with docker instance with a site. The file is located in the root of repo and named `pwd.yml`.

## Services

### frappe-bench components

- backend, serves gunicorn backend
- frontend, serves static assets through nginx frontend reverse proxies websocket and gunicorn.
- queue-long, long default and short rq worker.
- queue-short, default and short rq worker.
- schedule, event scheduler.
- websocket, socketio websocket for realtime communication.

### Run once configuration

- configurator, configures `common_site_config.json` to set db and redis hosts.
- create-site, creates one site to serve as default site for the frappe-bench.

### Service dependencies

- db, mariadb, container with frappe specific configuration.
- redis-cache, redis for cache data.
- redis-queue, redis for rq data and pub/sub.

## Volumes

- sites: Volume for bench data. Common config, all sites, all site configs and site files will be stored here.
- logs: Volume for bench logs. all process logs are dumped here. No need to mount it. Each container will create a temporary volume for logs if not specified.

## Site routing defaults

For a production deployment, use the base `compose.yaml` and overrides, as shown in [Set up a single server with Traefik](../11-how-to/15-single-server-traefik.md).

This serves only site called `frontend` through the nginx. `FRAPPE_SITE_NAME_HEADER` is set to `frontend` and a default site called `frontend` is created.

Change the `$$host` will allow container to accept any host header and serve that site. To escape `$` in compose yaml use it like `$$`. To unset default site remove `currentsite.txt` file from `sites` directory.
