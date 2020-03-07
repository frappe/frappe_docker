## Getting Started

The templates in this repository will help deploy Frappe/ERPNext docker in a production environment.

This docker installation takes care of the following:

* Setting up the desired version of Frappe/ERPNext.
* Setting up all the system requirements: eg. MariaDB, Node, Redis.
* [OPTIONAL] Configuring networking for remote access and setting up LetsEncrypt

For docker based development refer this [README](development/README.md)

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


### Local deployment

For trying out locally or to develop apps using ERPNext ReST API port 80 must be published.
First start the containers and then run an additional command to publish port of *-nginx container.

To start and publish Frappe/ERPNext services as local api, run the following commands:

For Erpnext:

```sh
# Start services
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    --project-directory installation up -d

# Publish port
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    --project-directory installation run --publish 80:80 -d erpnext-nginx
```

For Frappe:

```sh
# Start services
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-frappe.yml \
    --project-directory installation up -d

# Publish port
docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-frappe.yml \
    --project-directory installation run --publish 80:80 -d frappe-nginx
```

Make sure to replace `<project-name>` with any desired name you wish to set for the project.

Note:
 - This command adds an additional container for frappe-nginx with published ports.
 - The local deployment is for testing and REST API development purpose only.
 - The site names are limited to patterns matching \*.localhost by default
 - Additional site name patterns can be added to /etc/hosts of desired container or host

### Deployment for production

#### Setup Letsencrypt Nginx Proxy Companion

Letsencrypt Nginx Proxy Companion can optionally be setup to provide SSL. This is recommended for instances accessed over the internet.

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
Letsencrypt Nginx Proxy Companion works by automatically proxying to containers with the `VIRTUAL_HOST` environmental variable.

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
    * frappe-socketio: enables realtime communication to the user interface through websockets
    * frappe-worker-default: background runner
    * frappe-worker-short: background runner for short-running jobs
    * frappe-worker-long: background runner for long-running jobs
    * frappe-schedule

* docker-compose-frappe.yml
    * frappe-nginx: serves static assets and proxies web request to the appropriate container, allowing to offer all services on the same port.
        * volume: assets
    * erpnext-python: main application code
    * frappe-socketio: enables realtime communication to the user interface through websockets
    * frappe-worker-default: background runner
    * frappe-worker-short: background runner for short-running jobs
    * frappe-worker-long: background runner for long-running jobs
    * frappe-schedule

* docker-compose-networks.yml: this yml define the network to communicate with *Letsencrypt Nginx Proxy Companion*.


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
    -e "INSTALL_APPS=erpnext" \
    <project-name>_erpnext-python_1 docker-entrypoint.sh new
```

Environment Variables needed:

- `SITE_NAME`: name of the new site to create.
- `DB_ROOT_USER`: MariaDB Root user. The user that can create databases.
- `MYSQL_ROOT_PASSWORD`: In case of mariadb docker container use the one set in `MYSQL_ROOT_PASSWORD` in previous steps. In case of managed database use appropriate password.
- `ADMIN_PASSWORD`: set the administrator password for new site.
- `INSTALL_APPS=erpnext`: available only in erpnext-worker and erpnext containers (or other containers with custom apps). Installs ERPNext (and/or the specified apps, comma-delinieated) on this new site.
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

### Custom apps

> For the sake of example, we'll be using a place holder called `[custom]`, and we'll be building off the edge image.

To add your own apps to the image, we'll need to create a custom image with the help of a special wrapper script

1. Create two folders called `[custom]-worker` and `[custom]-nginx` in the `build` folder.

    ```bash
    cd frappe_docker
    mkdir ./build/[custom]-worker ./build/[custom]-nginx
    ```

2. Create a `Dockerfile` in `./build/[custom]-worker` with the following content:

    ```Dockerfile
    FROM frappe/erpnext-worker:edge

    RUN install_app [custom] https://github.com/[username]/[custom] [branch]
    # Only add the branch if you are using a specific tag or branch.
    ```

3. Create a `Dockerfile` in `./build/[custom]-nginx` with the following content:

    ```Dockerfile
    FROM bitnami/node:12-prod

    COPY build/[custom]-nginx/install_app.sh /install_app

    RUN /install_app [custom] https://github.com/[username]/[custom]

    FROM frappe/erpnext-nginx:edge

    COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
    COPY --from=0 /rsync /rsync
    RUN echo -n "\n[custom]" >> /var/www/html/apps.txt

    VOLUME [ "/assets" ]

    ENTRYPOINT ["/docker-entrypoint.sh"]
    CMD ["nginx", "-g", "daemon off;"]
    ```

4. Copy over the `install_app.sh` file from `./build/erpnext-nginx`

    ```bash
    cp ./build/erpnext-nginx/install.sh ./build/[custom]-nginx
    ```

5. Open up `./installation/docker-compose-custom.yml` and replace all instances of `[app]` with the name of your app.

    ```bash
    sed -i "s#\[app\]#[custom]#" ./installation/docker-compose-custom.yml
    ```

6. Install like usuall, except that when you set the `INSTALL_APPS` variable set it to `erpnext,[custom]`.

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
