## Getting Started

The templates in this repository will help deploy Frappe/ERPNext docker in a production environment.

This docker installation takes care of the following:

* Setting up the desired version of Frappe/ERPNext.
* Setting up all the system requirements: eg. MariaDB, Node, Redis.
* [OPTIONAL] Configuring networking for remote access and setting up LetsEncrypt

For docker based development refer to this [README](development/README.md)

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
    - Bootstraps a MariaDB container with this value set as the root password. If a managed MariaDB instance is used, there is no need to set the password here.
- `MARIADB_HOST=mariadb`
    - Sets the hostname to `mariadb`. This is required if the database is managed by the containerized MariaDB instance.
    - In case of a separately managed database setups, set the value to the database's hostname/IP/domain.
- `SITES=site1.domain.com,site2.domain.com`
    - List of sites that are part of the deployment "bench" Each site is separated by a comma(,).
    - If LetsEncrypt is being setup, make sure that the DNS for all the site's domains correctly point to the current instance.
- `LETSENCRYPT_EMAIL=your.email@your.domain.com`
    - Email for LetsEncrypt expiry notification. This is only required if you are setting up LetsEncrypt.


### Local deployment for testing

For trying out locally or to develop apps using ERPNext REST API port 80 must be published.
The first command will start the containers; the second command will publish the port of the *-nginx container.


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

Make sure to replace `<project-name>` with the desired name you wish to set for the project.

Notes:

- The local deployment is for testing and REST API development purpose only
- A complete development environment is available [here](Development/README.md)
- The site names are limited to patterns matching \*.localhost by default
- Additional site name patterns can be added by editing /etc/hosts of your host machine

### Deployment for production

#### Setup Letsencrypt Nginx Proxy Companion

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

For more details, see the [Letsencrypt Nginx Proxy Companion github repo](https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion). Letsencrypt Nginx Proxy Companion github repo works by automatically proxying to containers with the `VIRTUAL_HOST` environmental variable.

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

* docker-compose-networks.yml: this yaml define the network to communicate with *Letsencrypt Nginx Proxy Companion*.


### Site operations

#### Setup New Sites

Note:

- Wait for the MariaDB service to start before trying to create a new site.
    - If new site creation fails, retry after the MariaDB container is up and running.
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
- `DB_ROOT_USER`: MariaDB Root user.
- `MYSQL_ROOT_PASSWORD`: In case of the MariaDB docker container use the one set in `MYSQL_ROOT_PASSWORD` in previous steps. In case of a managed database use the appropriate password.
- `ADMIN_PASSWORD`: set the administrator password for the new site.
- `INSTALL_APPS=erpnext`: available only in erpnext-worker and erpnext containers (or other containers with custom apps). Installs ERPNext (and/or the specified apps, comma-delinieated) on this new site.
- `FORCE=1`: optional variable which force installation of the same site.

#### Backup Sites

Environment Variables

- `SITES` is list of sites separated by `:` colon to migrate. e.g. `SITES=site1.domain.com` or `SITES=site1.domain.com:site2.domain.com` By default all sites in bench will be backed up.
- `WITH_FILES` if set to 1, it will backup user-uploaded files.

```sh
docker exec -it \
    -e "SITES=site1.domain.com:site2.domain.com" \
    -e "WITH_FILES=1" \
    <project-name>_erpnext-python_1 docker-entrypoint.sh backup
```

The backup will be available in the `sites` mounted volume.

#### Push backup to s3 compatible storage

Environment Variables

- `BUCKET_NAME`, Required to set bucket created on S3 compatible storage.
- `ACCESS_KEY_ID`, Required to set access key.
- `SECRET_ACCESS_KEY`, Required to set secret access key.
- `ENDPOINT_URL`, Required to set URL of S3 compatible storage.
- `BUCKET_DIR`, Required to set directory in bucket where sites from this deployment will be backed up.
- `BACKUP_LIMIT`, Optionally set this to limit number of backups in bucket directory. Defaults to 3.

```sh
 docker run \
    -e "BUCKET_NAME=backups" \
    -e "ACCESS_KEY_ID=access_id_from_provider" \
    -e "SECRET_ACCESS_KEY=secret_access_from_provider" \
    -e "ENDPOINT_URL=https://region.storage-provider.com" \
    -e "BUCKET_DIR=frappe-bench-v12" \
    -v ./installation/sites:/home/frappe/frappe-bench/sites \
    --network <project-name>_default \
    frappe/frappe-worker:v12 push-backup
```

