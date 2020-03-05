## Getting Started

The templates in this repository will help deploy Frappe/ERPNext docker in a production environment.

This docker installation takes care of the following:

* Setting up the desired version of Frappe/ERPNext.
* Setting up all the system requirements: eg. MariaDB, Node, Redis.
* [OPTIONAL] Configuring networking for remote access and setting up LetsEncrypt

## Deployment

### Setting up Pre-requisites

This repository requires Docker and Git to be setup on the instance to be used.

### Cloning the repository and preliminary steps

Clone this repository somewhere in your system:

```sh
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

Copy the example docker environment file to `.env`:

```sh
cp installation/env-example installation/.env
```

Make a directory for sites:

```sh
mkdir installation/sites
```

### Setup Environment Variables

To get started, copy the existing `env-example` file to `.env` inside the `installation` directory. By default, the file will contain the following variables:

- `VERSION=edge`
    - In this case, `edge` corresponds to `develop`. To setup any other version, you may use the branch name or version specific tags. (eg. version-12, v11.1.15, v11)
- `MYSQL_ROOT_PASSWORD=admin`
    - Bootstraps a MariaDB container with this value set as the root password. If a managed MariaDB instance is to be used, there is no need to set the password here.
- `MARIADB_HOST=mariadb`
    - Sets the hostname to `mariadb`. This is required if the database is managed with the containerized MariaDB instance.
    - In case of a separately managed database setup, set the value to the database's hostname/IP/domain.
- `SITES=site1.domain.com,site2.domain.com`
    - List of sites that are part of the deployment "bench". Each site is separated by a comma(,).
    - If LetsEncrypt is being setup, make sure that the DNS for all the site's domains are pointing to the current instance.
- `LETSENCRYPT_EMAIL=your.email@your.domain.com`
    - Email for LetsEncrypt expiry notification. This is only required if you are setting up LetsEncrypt.


### Deployment for local development

To start the Frappe/ERPNext services for production, run the following command:

For Erpnext:


```sh
docker-compose \ 
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation run --publish 80:80 erpnext-nginx
```

For Frappe:
```sh
docker-compose \ 
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-frappe.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation run --publish 80:80 frappe-nginx
```

Make sure to replace `<project-name>` with any desired name you wish to set for the project.

Note: this command does not run docker-compose in daemon mode. You will need to keep the terminal window open.
Note: the local deployment is for testing only. The site names are limited to patterns matching \*.localhost.


### Deployment for production

#### Setup Letsencrypt Nginx Proxy Companion



Letsencrypt Nginx Proxy Companion can optionally be setup to provide SSL. This is recommended for istances accessed over the internet. 

Your DNS will need to be configured correctly in order for Letsencrypt to verify your domain.

To setup the proxy companion, run the following commands:

```sh
cd $HOME
git clone https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion.git
cd docker-compose-letsencrypt-nginx-proxy-companion
cp .env.sample .env
./start.sh
```

For more details, see: https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion
Letsencrypt Nginx Proxy Companion works by automatically proxing to containers with the `VIRTUAL_HOST` environmental variable.


#### Start Frappe/ERPNext Services

To start the Frappe/ERPNext services for production, run the following command:

```sh
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation up -d
```

Make sure to replace `<project-name>` with any desired name you wish to set for the project.
Note: use `docker-compose-frappe.yml` in case you need only Frappe without ERPNext.


### Docker containers

This repository contains the following docker-compose files each one containing the described images:
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
        * volume: assets
    * erpnext-python: main application code
    * frappe-socketio: enables realtime comunication to the user interface through websockets
    * frappe-worker-default: background runner
    * frappe-worker-short: background runner for short-running jobs
    * frappe-worker-long: background runner for long-running jobs
    * frappe-schedule

* docker-compose-frappe.yml
    * frappe-nginx: serves static assets and proxies web request to the appropriate container, allowing to offer all services on the same port. 
        * volume: assets
    * erpnext-python: main application code
    * frappe-socketio: enables realtime comunication to the user interface through websockets
    * frappe-worker-default: background runner
    * frappe-worker-short: background runner for short-running jobs
    * frappe-worker-long: background runner for long-running jobs
    * frappe-schedule

* docker-compose-networks.yml: this yml define the network to comunicate with *Letsencrypt Nginx Proxy Companion*.


### Site operations

#### Setup New Sites

Note:

- Wait for the mariadb service to start before trying to create a new site.
    - If new site creation fails, retry after the mariadb container is up and running.
    - If you're using a managed database instance, make sure that the database is running before setting up a new site.
- Use `.env` file or environment variables instead of passing secrets as command arguments.

```sh
# Create ERPNext site
docker exec -it \
    -e "SITE_NAME=$SITE_NAME" \
    -e "DB_ROOT_USER=$DB_ROOT_USER" \
    -e "MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD" \
    -e "ADMIN_PASSWORD=$ADMIN_PASSWORD" \
    -e "INSTALL_ERPNEXT=1" \
    <project-name>_erpnext-python_1 docker-entrypoint.sh new
