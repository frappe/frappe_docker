### Prerequisites

IMPORTANT: All commands are executed on live server with public IP and DNS Configured.

#### Setup docker swarm

Follow [dockerswarm.rocks](https://dockerswarm.rocks) guide to setup Docker swarm, Traefik and Portainer.

Use Portainer for rest of the guide

### Create Config

Configs > Add Config > `frappe-mariadb-config`

```
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

### Create Secret

Secret > Add Secret > `frappe-mariadb-root-password`

```
longsecretpassword
```

Note down this password.
It is only available in mariadb containers at location `/run/secrets/frappe-mariadb-root-password` later

### Deploy MariaDB Replication

Stacks > Add Stacks > `frappe-mariadb`

```yaml
version: "3.7"

services:
  mariadb-master:
    image: 'bitnami/mariadb:10.3'
    deploy:
      restart_policy:
        condition: on-failure
    configs:
      - source: frappe-mariadb-config
        target: /opt/bitnami/mariadb/conf/bitnami/my_custom.cnf
    networks:
      - frappe-network
    secrets:
      - frappe-mariadb-root-password
    volumes:
      - 'mariadb_master_data:/bitnami/mariadb'
    environment:
      - MARIADB_REPLICATION_MODE=master
      - MARIADB_REPLICATION_USER=repl_user
      - MARIADB_REPLICATION_PASSWORD_FILE=/run/secrets/frappe-mariadb-root-password
      - MARIADB_ROOT_PASSWORD_FILE=/run/secrets/frappe-mariadb-root-password

  mariadb-slave:
    image: 'bitnami/mariadb:10.3'
    deploy:
      restart_policy:
        condition: on-failure
    configs:
      - source: frappe-mariadb-config
        target: /opt/bitnami/mariadb/conf/bitnami/my_custom.cnf
    networks:
      - frappe-network
    secrets:
      - frappe-mariadb-root-password
    volumes:
      - 'mariadb_slave_data:/bitnami/mariadb'
    environment:
      - MARIADB_REPLICATION_MODE=slave
      - MARIADB_REPLICATION_USER=repl_user
      - MARIADB_REPLICATION_PASSWORD_FILE=/run/secrets/frappe-mariadb-root-password
      - MARIADB_MASTER_HOST=mariadb-master
      - MARIADB_MASTER_PORT_NUMBER=3306
      - MARIADB_MASTER_ROOT_PASSWORD_FILE=/run/secrets/frappe-mariadb-root-password

volumes:
  mariadb_master_data:
  mariadb_slave_data:

configs:
  frappe-mariadb-config:
    external: true

secrets:
  frappe-mariadb-root-password:
    external: true

networks:
  frappe-network:
    name: frappe-network
    attachable: true
```

### Deploy Frappe/ERPNext

Stacks > Add Stacks > `frappe-bench-v13`

```yaml
version: "3.7"

services:
  redis-cache:
    image: redis:latest
    volumes:
      - redis-cache-vol:/data
    deploy:
      restart_policy:
        condition: on-failure
    networks:
      - frappe-network

  redis-queue:
    image: redis:latest
    volumes:
      - redis-queue-vol:/data
    deploy:
      restart_policy:
        condition: on-failure
    networks:
      - frappe-network

  redis-socketio:
    image: redis:latest
    volumes:
      - redis-socketio-vol:/data
    deploy:
      restart_policy:
        condition: on-failure
    networks:
      - frappe-network

  erpnext-nginx:
    image: frappe/erpnext-nginx:${ERPNEXT_VERSION?Variable ERPNEXT_VERSION not set}
    environment:
      - UPSTREAM_REAL_IP_ADDRESS=10.0.0.0/8
      - FRAPPE_PY=erpnext-python
      - FRAPPE_PY_PORT=8000
      - FRAPPE_SOCKETIO=frappe-socketio
      - SOCKETIO_PORT=9000
    volumes:
      - sites-vol:/var/www/html/sites:rw
      - assets-vol:/assets:rw
    networks:
      - frappe-network
      - traefik-public
    deploy:
      restart_policy:
        condition: on-failure
      labels:
        - "traefik.docker.network=traefik-public"
        - "traefik.enable=true"
        - "traefik.constraint-label=traefik-public"
        - "traefik.http.routers.erpnext-nginx.rule=Host(${SITES?Variable SITES not set})"
        - "traefik.http.routers.erpnext-nginx.entrypoints=http"
        - "traefik.http.routers.erpnext-nginx.middlewares=https-redirect"
        - "traefik.http.routers.erpnext-nginx-https.rule=Host(${SITES?Variable SITES not set})"
        - "traefik.http.routers.erpnext-nginx-https.entrypoints=https"
        - "traefik.http.routers.erpnext-nginx-https.tls=true"
        - "traefik.http.routers.erpnext-nginx-https.tls.certresolver=le"
        - "traefik.http.services.erpnext-nginx.loadbalancer.server.port=80"

  erpnext-python:
    image: frappe/erpnext-worker:${ERPNEXT_VERSION?Variable ERPNEXT_VERSION not set}
    deploy:
      restart_policy:
        condition: on-failure
    environment:
      - MARIADB_HOST=${MARIADB_HOST?Variable MARIADB_HOST not set}
      - REDIS_CACHE=redis-cache:6379
      - REDIS_QUEUE=redis-queue:6379
      - REDIS_SOCKETIO=redis-socketio:6379
      - SOCKETIO_PORT=9000
      - AUTO_MIGRATE=1
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
      - assets-vol:/home/frappe/frappe-bench/sites/assets:rw
    networks:
      - frappe-network

  frappe-socketio:
    image: frappe/frappe-socketio:${FRAPPE_VERSION?Variable FRAPPE_VERSION not set}
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
    networks:
      - frappe-network

  erpnext-worker-default:
    image: frappe/erpnext-worker:${ERPNEXT_VERSION?Variable ERPNEXT_VERSION not set}
    deploy:
      restart_policy:
        condition: on-failure
    command: worker
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
    networks:
      - frappe-network

  erpnext-worker-short:
    image: frappe/erpnext-worker:${ERPNEXT_VERSION?Variable ERPNEXT_VERSION not set}
    deploy:
      restart_policy:
        condition: on-failure
    command: worker
    environment:
      - WORKER_TYPE=short
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
    networks:
      - frappe-network

  erpnext-worker-long:
    image: frappe/erpnext-worker:${ERPNEXT_VERSION?Variable ERPNEXT_VERSION not set}
    deploy:
      restart_policy:
        condition: on-failure
    command: worker
    environment:
      - WORKER_TYPE=long
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
    networks:
      - frappe-network

  frappe-schedule:
    image: frappe/erpnext-worker:${ERPNEXT_VERSION?Variable ERPNEXT_VERSION not set}
    deploy:
      restart_policy:
        condition: on-failure
    command: schedule
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
    networks:
      - frappe-network

volumes:
  redis-cache-vol:
  redis-queue-vol:
  redis-socketio-vol:
  assets-vol:
  sites-vol:

networks:
  traefik-public:
    external: true
  frappe-network:
    external: true
```

Use environment variables:

- `ERPNEXT_VERSION` variable to be set to desired version of ERPNext. e.g. 12.10.0
- `FRAPPE_VERSION` variable to be set to desired version of Frappe Framework. e.g. 12.7.0
- `MARIADB_HOST=frappe-mariadb_mariadb-master`
- `SITES` variable is list of sites in back tick and separated by comma
```
SITES=`site1.example.com`,`site2.example.com`
```

### Create new site job

1. Containers > Add Container > `add-site1-example-com`
2. Select Image frappe/erpnext-worker:v13
3. Set command as `new`
4. Select network `frappe-network`
5. Select Volume `frappe-bench-v13_sites-vol` and mount in container `/home/frappe/frappe-bench/sites`
6. Env variables:
    - MYSQL_ROOT_PASSWORD=longsecretpassword
    - SITE_NAME=site1.example.com
    - INSTALL_APPS=erpnext
7. Start container

### Migrate Sites job

1. Containers > Add Container > `migrate-sites`
2. Select Image frappe/erpnext-worker:v13
3. Set command as `migrate`
4. Select network `frappe-network`
5. Select Volume `frappe-bench-v13_sites-vol` and mount in container `/home/frappe/frappe-bench/sites`
6. Env variables:
    - MAINTENANCE_MODE=1
7. Start container