Note:

- Above example will backup files in bucket called `backup` at location `frappe-bench-v12/site.name.com/DATE_TIME/DATE_TIME-site_name_com-{filetype}.{extension}`,
- example DATE_TIME: 20200325_042020.
- example filetype: database, files or private-files
- example extension: sql.gz or tar

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

#### Restore backups

Environment Variables

- `MYSQL_ROOT_PASSWORD`, Required to restore mariadb backups.
- `BUCKET_NAME`, Required to set bucket created on S3 compatible storage.
- `ACCESS_KEY_ID`, Required to set access key.
- `SECRET_ACCESS_KEY`, Required to set secret access key.
- `ENDPOINT_URL`, Required to set URL of S3 compatible storage.
- `BUCKET_DIR`, Required to set directory in bucket where sites from this deployment will be backed up.

```sh
docker run \
    -e "MYSQL_ROOT_PASSWORD=admin" \
    -e "BUCKET_NAME=backups" \
    -e "ACCESS_KEY_ID=access_id_from_provider" \
    -e "SECRET_ACCESS_KEY=secret_access_from_provider" \
    -e "ENDPOINT_URL=https://region.storage-provider.com" \
    -e "BUCKET_DIR=frappe-bench-v12" \
    -v ./installation/sites:/home/frappe/frappe-bench/sites \
    -v ./backups:/home/frappe/backups \
    --network <project-name>_default \
    frappe/frappe-worker:v12 restore-backup
```

Note:

- Volume must be mounted at location `/home/frappe/backups` for restoring sites
- If no backup files are found in volume, it will use s3 credentials to pull backups
- Backup structure for mounted volume or downloaded from s3:
    - /home/frappe/backups
        - site1.domain.com
            - 20200420_162000
                - 20200420_162000-site1_domain_com-*
        - site2.domain.com
            - 20200420_162000
                - 20200420_162000-site2_domain_com-*

### Custom apps

To add your own Frappe/ERPNext apps to the image, we'll need to create a custom image with the help of a unique wrapper script

> For the sake of simplicity, in this example, we'll be using a place holder called `[custom]`, and we'll be building off the edge image.

Create two directories called `[custom]-worker` and `[custom]-nginx` in the `build` directory.

```shell
cd frappe_docker
mkdir ./build/[custom]-worker ./build/[custom]-nginx
```

Create a `Dockerfile` in `./build/[custom]-worker` with the following content:

```Dockerfile
FROM frappe/erpnext-worker:edge

RUN install_app [custom] https://github.com/[username]/[custom] [branch]
# Only add the branch if you are using a specific tag or branch.
```

Create a `Dockerfile` in `./build/[custom]-nginx` with the following content:

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

Copy over the `install_app.sh` file from `./build/erpnext-nginx`

```shell
cp ./build/erpnext-nginx/install.sh ./build/[custom]-nginx
```

Open up `./installation/docker-compose-custom.yml` and replace all instances of `[app]` with the name of your app.

```shell
sed -i "s#\[app\]#[custom]#" ./installation/docker-compose-custom.yml
```

Install like usual, except that when you set the `INSTALL_APPS` variable to `erpnext,[custom]`.

## Troubleshoot

### Failed migration after image upgrade

Issue: After upgrade of the containers, the automatic migration fails.
Solution: Remove containers and volumes, and clear redis cache:

```shell
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

### ValueError: There exists an active worker named XXX already

Issue: You have the following error during container restart


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

Solution: Clear redis cache using `docker exec` command (take care of replacing `<project-name>` accordingly):

```sh
# Clear the cache which is causing problem.

docker exec -it <project-name>_redis-cache_1 redis-cli FLUSHALL
docker exec -it <project-name>_redis-queue_1 redis-cli FLUSHALL
docker exec -it <project-name>_redis-socketio_1 redis-cli FLUSHALL
```

Note: Environment variables from `.env` file located at the current working directory will be used.

## Development

This repository includes a complete setup to develop with Frappe/ERPNext and Bench, Including the following features:

- VSCode containers integration
- VSCode Python debugger
- Pre-configured Docker containers for an easy start

A complete Readme is available in [development/README.md](development/README.md)