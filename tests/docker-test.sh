#!/bin/bash

function checkMigrationComplete() {
    echo "Check Migration"
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

    echo -e "\e[4mMigration Log\e[0m"
    docker logs $CONTAINER_ID
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

echo -e "\e[1m\e[4mCopy env-example file\e[0m"
cp env-example .env
echo -e "\n"

echo -e "\e[1m\e[4mSet version to v12\e[0m"
sed -i -e "s/edge/v12/g" .env
echo -e "\n"

echo -e "\e[1m\e[4mStart Services\e[0m"
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
echo -e "\n"

echo -e "\e[1m\e[4mCreate new site (v12)\e[0m"
docker run -it \
    -e "SITE_NAME=test.localhost" \
    -e "INSTALL_APPS=erpnext" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:v12 new
echo -e "\n"

echo -e "\e[1m\e[4mPing created site\e[0m"
curl -sS http://test.localhost/api/method/version
echo -e "\n"

echo -e "\e[1m\e[4mCheck Created Site Index Page\e[0m"
curl -s http://test.localhost | w3m -T text/html -dump
echo -e "\n"

echo -e "\e[1m\e[4mSet version to edge\e[0m"
sed -i -e "s/v12/edge/g" .env
echo -e "\n"

echo -e "\e[1m\e[4mRestart containers with edge image\e[0m"
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
echo -e "\n"

echo -e "\e[1m\e[4mPing migrated site\e[0m"
sleep 3
curl -sS http://test.localhost/api/method/version
echo -e "\n"

echo -e "\e[1m\e[4mCheck Migrated Site Index Page\e[0m"
curl -s http://test.localhost | w3m -T text/html -dump
echo -e "\n"

echo -e "\e[1m\e[4mCreate new site (pgsql)\e[0m"
docker run -it \
    -e "SITE_NAME=pgsql.localhost" \
    -e "POSTGRES_HOST=postgresql" \
    -e "DB_ROOT_USER=postgres" \
    -e "POSTGRES_PASSWORD=admin" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge new
echo -e "\n"

echo -e "\e[1m\e[4mCheck New PGSQL Site\e[0m"
sleep 3
RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "$RESTORE_STATUS" && $INCREMENT -lt 60 ]]; do
    sleep 1
    echo -e "\e[1m\e[4mWait for restoration to complete ..."
    RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
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
echo -e "\n"

echo -e "\e[1m\e[4mPing new pgsql site\e[0m"
echo $RESTORE_STATUS
echo -e "\n"

echo -e "\e[1m\e[4mCheck New PGSQL Index Page\e[0m"
curl -s http://pgsql.localhost | w3m -T text/html -dump
echo -e "\n"

echo -e "\e[1m\e[4mBackup site\e[0m"
docker run -it \
    -e "WITH_FILES=1" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge backup
echo -e "\n"

export MINIO_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
export MINIO_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

echo -e "\e[1m\e[4mStart MinIO container for s3 compatible storage\e[0m"
docker run -d --name minio \
  -e "MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY" \
  -e "MINIO_SECRET_KEY=$MINIO_SECRET_KEY" \
  --network frappebench00_default \
  minio/minio server /data
echo -e "\n"

echo -e "\e[1m\e[4mCreate bucket named erpnext\e[0m"
docker run \
    --network frappebench00_default \
    vltgroup/s3cmd:latest s3cmd --access_key=$MINIO_ACCESS_KEY \
    --secret_key=$MINIO_SECRET_KEY \
    --region=us-east-1 \
    --no-ssl \
    --host=minio:9000 \
    --host-bucket=minio:9000 \
    mb s3://erpnext
echo -e "\n"

echo -e "\e[1m\e[4mPush backup to MinIO s3\e[0m"
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
echo -e "\n"

echo -e "\e[1m\e[4mStop Services\e[0m"
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/erpnext-publish.yml \
    stop
echo -e "\n"

echo -e "\e[1m\e[4mPrune Containers\e[0m"
docker container prune -f && docker volume prune -f
echo -e "\n"

echo -e "\e[1m\e[4mStart Services\e[0m"
docker-compose \
    --project-name frappebench00 \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/erpnext-publish.yml \
    up -d

loopHealthCheck
echo -e "\n"

echo -e "\e[1m\e[4mRestore backup from MinIO / S3\e[0m"
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
echo -e "\n"

