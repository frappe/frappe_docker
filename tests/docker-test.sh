#!/bin/bash

function checkMigrationComplete() {
    echo "Check Auto Migration"
    CONTAINER_ID=$(docker-compose \
        --project-name frappebench00 \
        -f installation/docker-compose-common.yml \
        -f installation/docker-compose-erpnext.yml \
        -f installation/erpnext-publish.yml \
        ps -q erpnext-python)

    DOCKER_LOG=$(docker logs $CONTAINER_ID 2>&1 | grep "Starting gunicorn")
    INCREMENT=0
    while [[ $DOCKER_LOG != *"Starting gunicorn"* && $INCREMENT -lt 60 ]]; do
        sleep 3
        echo "Wait for migration to complete ..."
        ((INCREMENT=INCREMENT+1))
        DOCKER_LOG=$(docker logs $CONTAINER_ID 2>&1 | grep "Starting gunicorn")
        if [[ $DOCKER_LOG != *"Starting gunicorn"* && $INCREMENT -eq 60  ]]; then
            docker logs $CONTAINER_ID
            exit 1
        fi
    done
}

function loopHealthCheck() {
    echo "Create Container to Check MariaDB"
    docker run --name frappe_doctor \
        -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
        --network frappebench00_default \
        frappe/erpnext-worker:edge doctor || true

    echo "Loop Health Check"
    FRAPPE_LOG=$(docker logs frappe_doctor | grep "Health check successful" || echo "")
    while [[ -z "$FRAPPE_LOG" ]]; do
        sleep 1
        CONTAINER=$(docker start frappe_doctor)
        echo "Restarting $CONTAINER ..."
        FRAPPE_LOG=$(docker logs frappe_doctor | grep "Health check successful" || echo "")
    done
    echo "Health check successful"
}

echo "Copy env-example file"
cp env-example .env

echo "Set version to v12"
sed -i -e "s/edge/v12/g" .env

echo "Start Services"
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/erpnext-publish.yml \
    up -d

loopHealthCheck

echo "Create new site (v12)"
docker run -it \
    -e "SITE_NAME=test.localhost" \
    -e "INSTALL_APPS=erpnext" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:v12 new

echo "Ping created site"
curl -S http://test.localhost/api/method/version
echo ""

echo "Set version to edge"
sed -i -e "s/v12/edge/g" .env

echo "Restart containers with edge image"
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

echo "Ping migrated site"
sleep 3
curl -S http://test.localhost/api/method/version
echo ""

echo "Backup site"
docker run -it \
    -e "WITH_FILES=1" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge backup

export MINIO_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
export MINIO_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

echo "Start MinIO container for s3 compatible storage"
docker run -d --name minio \
  -e "MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY" \
  -e "MINIO_SECRET_KEY=$MINIO_SECRET_KEY" \
  --network frappebench00_default \
  minio/minio server /data

echo "Create bucket named erpnext after 3 sec."
sleep 3
docker run \
    --network frappebench00_default \
    vltgroup/s3cmd:latest s3cmd --access_key=$MINIO_ACCESS_KEY \
    --secret_key=$MINIO_SECRET_KEY \
    --region=us-east-1 \
    --no-ssl \
    --host=minio:9000 \
    --host-bucket=minio:9000 \
    mb s3://erpnext

echo "Push backup to MinIO s3"
docker run \
    -e BUCKET_NAME=erpnext \
    -e REGION=us-east-1 \
    -e BUCKET_DIR=local \
    -e ACCESS_KEY_ID=$MINIO_ACCESS_KEY \
    -e SECRET_ACCESS_KEY=$MINIO_SECRET_KEY \
    -e ENDPOINT_URL=http://minio:9000 \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge push-backup

echo "Stop Services"
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/erpnext-publish.yml \
    stop

echo "Prune Containers"
docker container prune -f && docker volume prune -f

echo "Start Services"
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/erpnext-publish.yml \
    up -d

loopHealthCheck

echo "Restore backup from MinIO / S3"
docker run \
    -e MYSQL_ROOT_PASSWORD=admin \
    -e BUCKET_NAME=erpnext \
    -e BUCKET_DIR=local \
    -e ACCESS_KEY_ID=$MINIO_ACCESS_KEY \
    -e SECRET_ACCESS_KEY=$MINIO_SECRET_KEY \
    -e ENDPOINT_URL=http://minio:9000 \
    -e REGION=us-east-1 \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge restore-backup

echo "Check Restored Site"
sleep 3
RESTORE_STATUS=$(curl -S http://test.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "$RESTORE_STATUS" && $INCREMENT -lt 60 ]]; do
    sleep 1
    echo "Wait for restoration to complete ..."
    RESTORE_STATUS=$(curl -S http://test.localhost/api/method/version || echo "")
    ((INCREMENT=INCREMENT+1))
    if [[ -z "$RESTORE_STATUS" && $INCREMENT -eq 60 ]]; then
        CONTAINER_ID=$(docker-compose \
            --project-name frappebench00 \
            -f installation/docker-compose-common.yml \
            -f installation/docker-compose-erpnext.yml \
            -f installation/erpnext-publish.yml \
            ps -q erpnext-python)
        docker logs $CONTAINER_ID
        exit 1
    fi
done

echo "Ping restored site"
echo $RESTORE_STATUS

echo "Migrate command in edge container"
docker run -it \
    -e "MAINTENANCE_MODE=1" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge migrate

checkMigrationComplete

echo "Create new site (edge)"
docker run -it \
    -e "SITE_NAME=edge.localhost" \
    -e "INSTALL_APPS=erpnext" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge new

echo "Check console command for site test.localhost"
docker run \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge console test.localhost
