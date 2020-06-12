### Setting up Pre-requisites

This repository requires Docker, docker-compose and Git to be setup on the instance to be used.

For Docker basics and best practices. Refer Docker documentation.

### Cloning the repository and preliminary steps

Clone this repository somewhere in your system:

```sh
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

Copy the example docker environment file to `.env`:

For local setup

```sh
cp env-local .env
```

For production

```sh
cp env-production .env
```

### Setup Environment Variables

To get started, copy the existing `env-local` or `env-production` file to `.env`. By default, the file will contain the following variables:

- `ERPNEXT_VERSION=edge`
    - In this case, `edge` corresponds to `develop`. To setup any other version, you may use the branch name or version specific tags. (eg. version-12, v11.1.15, v11).
- `FRAPPE_VERSION=edge`
    - In this case, `edge` corresponds to `develop`. To setup any other version, you may use the branch name or version specific tags. (eg. version-12, v11.1.15, v11).
- `MYSQL_ROOT_PASSWORD=admin`
    - Bootstraps a MariaDB container with this value set as the root password. If a managed MariaDB instance is used, there is no need to set the password here.
- `MARIADB_HOST=mariadb`
    - Sets the hostname to `mariadb`. This is required if the database is managed by the containerized MariaDB instance.
    - In case of a separately managed database setups, set the value to the database's hostname/IP/domain.
- `SITE_NAME=mysite.localhost`
    - Creates this site after starting all services and installs ERPNext.
- ``SITES=`${SITE_NAME}` ``
    - List of sites that are part of the deployment "bench" Each site is separated by a comma(,) and quoted in backtick (`). By default site created by ``SITE_NAME`` variable is added here.
    - If LetsEncrypt is being setup, make sure that the DNS for all the site's domains correctly point to the current instance.
- `LETSENCRYPT_EMAIL=your.email@your.domain.com`
    - Email for LetsEncrypt expiry notification. This is only required if you are setting up LetsEncrypt.

Notes:

- `AUTO_MIGRATE` variable is set to `1` by default. It checks if there is semver bump or git hash change in case of develop branch and automatically migrates the sites on container start up.
- It is good practice to use image tag for specific version instead of latest. e.g `frappe-socketio:v12.5.1`, `erpnext-nginx:v12.7.1`.

### Start containers

Execute the following command:

```sh
docker-compose --project-name <project-name> up -d
```

Make sure to replace `<project-name>` with the desired name you wish to set for the project.

Notes:

- The local deployment is for testing and REST API development purpose only
- A complete development environment is available [here](development)
- The site names are limited to patterns matching \*.localhost by default
- Additional site name patterns can be added by editing /etc/hosts of your host machine

#### Using Amazon RDS (or any other DBaaS)

To configure usage of RDS, `common_site_config.json` in your `sites-vol` volume has to be edited using:

```sh
docker run \
    -it \
    -v <project-name>_sites-vol:/sites \
    alpine vi /sites/common_site_config.json
```

Instead of `alpine` you can use any image you like.

