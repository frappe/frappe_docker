### Prerequisites

IMPORTANT: All commands are executed on live server with public IP and DNS Configured.

#### Setup docker swarm

Set hostname

```shell
export USE_HOSTNAME=dog.example.com

echo $USE_HOSTNAME > /etc/hostname
hostname -F /etc/hostname
```

Update packages using tools provided by installed linux distribution.

Example on Ubuntu. Use distro specific commands.

```shell
apt-get update -y && apt-get upgrade
```

Install Docker using official convenience script

```shell
# Download Docker
curl -fsSL get.docker.com -o get-docker.sh
# Install Docker using the stable channel (instead of the default "edge")
CHANNEL=stable sh get-docker.sh
# Remove Docker install script
rm get-docker.sh
```

Setup Swarm Mode

```shell
docker swarm init --advertise-addr 111.111.111.111
```

Note: Select the public IP of the server instead of 111.111.111.111

Add worker nodes. Execute following command from worker node.

```shell
docker swarm join --token SWMTKN-1-5tl7ya98erd9qtasdfml4lqbosbhfqv3asdf4p13-dzw6ugasdfk0arn0 111.111.111.111:2377
```

Note: Replace appropriate token and Public IP of manager in the command.

#### Install Traefik on manager node

Set environment variables

- `EMAIL=user@domain.com`: Letsencrypt Email
- `DOMAIN`: Domain for traefik dashboard, e.g. traefik.example.com
- `HASHED_PASSWORD=$(openssl passwd -apr1 $PASSWORD)` where `PASSWORD` is secret string

deploy the following yaml.

```shell
docker stack deploy -c traefik.yaml traefik
```

```yaml
version: "3.3"

services:
  traefik:
    image: traefik:v2.2
    ports:
      - target: 80
        published: 80
        mode: host
      - target: 443
        published: 443
        mode: host
    command:
      - --api
      - --log.level=INFO
      - --accesslog=true
      - --metrics.prometheus=true
      - --providers.docker=true
      - --providers.docker.endpoint=unix:///var/run/docker.sock
      - --providers.docker.swarmMode=true
      - --providers.docker.exposedbydefault=false
      - --providers.docker.network=traefik-public
      - --entrypoints.http.address=:80
      - --entrypoints.https.address=:443
      - --certificatesResolvers.certbot=true
      - --certificatesResolvers.certbot.acme.httpChallenge=true
      - --certificatesResolvers.certbot.acme.httpChallenge.entrypoint=http
      - --certificatesResolvers.certbot.acme.email=${EMAIL?Variable EMAIL not set}
      - --certificatesResolvers.certbot.acme.storage=/certs/acme-v2.json
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /data/traefik/certs:/certs
    networks:
      - traefik-public
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
      labels:
        # v2.2
        - "traefik.docker.network=traefik-public"
        - "traefik.enable=true"
        - "traefik.http.services.traefik.loadbalancer.server.port=8080"
        # Http
        - "traefik.http.routers.traefik.rule=Host(`${DOMAIN?Variable DOMAIN not set}`)"
        - "traefik.http.routers.traefik.entrypoints=http,https"
        # Enable Let's encrypt auto certificat creation
        - "traefik.http.routers.traefik.tls.certresolver=certbot"
        # Enable authentification
        - "traefik.http.routers.traefik.middlewares=traefik-auth"
        - "traefik.http.middlewares.traefik-auth.basicauth.users=admin:${HASHED_PASSWORD?Variable HASHED_PASSWORD not set}"
        # Redirect All hosts to HTTPS
        - "traefik.http.routers.http-catchall.rule=hostregexp(`{host:.+}`)"
        - "traefik.http.routers.http-catchall.entrypoints=http"
        - "traefik.http.routers.http-catchall.middlewares=redirect-to-https@docker"
        - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
        - "traefik.http.routers.traefik.service=api@internal"
        - "traefik.http.routers.traefik.tls"

networks:
  traefik-public:
    name: traefik-public
    attachable: true
    driver: overlay
```

#### Install Portainer

Set environment variable `DOMAIN` as domain where portainer is located e.g. `DOMAIN=portainer.example.com`

deploy the following yaml.

```shell
docker stack deploy -c portainer.yaml portainer
```

```yaml
version: "3.3"

services:
  agent:
    image: portainer/agent:1.5.1
    environment:
      AGENT_CLUSTER_ADDR: tasks.agent
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes
    networks:
      - agent-network
    deploy:
      mode: global
      placement:
        constraints:
          - node.platform.os == linux

  portainer:
    image: portainer/portainer:1.23.2
    command: -H tcp://tasks.agent:9001 --tlsskipverify
    volumes:
      - portainer-data:/data
    networks:
      - agent-network
      - traefik-public
    deploy:
      placement:
        constraints:
          - node.role == manager
          - node.labels.portainer.portainer-data == true
      labels:
        - "traefik.docker.network=traefik-public"
        - "traefik.enable=true"
        - "traefik.http.services.portainer.loadbalancer.server.port=9000"
        # Http
        - "traefik.http.routers.portainer.rule=Host(`${DOMAIN?Variable DOMAIN not set}`)"
        - "traefik.http.routers.portainer.entrypoints=http,https"
        # Enable Let's encrypt auto certificate creation
        - "traefik.http.routers.portainer.tls.certresolver=certbot"
networks:
  agent-network:
    attachable: true
  traefik-public:
    external: true

volumes:
  portainer-data:
```

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

Stacks > Add Stacks > `frappe-bench-v12`

```yaml
version: "3"

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
    image: frappe/erpnext-nginx:v12.7.1
    environment:
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
        - "traefik.http.services.frappe-bench-v12.loadbalancer.server.port=80"
        # Http
        - "traefik.http.routers.frappe-bench-v12.rule=Host(${SITES?Variable SITES not set})"
        - "traefik.http.routers.frappe-bench-v12.entrypoints=http,https"
        # Enable Let's encrypt auto certificate creation
        - "traefik.http.routers.frappe-bench-v12.tls.certresolver=certbot"

  erpnext-python:
    image: frappe/erpnext-worker:v12.7.1
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
    image: frappe/frappe-socketio:v12.5.1
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
    networks:
      - frappe-network

  frappe-worker-default:
    image: frappe/erpnext-worker:v12.7.1
    deploy:
      restart_policy:
        condition: on-failure
    command: worker
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
    networks:
      - frappe-network

  frappe-worker-short:
    image: frappe/erpnext-worker:v12.7.1
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

  frappe-worker-long:
    image: frappe/erpnext-worker:v12.7.1
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
    image: frappe/erpnext-worker:v12.7.1
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

- `MARIADB_HOST=frappe-mariadb_mariadb-master`
- `SITES` variable is list of sites in back tick and separated by comma
```
SITES=`site1.example.com`,`site2.example.com`
```

### Create new site job

1. Containers > Add Container > `add-site1-example-com`
2. Select Image frappe/erpnext-worker:v12
3. Set command as `new`
4. Select network `frappe-network`
5. Select Volume `frappe-bench-v12_sites_vol` and mount in container `/home/frappe/frappe-bench/sites`
6. Env variables:
    - MYSQL_ROOT_PASSWORD=longsecretpassword
    - SITE_NAME=site1.example.com
7. Start container

### Migrate Sites job

1. Containers > Add Container > `migrate-sites`
2. Select Image frappe/erpnext-worker:v12
3. Set command as `migrate`
4. Select network `frappe-network`
5. Select Volume `frappe-bench-v12_sites_vol` and mount in container `/home/frappe/frappe-bench/sites`
6. Env variables:
    - MAINTENANCE_MODE=1
7. Start container

