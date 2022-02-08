Install [crazy-max/swarm-cronjob](https://github.com/crazy-max/swarm-cronjob) and then deploy following stack.

```yaml
version: "3.7"

services:
  backup:
    image: frappe/erpnext-worker:version-13
    entrypoint: ["bash", "-c"]
    command: ["docker-entrypoint.sh backup; docker-entrypoint.sh push-backup"]
    environment:
      - WITH_FILES=1
      - BUCKET_NAME=backups
      - REGION=region
      - ACCESS_KEY_ID=access_id_from_provider
      - SECRET_ACCESS_KEY=secret_access_from_provider
      - ENDPOINT_URL=https://region.storage-provider.com
      - BUCKET_DIR=frappe-bench
    volumes:
      - "sites-vol:/home/frappe/frappe-bench/sites"
    deploy:
      labels:
        - "swarm.cronjob.enable=true"
        - "swarm.cronjob.schedule=0 */3 * * *"
        - "swarm.cronjob.skip-running=true"
      replicas: 0
      restart_policy:
        condition: none
    networks:
      - frappe-network

volumes:
  sites-vol:
    external: true
    name: frappe-bench-v12_sites-vol

networks:
  frappe-network:
    external: true
```

Note:

- In Above stack, `backup` runs every 3 hours.
- Change image and tag version as per need.
- Change environment variables as per the bucket credentials.
- Change cron string(s) as per need.

### For docker-compose based installation not using docker swarm

Add minio

```yaml
version: "3.7"
services:
  minio:
    image: minio/minio
    command: ["server", "/data"]
    environment:
      - MINIO_ACCESS_KEY=RANDOMACCESSKEY
      - MINIO_SECRET_KEY=RANDOMSECRETKEY
    volumes:
      - "minio-vol:/data"
    networks:
      - erpnext-network
    # Do not enable, check how to secure minio, out of scope of this project.
    #labels:
    #  - "traefik.enable=true"
    #  - "traefik.http.routers.minio.rule=Host(`backup.example.com`)"
    #  - "traefik.http.routers.minio.entrypoints=websecure"
    #  - "traefik.http.routers.minio.tls.certresolver=myresolver"
    #  - "traefik.http.services.minio.loadbalancer.server.port=9000"

networks:
  erpnext-network:
    external: true
    name: <your_frappe_docker_project_name>_default

volumes:
  minio-vol:
```

Create backup service. Create file `backup-job.yml`

```yaml
version: "3.7"
services:
  push-backup:
    image: frappe/erpnext-worker:v13
    entrypoint: ["bash", "-c"]
    command: ["docker-entrypoint.sh backup; docker-entrypoint.sh push-backup"]
    environment:
      - WITH_FILES=1
      - BUCKET_NAME=erpnext
      - REGION=us-east-1
      - ACCESS_KEY_ID=RANDOMACCESSKEY
      - SECRET_ACCESS_KEY=RANDOMSECRETKEY
      - ENDPOINT_URL=http://minio:9000
      - BUCKET_DIR=backups
      - BACKUP_LIMIT=8
    volumes:
      - "sites-vol:/home/frappe/frappe-bench/sites"
    networks:
      - erpnext-network

networks:
  erpnext-network:
    external: true
    name: <your_frappe_docker_project_name>_default

volumes:
  sites-vol:
    external: true
    name: <your_frappe_docker_project_name>_sites-vol
```

Add crontab entry for backup every 6 hours

```
0 */6 * * * /usr/local/bin/docker-compose -f /path/to/backup-job.yml up -d > /dev/null
```