```

Environment Variables needed:

- `SITE_NAME`: name of the new site to create.
- `DB_ROOT_USER`: MariaDB Root user. The user that can create databases.
- `MYSQL_ROOT_PASSWORD`: In case of mariadb docker container use the one set in `MYSQL_ROOT_PASSWORD` in previous steps. In case of managed database use appropriate password.
- `ADMIN_PASSWORD`: set the administrator password for new site.
- `INSTALL_ERPNEXT=1`: available only in erpnext-worker and erpnext containers. Installs ERPNext on this new site.
- `FORCE=1`: is optional variable which force installs the same site.

#### Backup Sites

Environment Variables

- `SITES` is list of sites separated by (:) colon to migrate. e.g. `SITES=site1.domain.com` or `SITES=site1.domain.com:site2.domain.com` By default all sites in bench will be backed up.
- `WITH_FILES` if set to 1, it will backup user uploaded files for the sites.

```sh
docker exec -it \
    -e "SITES=site1.domain.com:site2.domain.com" \
    -e "WITH_FILES=1" \
    <project-name>_erpnext-python_1 docker-entrypoint.sh backup
```

Backup will be available in the `sites` mounted volume.

#### Updating and Migrating Sites

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
    --project-directory installation up -d

docker exec -it \
    -e "MAINTENANCE_MODE=1" \
    <project-name>_erpnext-python_1 docker-entrypoint.sh migrate
```

## Troubleshoot

1. Remove containers and volumes, and clear redis cache:

This can be used when existing images are upgraded and migration fails.

```
# change to repo root
cd $HOME/frappe_docker

# Stop all bench containers
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation stop

# Remove redis containers
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation rm redis-cache redis-queue redis-socketio

# Clean redis volumes
docker volume rm \
    <project-name>_redis-cache-vol \
    <project-name>_redis-queue-vol \
    <project-name>_redis-socketio-vol

# Restart project
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation up -d
```

2. Clear redis cache using `docker exec` command:

In case of following error during container restarts:

```
frappe-worker-short_1    | Traceback (most recent call last):
frappe-worker-short_1    |   File "/home/frappe/frappe-bench/commands/worker.py", line 5, in <module>
frappe-worker-short_1    |     start_worker(queue, False)
frappe-worker-short_1    |   File "/home/frappe/frappe-bench/apps/frappe/frappe/utils/background_jobs.py", line 147, in start_worker
frappe-worker-short_1    |     Worker(queues, name=get_worker_name(queue)).work(logging_level = logging_level)
frappe-worker-short_1    |   File "/home/frappe/frappe-bench/env/lib/python3.7/site-packages/rq/worker.py", line 474, in work
frappe-worker-short_1    |     self.register_birth()
frappe-worker-short_1    |   File "/home/frappe/frappe-bench/env/lib/python3.7/site-packages/rq/worker.py", line 261, in register_birth
frappe-worker-short_1    |     raise ValueError(msg.format(self.name))
frappe-worker-short_1    | ValueError: There exists an active worker named '8dfe5c234085.10.short' already
```

Use commands :

```sh
# Clear the cache which is causing problem.

docker exec -it <project-name>_redis-cache_1 redis-cli FLUSHALL
docker exec -it <project-name>_redis-queue_1 redis-cli FLUSHALL
docker exec -it <project-name>_redis-socketio_1 redis-cli FLUSHALL
```

Note: Environment variables from `.env` file located at current working directory will be used.
