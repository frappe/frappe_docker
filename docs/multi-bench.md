# Multi bench

This setup separates all services such that only required ones can be deployed.

This is suitable when multiple services are installed on cluster with shared proxy/router, database, cache etc.

Make sure you've cloned this repository and switch to the directory before executing following commands.

## Setup Environment Variables

Copy the example docker environment file to `.env`:

```sh
cp env-example .env
```

To get started, copy the existing `env-example` file to `.env`. By default, the file will contain the following variables:

- `VERSION=edge`
    - In this case, `edge` corresponds to `develop`. To setup any other version, you may use the branch name or version specific tags. (eg. v13.0.0, version-12, v11.1.15, v11)
- `MYSQL_ROOT_PASSWORD=admin`
    - Bootstraps a MariaDB container with this value set as the root password. If a managed MariaDB instance is used, there is no need to set the password here.
- `MARIADB_HOST=mariadb`
    - Sets the hostname to `mariadb`. This is required if the database is managed by the containerized MariaDB instance.
    - In case of a separately managed database setups, set the value to the database's hostname/IP/domain.
- `SITES=site1.domain.com,site2.domain.com`
    - List of sites that are part of the deployment "bench" Each site is separated by a comma(,).
    - If LetsEncrypt is being setup, make sure that the DNS for all the site's domains correctly point to the current instance.
- `LETSENCRYPT_EMAIL=your.email@your.domain.com`
    - Email for LetsEncrypt expiry notification. This is only required if you are setting up LetsEncrypt.

Notes:

- docker-compose-erpnext.yml and docker-compose-frappe.yml set `AUTO_MIGRATE` environment variable to `1`.
- `AUTO_MIGRATE` checks if there is semver bump or git hash change in case of develop branch and automatically migrates the sites on container start up.
- It is good practice to use image tag for specific version instead of latest. e.g `frappe-socketio:v12.5.1`, `erpnext-nginx:v12.7.1`.

## Local deployment for testing

For trying out locally or to develop apps using ERPNext REST API port 80 must be published.
Following command will start the needed containers and expose ports.

For Erpnext:

```sh
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/erpnext-publish.yml \
    up -d
```

For Frappe:

```sh
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-frappe.yml \
    -f installation/frappe-publish.yml \
    up -d
```

Make sure to replace `<project-name>` with the desired name you wish to set for the project.

Notes:

- New site (first site) needs to be added after starting the services.
- The local deployment is for testing and REST API development purpose only
- A complete development environment is available [here](../development)
- The site names are limited to patterns matching \*.localhost by default
- Additional site name patterns can be added by editing /etc/hosts of your host machine

## Deployment for production

### Setup Letsencrypt Nginx Proxy Companion

Letsencrypt Nginx Proxy Companion can optionally be setup to provide SSL. This is recommended for instances accessed over the internet.

Your DNS will need to be configured correctly for Letsencrypt to verify your domain.

To setup the proxy companion, run the following commands:

```sh
cd $HOME
git clone https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion.git
cd docker-compose-letsencrypt-nginx-proxy-companion
cp .env.sample .env
./start.sh
```

It will create the required network and configure containers for Letencrypt ACME.

For more details, see the [Letsencrypt Nginx Proxy Companion github repo](https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion). Letsencrypt Nginx Proxy Companion github repo works by automatically proxying to containers with the `VIRTUAL_HOST` environmental variable.

Notes:

- `SITES` variables from `env-example` is set as `VIRTUAL_HOST`
- `LETSENCRYPT_EMAIL` variables from `env-example` is used as it is.
- This is simple nginx + letsencrypt solution. Any other solution can be setup. Above two variables can be re-used or removed in case any other reverse-proxy is used.

### Start Frappe/ERPNext Services

To start the Frappe/ERPNext services for production, run the following command:

```sh
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    up -d
```

Make sure to replace `<project-name>` with any desired name you wish to set for the project.

Notes:

- Use `docker-compose-frappe.yml` in case you need only Frappe without ERPNext.
- New site (first site) needs to be added after starting the services.

## Docker containers

This repository contains the following docker-compose files, each one containing the described images:
* docker-compose-common.yml
    * redis-cache
        * volume: redis-cache-vol
    * redis-queue
        * volume: redis-queue-vol
    * redis-socketio
        * volume: redis-socketio-vol
    * mariadb: main database
        * volume: mariadb-vol
* docker-compose-erpnext.yml
    * erpnext-nginx: serves static assets and proxies web request to the appropriate container, allowing to offer all services on the same port.
        * volume: assets-vol
    * erpnext-python: main application code
    * frappe-socketio: enables realtime communication to the user interface through websockets
    * frappe-worker-default: background runner
    * frappe-worker-short: background runner for short-running jobs
    * frappe-worker-long: background runner for long-running jobs
    * frappe-schedule

* docker-compose-frappe.yml
    * frappe-nginx: serves static assets and proxies web request to the appropriate container, allowing to offer all services on the same port.
        * volume: assets-vol, sites-vol
    * erpnext-python: main application code
        * volume: sites-vol
    * frappe-socketio: enables realtime communication to the user interface through websockets
        * volume: sites-vol
    * frappe-worker-default: background runner
        * volume: sites-vol
    * frappe-worker-short: background runner for short-running jobs
        * volume: sites-vol
    * frappe-worker-long: background runner for long-running jobs
        * volume: sites-vol
    * frappe-schedule
        * volume: sites-vol

* docker-compose-networks.yml: this yaml define the network to communicate with *Letsencrypt Nginx Proxy Companion*.

* erpnext-publish.yml: this yml extends erpnext-nginx service to publish port 80, can only be used with docker-compose-erpnext.yml

* frappe-publish.yml: this yml extends frappe-nginx service to publish port 80, can only be used with docker-compose-frappe.yml

## Updating and Migrating Sites

Switch to the root of the `frappe_docker` directory before running the following commands:

```sh
# Update environment variable VERSION
nano .env

# Pull new images
docker-compose \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    pull

# Restart containers
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    up -d

docker run \
    -e "MAINTENANCE_MODE=1" \
    -v <project-name>_sites-vol:/home/frappe/frappe-bench/sites \
    --network <project-name>_default \
    frappe/erpnext-worker:$VERSION migrate
```