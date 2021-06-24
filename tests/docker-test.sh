#!/bin/bash
ULINE='\e[1m\e[4m'
ENDULINE='\e[0m'
NEWLINE='\n'

function checkMigrationComplete() {
  echo "Check Migration"
  CONTAINER_ID=$(docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/erpnext-publish.yml \
    ps -q erpnext-python)

  DOCKER_LOG=$(docker logs ${CONTAINER_ID} 2>&1 | grep "Starting gunicorn")
  INCREMENT=0
  while [[ ${DOCKER_LOG} != *"Starting gunicorn"* && ${INCREMENT} -lt 60 ]]; do
    sleep 3
    echo "Wait for migration to complete ..."
    ((INCREMENT = INCREMENT + 1))
    DOCKER_LOG=$(docker logs ${CONTAINER_ID} 2>&1 | grep "Starting gunicorn")
    if [[ ${DOCKER_LOG} != *"Starting gunicorn"* && ${INCREMENT} -eq 60 ]]; then
      docker logs ${CONTAINER_ID}
      exit 1
    fi
  done

  echo -e "${ULINE}Migration Log${ENDULINE}"
  docker logs ${CONTAINER_ID}
}

function loopHealthCheck() {
  echo "Create Container to Check MariaDB"
  docker run --name frappe_doctor \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge doctor || true

  echo "Loop Health Check"
  FRAPPE_LOG=$(docker logs frappe_doctor | grep "Health check successful" || echo "")
  while [[ -z "${FRAPPE_LOG}" ]]; do
    sleep 1
    CONTAINER=$(docker start frappe_doctor)
    echo "Restarting ${CONTAINER} ..."
    FRAPPE_LOG=$(docker logs frappe_doctor | grep "Health check successful" || echo "")
  done
  echo "Health check successful"
}

echo -e "${ULINE}Copy env-example file${ENDULINE}"
cp env-example .env

echo -e "${NEWLINE}${ULINE}Set version to v13${ENDULINE}"
sed -i -e "s/edge/v13/g" .env

echo -e "${NEWLINE}${ULINE}Start Services${ENDULINE}"
docker-compose \
  --project-name frappebench00 \
  -f installation/docker-compose-common.yml \
  -f installation/docker-compose-erpnext.yml \
  -f installation/erpnext-publish.yml \
  pull
docker pull postgres:11.8
docker-compose \
  --project-name frappebench00 \
  -f installation/docker-compose-common.yml \
  -f installation/docker-compose-erpnext.yml \
  -f installation/erpnext-publish.yml \
  up -d
# Start postgres
docker run --name postgresql -d \
  -e "POSTGRES_PASSWORD=admin" \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  postgres:11.8

loopHealthCheck

echo -e "${NEWLINE}${ULINE}Create new site (v13)${ENDULINE}"
docker run -it \
  -e "SITE_NAME=test.localhost" \
  -e "INSTALL_APPS=erpnext" \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:v13 new

echo -e "${NEWLINE}${ULINE}Ping created site${ENDULINE}"
curl -sS http://test.localhost/api/method/version

echo -e "${NEWLINE}${ULINE}Check Created Site Index Page${ENDULINE}"
curl -s http://test.localhost | w3m -T text/html -dump

echo -e "${NEWLINE}${ULINE}Set version to edge${ENDULINE}"
sed -i -e "s/v13/edge/g" .env

echo -e "${NEWLINE}${ULINE}Restart containers with edge image${ENDULINE}"
docker-compose \
  --project-name frappebench00 \
  -f installation/docker-compose-common.yml \
  -f installation/docker-compose-erpnext.yml \
  -f installation/erpnext-publish.yml \
  stop
docker-compose \
  --project-name frappebench00 \
  -f installation/docker-compose-common.yml \
  -f installation/docker-compose-erpnext.yml \
  -f installation/erpnext-publish.yml \
  up -d

checkMigrationComplete

echo -e "${NEWLINE}${ULINE}Ping migrated site${ENDULINE}"
sleep 3
curl -sS http://test.localhost/api/method/version

echo -e "${NEWLINE}${ULINE}Check Migrated Site Index Page${ENDULINE}"
curl -s http://test.localhost | w3m -T text/html -dump

echo -e "${NEWLINE}${ULINE}Create new site (pgsql)${ENDULINE}"
docker run -it \
  -e "SITE_NAME=pgsql.localhost" \
  -e "POSTGRES_HOST=postgresql" \
  -e "DB_ROOT_USER=postgres" \
  -e "POSTGRES_PASSWORD=admin" \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge new

