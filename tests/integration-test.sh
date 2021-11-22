#!/bin/bash

set -e

source tests/functions.sh

project_name=frappe_bench_00

docker_compose_with_args() {
    # shellcheck disable=SC2068
    docker-compose \
        -p $project_name \
        -f installation/docker-compose-common.yml \
        -f installation/docker-compose-frappe.yml \
        -f installation/frappe-publish.yml \
        $@
}

check_migration_complete() {
    print_group Check migration

    container_id=$(docker_compose_with_args ps -q frappe-python)
    cmd="docker logs ${container_id} 2>&1 | grep 'Starting gunicorn' || echo ''"
    worker_log=$(eval "$cmd")
    INCREMENT=0

    while [[ ${worker_log} != *"Starting gunicorn"* && ${INCREMENT} -lt 120 ]]; do
        sleep 3
        ((INCREMENT = INCREMENT + 1))
        echo "Wait for migration to complete..."
        worker_log=$(eval "$cmd")
        if [[ ${worker_log} != *"Starting gunicorn"* && ${INCREMENT} -eq 120 ]]; then
            echo Migration timeout
            docker logs "${container_id}"
            exit 1
        fi
    done

    echo Migration Log
    docker logs "${container_id}"
}

check_health() {
    print_group Loop health check

    docker run --name frappe_doctor \
        -v "${project_name}_sites-vol:/home/frappe/frappe-bench/sites" \
        --network "${project_name}_default" \
        frappe/frappe-worker:edge doctor || true

    cmd='docker logs frappe_doctor | grep "Health check successful" || echo ""'
    doctor_log=$(eval "$cmd")
    INCREMENT=0

    while [[ -z "${doctor_log}" && ${INCREMENT} -lt 60 ]]; do
        sleep 1
        ((INCREMENT = INCREMENT + 1))
        container=$(docker start frappe_doctor)
        echo "Restarting ${container}..."
        doctor_log=$(eval "$cmd")

        if [[ ${INCREMENT} -eq 60 ]]; then
            docker logs "${container}"
            exit 1
        fi
    done
}

# Initial group
echo ::group::Setup .env
cp env-example .env
sed -i -e "s/edge/v13/g" .env
cat .env
# shellcheck disable=SC2046
export $(cat .env)

print_group Start services
echo Start main services
docker_compose_with_args up -d --quiet-pull

echo Start postgres
docker pull postgres:11.8 -q
docker run \
    --name postgresql \
    -d \
    -e POSTGRES_PASSWORD=admin \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    postgres:11.8

check_health

print_group "Create new site "
SITE_NAME=test.localhost
docker run \
    --rm \
    -e SITE_NAME=$SITE_NAME \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:v13 new

ping_site

print_group "Update .env (v13 -> edge)"
sed -i -e "s/v13/edge/g" .env
cat .env
# shellcheck disable=SC2046
export $(cat .env)

print_group Restart containers
docker_compose_with_args stop
docker_compose_with_args up -d

check_migration_complete
sleep 5
ping_site

PG_SITE_NAME=pgsql.localhost
print_group "Create new site (Postgres)"
docker run \
    --rm \
    -e SITE_NAME=$PG_SITE_NAME \
    -e POSTGRES_HOST=postgresql \
    -e DB_ROOT_USER=postgres \
    -e POSTGRES_PASSWORD=admin \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge new

check_migration_complete
SITE_NAME=$PG_SITE_NAME ping_site

print_group Backup site
docker run \
    --rm \
    -e WITH_FILES=1 \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge backup

MINIO_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
MINIO_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

print_group Prepare S3 server
echo Start S3 server
docker run \
    --name minio \
    -d \
    -e "MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY" \
    -e "MINIO_SECRET_KEY=$MINIO_SECRET_KEY" \
    --network ${project_name}_default \
    minio/minio server /data

echo Create bucket
docker run \
    --rm \
    --network ${project_name}_default \
    vltgroup/s3cmd:latest \
    s3cmd \
    --access_key=$MINIO_ACCESS_KEY \
    --secret_key=$MINIO_SECRET_KEY \
    --region=us-east-1 \
    --no-ssl \
    --host=minio:9000 \
    --host-bucket=minio:9000 \
    mb s3://frappe

print_group Push backup
docker run \
    --rm \
    -e BUCKET_NAME=frappe \
    -e REGION=us-east-1 \
    -e BUCKET_DIR=local \
    -e ACCESS_KEY_ID=$MINIO_ACCESS_KEY \
    -e SECRET_ACCESS_KEY=$MINIO_SECRET_KEY \
    -e ENDPOINT_URL=http://minio:9000 \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge push-backup

print_group Prune and restart services
docker_compose_with_args stop
docker container prune -f && docker volume prune -f
docker_compose_with_args up -d

check_health

print_group Restore backup from S3
docker run \
    --rm \
    -e MYSQL_ROOT_PASSWORD=admin \
    -e BUCKET_NAME=frappe \
    -e BUCKET_DIR=local \
    -e ACCESS_KEY_ID=$MINIO_ACCESS_KEY \
    -e SECRET_ACCESS_KEY=$MINIO_SECRET_KEY \
    -e ENDPOINT_URL=http://minio:9000 \
    -e REGION=us-east-1 \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge restore-backup

check_health
ping_site
SITE_NAME=$PG_SITE_NAME ping_site

EDGE_SITE_NAME=edge.localhost
print_group "Create new site (edge)"
docker run \
    --rm \
    -e SITE_NAME=$EDGE_SITE_NAME \
    -e INSTALL_APPS=frappe \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge new

check_health
SITE_NAME=$EDGE_SITE_NAME ping_site

print_group Migrate edge site
docker run \
    --rm \
    -e MAINTENANCE_MODE=1 \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    -v ${project_name}_assets-vol:/home/frappe/frappe-bench/sites/assets \
    --network ${project_name}_default \
    frappe/frappe-worker:edge migrate

check_migration_complete

print_group "Restore backup S3 (overwrite)"
docker run \
    --rm \
    -e MYSQL_ROOT_PASSWORD=admin \
    -e BUCKET_NAME=frappe \
    -e BUCKET_DIR=local \
    -e ACCESS_KEY_ID=$MINIO_ACCESS_KEY \
    -e SECRET_ACCESS_KEY=$MINIO_SECRET_KEY \
    -e ENDPOINT_URL=http://minio:9000 \
    -e REGION=us-east-1 \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge restore-backup

check_migration_complete
ping_site

print_group "Check console for $SITE_NAME"
docker run \
    --rm \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge console $SITE_NAME

print_group "Check console for $PG_SITE_NAME"
docker run \
    --rm \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge console $PG_SITE_NAME

print_group "Check drop site for $SITE_NAME (MariaDB)"
docker run \
    --rm \
    -e SITE_NAME=$SITE_NAME \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge drop

print_group "Check drop site for $PG_SITE_NAME (Postgres)"
docker run \
    --rm \
    -e SITE_NAME=$PG_SITE_NAME \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:edge drop

print_group Check bench --help
docker run \
    --rm \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    --user frappe \
    frappe/frappe-worker:edge bench --help