For full instructions, refer to the [wiki](https://github.com/frappe/frappe/wiki/Using-Frappe-with-Amazon-RDS-(or-any-other-DBaaS)). Common question can be found in Issues and on forum.

### Docker containers

This repository contains the following docker-compose files, each one containing the described images:
* redis-cache: cache store
    * volume: redis-cache-vol
* redis-queue: used by workers
    * volume: redis-queue-vol
* redis-socketio: used by socketio service
    * volume: redis-socketio-vol
* mariadb: main database
    * volume: mariadb-vol
* erpnext-nginx: serves static assets and proxies web request to the appropriate container, allowing to offer all services on the same port.
    * volume: assets-vol
* erpnext-python: main application code
* frappe-socketio: enables realtime communication to the user interface through websockets
* erpnext-worker-default: background runner
* erpnext-worker-short: background runner for short-running jobs
* erpnext-worker-long: background runner for long-running jobs
* erpnext-schedule
    * volume: sites-vol

### Site operations

Use env file,

```sh
source .env
```

Or specify environment variables instead of passing secrets as command arguments. Refer notes section for environment variables required

#### Setup New Site

Note:

- Wait for the MariaDB service to start before trying to create a new site.
    - If new site creation fails, retry after the MariaDB container is up and running.
    - If you're using a managed database instance, make sure that the database is running before setting up a new site.

```sh
# Create ERPNext site
docker run \
    -e "SITE_NAME=$SITE_NAME" \
    -e "DB_ROOT_USER=$DB_ROOT_USER" \
    -e "MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD" \
    -e "ADMIN_PASSWORD=$ADMIN_PASSWORD" \
    -e "INSTALL_APPS=erpnext" \
    -v <project-name>_sites-vol:/home/frappe/frappe-bench/sites \
    --network <project-name>_default \
    frappe/erpnext-worker:$VERSION new
```

Environment Variables needed:

- `SITE_NAME`: name of the new site to create.
- `DB_ROOT_USER`: MariaDB Root user.
- `MYSQL_ROOT_PASSWORD`: In case of the MariaDB docker container use the one set in `MYSQL_ROOT_PASSWORD` in previous steps. In case of a managed database use the appropriate password.
- `MYSQL_ROOT_PASSWORD_FILE` - When the MariaDB root password is stored using docker secrets.
- `ADMIN_PASSWORD`: set the administrator password for the new site.
- `ADMIN_PASSWORD_FILE`: set the administrator password for the new site using docker secrets.
- `INSTALL_APPS=erpnext`: available only in erpnext-worker and erpnext containers (or other containers with custom apps). Installs ERPNext (and/or the specified apps, comma-delinieated) on this new site.
- `FORCE=1`: optional variable which force installation of the same site.

#### Add sites to proxy

Change `SITES` variable to the list of sites created encapsulated in backtick and separated by comma with no space. e.g. ``SITES=`site1.example.com`,`site2.example.com` ``.

Reload variables with following command.

```sh
docker-compose up --project-name <project-name> -d
```

#### Backup Sites

Environment Variables

- `SITES` is list of sites separated by `:` colon to migrate. e.g. `SITES=site1.domain.com` or `SITES=site1.domain.com:site2.domain.com` By default all sites in bench will be backed up.
- `WITH_FILES` if set to 1, it will backup user-uploaded files.
- By default `backup` takes mariadb dump and gzips it. Example file, `20200325_221230-test_localhost-database.sql.gz`
- If `WITH_FILES` is set then it will also backup public and private files of each site as uncompressed tarball. Example files, `20200325_221230-test_localhost-files.tar` and `20200325_221230-test_localhost-private-files.tar`
- All the files generated by backup are placed at volume location `sites-vol:/{site-name}/private/backups/*`

```sh
docker run \
    -e "SITES=site1.domain.com:site2.domain.com" \
    -e "WITH_FILES=1" \
    -v <project-name>_sites-vol:/home/frappe/frappe-bench/sites \
    --network <project-name>_default \
    frappe/erpnext-worker:$VERSION backup
```

The backup will be available in the `sites-vol` volume.

#### Push backup to s3 compatible storage

Environment Variables

- `BUCKET_NAME`, Required to set bucket created on S3 compatible storage.
- `REGION`, Required to set region for S3 compatible storage.
- `ACCESS_KEY_ID`, Required to set access key.
- `SECRET_ACCESS_KEY`, Required to set secret access key.
- `ENDPOINT_URL`, Required to set URL of S3 compatible storage.
- `BUCKET_DIR`, Required to set directory in bucket where sites from this deployment will be backed up.
- `BACKUP_LIMIT`, Optionally set this to limit number of backups in bucket directory. Defaults to 3.

```sh
 docker run \
    -e "BUCKET_NAME=backups" \
    -e "REGION=region" \
    -e "ACCESS_KEY_ID=access_id_from_provider" \
    -e "SECRET_ACCESS_KEY=secret_access_from_provider" \
    -e "ENDPOINT_URL=https://region.storage-provider.com" \
    -e "BUCKET_DIR=frappe-bench" \
    -v <project-name>_sites-vol:/home/frappe/frappe-bench/sites \
    --network <project-name>_default \
    frappe/frappe-worker:$VERSION push-backup
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
docker-compose pull

# Restart containers
docker-compose --project-name <project-name> up -d
```

#### Restore backups

Environment Variables

- `MYSQL_ROOT_PASSWORD` or `MYSQL_ROOT_PASSWORD_FILE`(when using docker secrets), Required to restore mariadb backups.
- `BUCKET_NAME`, Required to set bucket created on S3 compatible storage.
- `ACCESS_KEY_ID`, Required to set access key.
- `SECRET_ACCESS_KEY`, Required to set secret access key.
- `ENDPOINT_URL`, Required to set URL of S3 compatible storage.
- `REGION`, Required to set region for s3 compatible storage.
- `BUCKET_DIR`, Required to set directory in bucket where sites from this deployment will be backed up.

```sh
docker run \
    -e "MYSQL_ROOT_PASSWORD=admin" \
    -e "BUCKET_NAME=backups" \
    -e "REGION=region" \
    -e "ACCESS_KEY_ID=access_id_from_provider" \
    -e "SECRET_ACCESS_KEY=secret_access_from_provider" \
    -e "ENDPOINT_URL=https://region.storage-provider.com" \
    -e "BUCKET_DIR=frappe-bench" \
    -v <project-name>_sites-vol:/home/frappe/frappe-bench/sites \
    -v ./backups:/home/frappe/backups \
    --network <project-name>_default \
    frappe/frappe-worker:$VERSION restore-backup
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