echo -e "${NEWLINE}${ULINE}Check New PGSQL Site${ENDULINE}"
sleep 3
RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -lt 60 ]]; do
  sleep 1
  echo -e "${ULINE}Wait for restoration to complete ..."
  RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
  ((INCREMENT = INCREMENT + 1))
  if [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -eq 60 ]]; then
    CONTAINER_ID=$(docker-compose \
      --project-name frappebench00 \
      -f installation/docker-compose-common.yml \
      -f installation/docker-compose-erpnext.yml \
      -f installation/erpnext-publish.yml \
      ps -q erpnext-python)
    docker logs ${CONTAINER_ID}
    exit 1
  fi
done

echo -e "${NEWLINE}${ULINE}Ping new pgsql site${ENDULINE}"
echo $RESTORE_STATUS

echo -e "${NEWLINE}${ULINE}Check New PGSQL Index Page${ENDULINE}"
curl -s http://pgsql.localhost | w3m -T text/html -dump

echo -e "${NEWLINE}${ULINE}Backup site${ENDULINE}"
docker run -it \
  -e "WITH_FILES=1" \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge backup

MINIO_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
MINIO_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

echo -e "${ULINE}Start MinIO container for s3 compatible storage${ENDULINE}"
docker run -d --name minio \
  -e "MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}" \
  -e "MINIO_SECRET_KEY=${MINIO_SECRET_KEY}" \
  --network frappebench00_default \
  minio/minio server /data

echo -e "${NEWLINE}${ULINE}Create bucket named erpnext${ENDULINE}"
docker run \
  --network frappebench00_default \
  vltgroup/s3cmd:latest s3cmd --access_key=${MINIO_ACCESS_KEY} \
  --secret_key=${MINIO_SECRET_KEY} \
  --region=us-east-1 \
  --no-ssl \
  --host=minio:9000 \
  --host-bucket=minio:9000 \
  mb s3://erpnext

echo -e "${NEWLINE}${NEWLINE}${ULINE}Push backup to MinIO s3${ENDULINE}"
docker run \
  -e BUCKET_NAME=erpnext \
  -e REGION=us-east-1 \
  -e BUCKET_DIR=local \
  -e ACCESS_KEY_ID=${MINIO_ACCESS_KEY} \
  -e SECRET_ACCESS_KEY=${MINIO_SECRET_KEY} \
  -e ENDPOINT_URL=http://minio:9000 \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge push-backup

echo -e "${NEWLINE}${ULINE}Stop Services${ENDULINE}"
docker-compose \
  --project-name frappebench00 \
  -f installation/docker-compose-common.yml \
  -f installation/docker-compose-erpnext.yml \
  -f installation/erpnext-publish.yml \
  stop

echo -e "${NEWLINE}${ULINE}Prune Containers${ENDULINE}"
docker container prune -f && docker volume prune -f

echo -e "${NEWLINE}${ULINE}Start Services${ENDULINE}"
docker-compose \
  --project-name frappebench00 \
  -f installation/docker-compose-common.yml \
  -f installation/docker-compose-erpnext.yml \
  -f installation/erpnext-publish.yml \
  up -d

loopHealthCheck

echo -e "${NEWLINE}${ULINE}Restore backup from MinIO / S3${ENDULINE}"
docker run \
  -e MYSQL_ROOT_PASSWORD=admin \
  -e BUCKET_NAME=erpnext \
  -e BUCKET_DIR=local \
  -e ACCESS_KEY_ID=${MINIO_ACCESS_KEY} \
  -e SECRET_ACCESS_KEY=${MINIO_SECRET_KEY} \
  -e ENDPOINT_URL=http://minio:9000 \
  -e REGION=us-east-1 \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge restore-backup

echo -e "${NEWLINE}${ULINE}Check Restored Site (test)${ENDULINE}"
sleep 3
RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -lt 60 ]]; do
  sleep 1
  echo "Wait for restoration to complete ..."
  RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
  ((INCREMENT = INCREMENT + 1))
  if [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -eq 60 ]]; then
    CONTAINER_ID=$(docker-compose \
      --project-name frappebench00 \
      -f installation/docker-compose-common.yml \
      -f installation/docker-compose-erpnext.yml \
      -f installation/erpnext-publish.yml \
      ps -q erpnext-python)
    docker logs ${CONTAINER_ID}
    exit 1
  fi
done

echo -e "${ULINE}Ping restored site (test)${ENDULINE}"
echo ${RESTORE_STATUS}

echo -e "${NEWLINE}${ULINE}Check Restored Site Index Page (test)${ENDULINE}"
curl -s http://test.localhost | w3m -T text/html -dump

echo -e "${NEWLINE}${ULINE}Check Restored Site (pgsql)${ENDULINE}"
sleep 3
RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -lt 60 ]]; do
  sleep 1
  echo "Wait for restoration to complete ..."
  RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
  ((INCREMENT = INCREMENT + 1))
  if [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -eq 60 ]]; then
    CONTAINER_ID=$(docker-compose \
      --project-name frappebench00 \
      -f installation/docker-compose-common.yml \
      -f installation/docker-compose-erpnext.yml \
      -f installation/erpnext-publish.yml \
      ps -q erpnext-python)
    docker logs ${CONTAINER_ID}
    exit 1
  fi
