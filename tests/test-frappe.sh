#!/bin/bash

set -e

source tests/functions.sh

project_name="test_frappe"
SITE_NAME="test_frappe.localhost"

echo ::group::Setup env
cp env-example .env
sed -i -e "s/edge/test/g" .env
# shellcheck disable=SC2046
export $(cat .env)
cat .env

print_group Start services
FRAPPE_VERSION="test" \
    docker-compose \
    -p $project_name \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-frappe.yml \
    -f installation/frappe-publish.yml \
    up -d

print_group Create site
docker run \
    --rm \
    -e "SITE_NAME=$SITE_NAME" \
    -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
    --network ${project_name}_default \
    frappe/frappe-worker:test new

ping_site
rm .env
