# Production deployment using docker

### Setup Letsencrypt Nginx Proxy Companion

DNS needs to be configured for following to work.

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
cd frappe_docker
cp installation/env-example .env

# make directory for sites
mkdir installation/sites
```

### Setup Environment Variables

Environment variables are set to pass secret and variable data.

If `env-example` is copied to `.env` following values are set.

- `VERSION=edge` set version tag or latest for major version e.g. v12.3.0, v12.
- `MYSQL_ROOT_PASSWORD=admin`, set mariadb root password (bootstraps a mariadb container with this root password). If managed database mariadb is used NO need to set the password here.
- `MARIADB_HOST=mariadb` set hostname to `mariadb` in case of docker container for mariadb is used. In case managed db is used set the hostname/IP/domain name here.
- `SITES=site1.domain.com,site2.domain.com` these are list of sites that are part of the deployment "bench". Each site is separated by (,) comma.
- `LETSENCRYPT_EMAIL=your.email@your.domain.com` email for letsencrypt expiry notification.

### Start frappe-bench services

```sh
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation up -d
```

Note: use `docker-compose-frappe.yml` in case you need bench with just frappe installed.

### Create new sites

Note:

- Wait for mariadb to start. If new site creation fails re-try again after mariadb container is up and running.
- Use `.env` file or environment variables instead of passing secrets as command arguments.

```sh
# Create ERPNext site
docker exec -it \
    -e "SITE_NAME=$SITE_NAME" \
    -e "DB_ROOT_USER=$DB_ROOT_USER" \
    -e "MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD" \
    -e "ADMIN_PASSWORD=$ADMIN_PASSWORD" \
    -e "INSTALL_ERPNEXT=1" \
    frappebench00_erpnext-python_1 docker-entrypoint.sh new
```

Environment Variables needed:

- `SITE_NAME`, name of the new site to create.
- `DB_ROOT_USER`, MariaDB Root user. The user that can create databases.
- `MYSQL_ROOT_PASSWORD`, In case of mariadb docker container use the one set in `MYSQL_ROOT_PASSWORD` in previous steps. In case of managed database use appropriate password.
- `ADMIN_PASSWORD` set the administrator password for new site.
- `INSTALL_ERPNEXT=1` available only in erpnext-worker and erpnext containers. Installs ERPNext on this new site.
- `FORCE=1` is optional variable which force installs the same site.

### Backup sites

Environment Variables

- `SITES` is list of sites separated by (:) colon to migrate. e.g. `SITES=site1.domain.com` or `SITES=site1.domain.com:site2.domain.com` By default all sites in bench will be backed up.
- `WITH_FILES` if set to 1, it will back up user uploaded files for the sites.

```sh
docker exec -it \
    -e "SITES=site1.domain.com:site2.domain.com" \
    -e "WITH_FILES=1" \
    frappebench00_erpnext-python_1 docker-entrypoint.sh backup
```

Backup will be available in `sites` mounted volume.

### Update and migrate site

```sh
# Change to repo root
cd $HOME/frappe_docker

# Update environment variable VERSION
nano .env

# Pull new images
docker-compose \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    pull

# Restart containers
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation up -d

docker exec -it \
    -e "MAINTENANCE_MODE=1" \
    frappebench00_erpnext-python_1 docker-entrypoint.sh migrate
```

### Troubleshoot

1. Remove containers and volumes clear redis cache:

This can be used when images are upgraded and if migration fails.

```
# change to repo root
cd $HOME/frappe_docker

# Stop all bench containers
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation stop

# Remove redis containers
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation rm redis-cache redis-queue redis-socketio

# Clean redis volumes
docker volume rm \
    frappebench00_redis-cache-vol \
    frappebench00_redis-queue-vol \
    frappebench00_redis-socketio-vol

# Restart project
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation up -d
```

2. Clear redis cache by exec command:

In case of following error during container restarts,

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

docker exec -it frappebench00_redis-cache_1 redis-cli FLUSHALL
docker exec -it frappebench00_redis-queue_1 redis-cli FLUSHALL
docker exec -it frappebench00_redis-socketio_1 redis-cli FLUSHALL
```

Note: Environment variables from `.env` file located at current working directory will be used.
