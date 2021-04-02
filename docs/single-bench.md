# Single Bench

This setup starts traefik service as part of single docker-compose project. It is quick to get started locally or on production for a single server with single deployment.

This is not suitable when multiple services are installed on cluster with shared proxy/router, database, cache etc.

Make sure you've cloned this repository and switch to the directory before executing following commands.

## Setup Environment Variables

Copy the example docker environment file to `.env`:

For local setup

```sh
cp env-local .env
```

For production

```sh
cp env-production .env

```

To get started, copy the existing `env-local` or `env-production` file to `.env`. By default, the file will contain the following variables:

- `ERPNEXT_VERSION=edge`
    - In this case, `edge` corresponds to `develop`. To setup any other version, you may use the branch name or version specific tags. (eg. v13.0.0, version-12, v11.1.15, v11).
- `FRAPPE_VERSION=edge`
    - In this case, `edge` corresponds to `develop`. To setup any other version, you may use the branch name or version specific tags. (eg. v13.0.0, version-12, v11.1.15, v11).
- `MARIADB_HOST=mariadb`
    - Sets the hostname to `mariadb`. This is required if the database is managed by the containerized MariaDB instance.
- `MYSQL_ROOT_PASSWORD=admin`
    - Bootstraps a MariaDB container with this value set as the root password. If a managed MariaDB instance is used, there is no need to set the password here.
    - In case of a separately managed database setups, set the value to the database's hostname/IP/domain.
- `SITE_NAME=erp.example.com`
    - Creates this site after starting all services and installs ERPNext. Site name must be resolvable by users machines and the ERPNext components.  e.g. `erp.example.com` or `mysite.localhost`.
- ``SITES=`erp.example.com` ``
    - List of sites that are part of the deployment "bench" Each site is separated by a comma(,) and quoted in backtick (`). By default site created by ``SITE_NAME`` variable is added here.
    - If LetsEncrypt is being setup, make sure that the DNS for all the site's domains correctly point to the current instance.
- `DB_ROOT_USER=root`
    - MariaDB root username
- `ADMIN_PASSWORD=admin`
    - Password for the `Administrator` user, credentials after install `Administrator:$ADMIN_PASSWORD`.
- `INSTALL_APPS=erpnext`
    - Apps to install, the app must be already in the container image, to install other application read the [instructions on installing custom apps](./custom-apps-for-production.md).
- `LETSENCRYPT_EMAIL=email@example.com`
    - Email for LetsEncrypt expiry notification. This is only required if you are setting up LetsEncrypt.
- `ENTRYPOINT_LABEL=traefik.http.routers.erpnext-nginx.entrypoints=websecure`
    - Related to the traefik configuration, says all traffic from outside should come from HTTP or HTTPS, for local development should be web, for production websecure. if redirection is needed, read below.
- `CERT_RESOLVER_LABEL=traefik.http.routers.erpnext-nginx.tls.certresolver=myresolver`
    - Which traefik resolver to use to get TLS certificate, sets `erpnext.local.no-cert-resolver` for local setup.
- ``HTTPS_REDIRECT_RULE_LABEL=traefik.http.routers.http-catchall.rule=hostregexp(`{host:.+}`) ``
    - Related to the traefik https redirection configuration, sets `erpnext.local.no-redirect-rule` for local setup.
- `HTTPS_REDIRECT_ENTRYPOINT_LABEL=traefik.http.routers.http-catchall.entrypoints=web`
    - Related to the traefik https redirection configuration, sets `erpnext.local.no-entrypoint` for local setup.
- `HTTPS_REDIRECT_MIDDLEWARE_LABEL=traefik.http.routers.http-catchall.middlewares=redirect-to-https`
    - Related to the traefik https redirection configuration, sets `erpnext.local.no-middleware` for local setup.
- `HTTPS_USE_REDIRECT_MIDDLEWARE_LABEL=traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https`
    - Related to the traefik https redirection configuration, sets `erpnext.local-no-redirect-middleware` for local setup.

Notes:

- `AUTO_MIGRATE` variable is set to `1` by default. It checks if there is semver bump or git hash change in case of develop branch and automatically migrates the sites on container start up.
- It is good practice to use image tag for specific version instead of latest. e.g `frappe-socketio:v12.5.1`, `erpnext-nginx:v12.7.1`.

## Start containers

Execute the following command:

```sh
docker-compose --project-name <project-name> up -d
```

Make sure to replace `<project-name>` with the desired name you wish to set for the project.

Notes:

- If it is the first time running and site is being initialized, *it can take multiple minutes for the site to be up*. Monitor `site-creator` container logs to check progress. Use command `docker logs <project-name>_site-creator_1 -f`
- After the site is ready the username is `Administrator` and the password is `$ADMIN_PASSWORD`
- The local deployment is for testing and REST API development purpose only
- A complete development environment is available [here](../development)

## Docker containers

The docker-compose file contains following services:

* traefik: manages letsencrypt
    * volume: cert-vol
* redis-cache: cache store
    * volume: redis-cache-vol
* redis-queue: used by workers
    * volume: redis-queue-vol
* redis-socketio: used by socketio service
    * volume: redis-socketio-vol
* mariadb: main database
    * volume: mariadb-vol
* erpnext-nginx: serves static assets and proxies web request to the appropriate container, allowing to offer all services on the same port.
    * volume: assets-vol and sites-vol
* erpnext-python: main application code
    * volume: sites-vol and sites-vol
* frappe-socketio: enables realtime communication to the user interface through websockets
    * volume: sites-vol
* erpnext-worker-default: background runner
    * volume: sites-vol
* erpnext-worker-short: background runner for short-running jobs
    * volume: sites-vol
* erpnext-worker-long: background runner for long-running jobs
    * volume: sites-vol
* erpnext-schedule
    * volume: sites-vol
* site-creator: run once container to create new site.
    * volume: sites-vol

## Updating and Migrating Sites

Switch to the root of the `frappe_docker` directory before running the following commands:

```sh
# Update environment variables ERPNEXT_VERSION and FRAPPE_VERSION
nano .env

# Pull new images
docker-compose pull

# Restart containers
docker-compose --project-name <project-name> up -d
```
