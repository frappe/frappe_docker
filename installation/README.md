# Production deployment using docker

### Setup Letsencrypt Nginx Proxy Companion

Read more: https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion

```sh
cd $HOME
git clone https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion.git
cd docker-compose-letsencrypt-nginx-proxy-companion
cp .env.sample .env
./start.sh
```

### Clone frappe_docker repository

```sh
cd $HOME
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker/installation
cp env-example .env

# make directory for sites
mkdir sites
```

### Setup Environment Variables

3 Environment variables are set to pass secret and variable data.

If `env-example` is copied to `.env` following values are set.

- `VERSION=edge` set version tag or latest for major version e.g. v12.3.0, v12
- `MYSQL_ROOT_PASSWORD=admin`, set mariadb root password (bootstraps a mariadb container with this root password). If managed database mariadb is used NO need to set the password here
- `MARIADB_HOST=mariadb` set hostname to `mariadb` in case of docker container for mariadb is used. In case managed db is used set the hostname/IP/domain name here
- `SITES=site1.domain.com,site2.domain.com` these are list of sites that are part of the deployment "bench". Each site is separated by (,) comma
- `LETSENCRYPT_EMAIL=your.email@your.domain.com` email for letsencrypt expiry notification

### Start frappe-bench services

DNS needs to be configured for following to work

```sh
docker-compose \
    --project-name frappe-bench-00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-conpose-erpnext.yml \
    --project-directory . up -d
```

Note: use `docker-compose-frappe.yml` in case you need bench with just frappe installed

### Create new sites

Note: Wait for mariadb to start. If new site creation fails re-try again after mariadb container is up and running

```sh
# Create ERPNext site
docker exec \
    -e "SITE_NAME=site1.domain.com" \
    -e "DB_ROOT_USER=root" \
    -e "DB_ROOT_PASSWORD=admin" \
    -e "ADMIN_PASSWORD=admin" \
    -e "INSTALL_ERPNEXT=1" \
    frappe-bench-00_erpnext-python_1 new
```

Environment Variables:

- `SITE_NAME`, name of the new site to create
- `DB_ROOT_USER`, MariaDB Root user. The user that can create databases
- `DB_ROOT_PASSWORD`, In case of mariadb docker container use the one set in `MYSQL_ROOT_PASSWORD` in previous steps. In case of managed database use appropriate password
- `ADMIN_PASSWORD` set the administrator password for new site
- `INSTALL_ERPNEXT=1` available only in erpnext-worker and erpnext containers. Installs ERPNext on this new site
- `FORCE=1` is optional variable which force installs the same site.

### Backup sites

Environment Variables

- `SITES` is list of sites separated by (:) colon to migrate. e.g. `SITES=site1.domain.com` or `SITES=site1.domain.com:site2.domain.com` By default all sites in bench will be backed up
- `WITH_FILES` if set to 1, it will back up user uploaded files for the sites

```sh
docker exec \
    -e "SITES=site1.domain.com:site2.domain.com" \
    -e "WITH_FILES=1" \
    frappe-bench-00_erpnext-python_1 backup
```

Backup will be available in `sites` mounted volume

### Update and migrate site

```sh
# Change to repo root
cd $HOME/frappe_docker

# Pull new images
docker-compose \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    pull

# Restart containers
docker-compose \
    --project-name frappe-bench-00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    --project-directory . restart

docker exec \
    -e "MAINTENANCE_MODE=1" \
    frappe-bench-00_erpnext-python_1 migrate
```

### Troubleshoot

1. Clearing redis cache:

```
# change to repo root
cd $HOME/frappe_docker

# Stop all bench containers
docker-compose \
    --project-name frappe-bench-00 \
    -f docker/docker-compose-common.yml \
    -f docker/docker-compose-erpnext.yml \
    --project-directory . stop

# Remove redis containers
docker-compose \
    --project-name frappe-bench-00 \
    -f docker/docker-compose-common.yml \
    -f docker/docker-compose-erpnext.yml \
    --project-directory . rm redis-cache redis-queue redis-socketio

# Clean redis volumes
docker volume rm \
    frappe-bench-00_redis-cache-vol \
    frappe-bench-00_redis-queue-vol \
    frappe-bench-00_redis-socketio-vol

# Restart project
docker-compose \
    --project-name frappe-bench-00 \
    -f docker/docker-compose-common.yml \
    -f docker/docker-compose-erpnext.yml \
    --project-directory . up -d
```

Note: Environment variables from `.env` file located at current working directory will be used.