echo -e "\e[1m\e[4mCheck Restored Site (test)\e[0m"
sleep 3
RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "$RESTORE_STATUS" && $INCREMENT -lt 60 ]]; do
    sleep 1
    echo "Wait for restoration to complete ..."
    RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
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

echo -e "\e[1m\e[4mPing restored site (test)\e[0m"
echo $RESTORE_STATUS
echo -e "\n"

echo -e "\e[1m\e[4mCheck Restored Site Index Page (test)\e[0m"
curl -s http://test.localhost | w3m -T text/html -dump
echo -e "\n"

echo -e "\e[1m\e[4mCheck Restored Site (pgsql)\e[0m"
sleep 3
RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "$RESTORE_STATUS" && $INCREMENT -lt 60 ]]; do
    sleep 1
    echo "Wait for restoration to complete ..."
    RESTORE_STATUS=$(curl -sS http://pgsql.localhost/api/method/version || echo "")
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

echo -e "\e[1m\e[4mPing restored site (pgsql)\e[0m"
echo $RESTORE_STATUS
echo -e "\n"

echo -e "\e[1m\e[4mCheck Restored Site Index Page (pgsql)\e[0m"
curl -s http://pgsql.localhost | w3m -T text/html -dump
echo -e "\n"

echo -e "\e[1m\e[4mCreate new site (edge)\e[0m"
docker run -it \
    -e "SITE_NAME=edge.localhost" \
    -e "INSTALL_APPS=erpnext" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge new
echo -e "\n"

echo -e "\e[1m\e[4mCheck New Edge Site\e[0m"
sleep 3
RESTORE_STATUS=$(curl -sS http://edge.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "$RESTORE_STATUS" && $INCREMENT -lt 60 ]]; do
    sleep 1
    echo -e "\e[1m\e[4mWait for restoration to complete ..."
    RESTORE_STATUS=$(curl -sS http://edge.localhost/api/method/version || echo "")
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
echo -e "\n"

echo -e "\e[1m\e[4mPing new edge site\e[0m"
echo $RESTORE_STATUS
echo -e "\n"

echo -e "\e[1m\e[4mCheck New Edge Index Page\e[0m"
curl -s http://edge.localhost | w3m -T text/html -dump
echo -e "\n"

echo -e "\e[1m\e[4mMigrate command in edge container\e[0m"
docker run -it \
    -e "MAINTENANCE_MODE=1" \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    -v frappebench00_assets-vol:/home/frappe/frappe-bench/sites/assets \
    --network frappebench00_default \
    frappe/erpnext-worker:edge migrate

checkMigrationComplete
echo -e "\n"

echo -e "\e[1m\e[4mRestore backup from MinIO / S3 (Overwrite)\e[0m"
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
echo -e "\n"

echo -e "\e[1m\e[4mCheck Overwritten Site\e[0m"
sleep 3
RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
INCREMENT=0
while [[ -z "$RESTORE_STATUS" && $INCREMENT -lt 60 ]]; do
    sleep 1
    echo -e "\e[1m\e[4mWait for restoration to complete ..."
    RESTORE_STATUS=$(curl -sS http://test.localhost/api/method/version || echo "")
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
echo -e "\n"

echo -e "\e[1m\e[4mPing overwritten site\e[0m"
echo $RESTORE_STATUS
echo -e "\n"

echo -e "\e[1m\e[4mCheck Overwritten Index Page\e[0m"
curl -s http://test.localhost | w3m -T text/html -dump
echo -e "\n"

echo -e "\e[1m\e[4mCheck console command for site test.localhost\e[0m"
docker run \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge console test.localhost

echo -e "\e[1m\e[4mCheck console command for site pgsql.localhost\e[0m"
docker run \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge console pgsql.localhost

echo -e "\e[1m\e[4mCheck drop site: test.localhost (mariadb)\e[0m"
docker run \
    -e SITE_NAME=test.localhost \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge drop

echo -e "\e[1m\e[4mCheck drop site: pgsql.localhost (pgsql)\e[0m"
docker run \
    -e SITE_NAME=pgsql.localhost \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    frappe/erpnext-worker:edge drop

echo -e "\e[1m\e[4mCheck bench --help\e[0m"
docker run \
    -v frappebench00_sites-vol:/home/frappe/frappe-bench/sites \
    --network frappebench00_default \
    --user frappe \
    frappe/erpnext-worker:edge bench --help