done

echo -e "${ULINE}Ping restored site (pgsql)${ENDULINE}"
echo ${RESTORE_STATUS}

echo -e "${NEWLINE}${ULINE}Check Restored Site Index Page (pgsql)${ENDULINE}"
curl -s http://pgsql.localhost | w3m -T text/html -dump

echo -e "${NEWLINE}${ULINE}Create new site (edge)${ENDULINE}"
docker run -it \
  -e "SITE_NAME=edge.localhost" \
  -e "INSTALL_APPS=erpnext" \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge new

echo -e "${NEWLINE}${ULINE}Check New Edge Site${ENDULINE}"
sleep 3
RESTORE_STATUS=$(curl -sS http://edge.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -lt 60 ]]; do
  sleep 1
  echo -e "${ULINE}Wait for restoration to complete ...${ENDULINE}"
  RESTORE_STATUS=$(curl -sS http://edge.localhost/api/method/version || echo "")
  ((INCREMENT = INCREMENT + 1))
  if [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -eq 60 ]]; then
    CONTAINER_ID=$(docker-compose \
      --project-name frappebench00 \
      -f installation/docker-compose-common.yml \
      -f installation/docker-compose-erpnext.yml \
      -f installation/erpnext-publish.yml \
      ps -q erpnext-python)
    docker logs ${CONTAINER_ID}
    exit 1
  fi
done

echo -e "${NEWLINE}${ULINE}Ping new edge site${ENDULINE}"
echo ${RESTORE_STATUS}

echo -e "${NEWLINE}${ULINE}Check New Edge Index Page${ENDULINE}"
curl -s http://edge.localhost | w3m -T text/html -dump

echo -e "${NEWLINE}${ULINE}Migrate command in edge container${ENDULINE}"
docker run -it \
  -e "MAINTENANCE_MODE=1" \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  -v frappebench00_assets-vol:/home/frappe/frappe-bench/sites/assets \
  --network frappebench00_default \
  frappe/erpnext-worker:edge migrate

checkMigrationComplete

echo -e "${NEWLINE}${ULINE}Restore backup from MinIO / S3 (Overwrite)${ENDULINE}"
docker run \
  -e MYSQL_ROOT_PASSWORD=admin \
  -e BUCKET_NAME=erpnext \
  -e BUCKET_DIR=local \
  -e ACCESS_KEY_ID=${MINIO_ACCESS_KEY} \
  -e SECRET_ACCESS_KEY=${MINIO_SECRET_KEY} \
  -e ENDPOINT_URL=http://minio:9000 \
  -e REGION=us-east-1 \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge restore-backup

echo -e "${NEWLINE}${ULINE}Check Overwritten Site${ENDULINE}"
sleep 3
RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -lt 60 ]]; do
  sleep 1
  echo -e "${ULINE}Wait for restoration to complete ..."
  RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
  ((INCREMENT = INCREMENT + 1))
  if [[ -z "${RESTORE_STATUS}" && ${INCREMENT} -eq 60 ]]; then
    CONTAINER_ID=$(docker-compose \
      --project-name frappebench00 \
      -f installation/docker-compose-common.yml \
      -f installation/docker-compose-erpnext.yml \
      -f installation/erpnext-publish.yml \
      ps -q erpnext-python)
    docker logs ${CONTAINER_ID}
    exit 1
  fi
done

echo -e "${NEWLINE}${ULINE}Ping overwritten site${ENDULINE}"
echo ${RESTORE_STATUS}

echo -e "${NEWLINE}${ULINE}Check Overwritten Index Page${ENDULINE}"
curl -s http://test.localhost | w3m -T text/html -dump

echo -e "${NEWLINE}${ULINE}Check console command for site test.localhost${ENDULINE}"
docker run \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge console test.localhost

echo -e "${NEWLINE}${ULINE}Check console command for site pgsql.localhost${ENDULINE}"
docker run \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge console pgsql.localhost

echo -e "${NEWLINE}${ULINE}Check drop site: test.localhost (mariadb)${ENDULINE}"
docker run \
  -e SITE_NAME=test.localhost \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge drop

echo -e "${NEWLINE}${ULINE}Check drop site: pgsql.localhost (pgsql)${ENDULINE}"
docker run \
  -e SITE_NAME=pgsql.localhost \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  frappe/erpnext-worker:edge drop

echo -e "${NEWLINE}${ULINE}Check bench --help${ENDULINE}"
docker run \
  -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
  --network frappebench00_default \
  --user frappe \
  frappe/erpnext-worker:edge bench --help
