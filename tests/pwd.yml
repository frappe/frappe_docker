version: "3"

services:
  traefik:
    image: "traefik:v2.2"
    ports:
      - "80:80"
    deploy:
      restart_policy:
        condition: on-failure
      labels:
        - "traefik.enable=true"
    command:
      - "--log.level=DEBUG"
      - "--providers.docker"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--providers.docker.swarmmode"
      - "--accesslog"
      - "--log"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  erpnext-nginx:
    image: frappe/erpnext-nginx:edge
    environment:
      - FRAPPE_PY=erpnext-python
      - FRAPPE_PY_PORT=8000
      - FRAPPE_SOCKETIO=frappe-socketio
      - SOCKETIO_PORT=9000
    deploy:
      restart_policy:
        condition: on-failure
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.erpnext-nginx.rule=HostRegexp(`{catchall:.*}`)"
        - "traefik.http.middlewares.erpnext-nginx.headers.customrequestheaders.Host=erpnext-nginx"
        - "traefik.http.routers.erpnext-nginx.middlewares=erpnext-nginx"
        - "traefik.http.routers.erpnext-nginx.entrypoints=web"
        - "traefik.http.services.erpnext-nginx.loadbalancer.server.port=80"
    volumes:
      - sites-vol:/var/www/html/sites:rw
      - assets-vol:/assets:rw

  erpnext-python:
    image: frappe/erpnext-worker:edge
    deploy:
      restart_policy:
        condition: on-failure
    environment:
      - MARIADB_HOST=mariadb
      - REDIS_CACHE=redis-cache:6379
      - REDIS_QUEUE=redis-queue:6379
      - REDIS_SOCKETIO=redis-socketio:6379
      - SOCKETIO_PORT=9000
      - AUTO_MIGRATE=1
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw
      - assets-vol:/home/frappe/frappe-bench/sites/assets:rw

  frappe-socketio:
    image: frappe/frappe-socketio:edge
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw

  erpnext-worker-default:
    image: frappe/erpnext-worker:edge
    deploy:
      restart_policy:
        condition: on-failure
    command: worker
    depends_on:
      - redis-queue
      - redis-cache
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw

  erpnext-worker-short:
    image: frappe/erpnext-worker:edge
    deploy:
      restart_policy:
        condition: on-failure
    command: worker
    environment:
      - WORKER_TYPE=short
    depends_on:
      - redis-queue
      - redis-cache
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw

  erpnext-worker-long:
    image: frappe/erpnext-worker:edge
    deploy:
      restart_policy:
        condition: on-failure
    command: worker
    environment:
      - WORKER_TYPE=long
    depends_on:
      - redis-queue
      - redis-cache
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw

  erpnext-schedule:
    image: frappe/erpnext-worker:edge
    deploy:
      restart_policy:
        condition: on-failure
    command: schedule
    depends_on:
      - redis-queue
      - redis-cache
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw

  redis-cache:
    image: redis:latest
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - redis-cache-vol:/data

  redis-queue:
    image: redis:latest
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - redis-queue-vol:/data

  redis-socketio:
    image: redis:latest
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - redis-socketio-vol:/data

  site-configurator:
    image: frappe/erpnext-worker:edge
    deploy:
      restart_policy:
        condition: none
    command: ["bash", "-c", "echo erpnext-nginx > /sites/currentsite.txt"]
    volumes:
      - sites-vol:/sites:rw

  mariadb-configurator:
    image: mariadb:10.3
    deploy:
      restart_policy:
        condition: none
    command:
      - "bash"
      - "-c"
      - >
        echo -e "[mysqld]\n
        skip-host-cache\n
        skip-name-resolve\n
        character-set-client-handshake = FALSE\n
        character-set-server = utf8mb4\n
        collation-server = utf8mb4_unicode_ci\n
        [mysql]\n
        default-character-set = utf8mb4\n
        [mysqld_safe]\n
        skip_log_error\n
        syslog\n" > /data/frappe.cnf
    volumes:
      - mariadb-conf-vol:/data:rw

  mariadb:
    image: mariadb:10.3
    deploy:
      restart_policy:
        condition: on-failure
    environment:
      - MYSQL_ROOT_PASSWORD=admin
    volumes:
      - mariadb-conf-vol:/etc/mysql/conf.d
      - mariadb-vol:/var/lib/mysql

  site-creator:
    image: frappe/erpnext-worker:edge
    deploy:
      restart_policy:
        condition: none
    command: new
    environment:
      - SITE_NAME=erpnext-nginx
      - DB_ROOT_USER=root
      - MYSQL_ROOT_PASSWORD=admin
      - ADMIN_PASSWORD=admin
      - INSTALL_APPS=erpnext
    volumes:
      - sites-vol:/home/frappe/frappe-bench/sites:rw

volumes:
  mariadb-vol:
  mariadb-conf-vol:
  redis-cache-vol:
  redis-queue-vol:
  redis-socketio-vol:
  assets-vol:
  sites-vol:
