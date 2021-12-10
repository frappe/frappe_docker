#!/bin/bash

set -e

source tests/functions.sh

project_name="test_erpnext"
SITE_NAME="test_erpnext.localhost"

echo ::group::Setup env
cp env-example .env
sed -i -e "s/edge/test/g" .env
# shellcheck disable=SC2046
export $(cat .env)
cat .env

print_group Start services
docker-compose \
  -p $project_name \
  -f installation/docker-compose-common.yml \
  -f installation/docker-compose-erpnext.yml \
  -f installation/erpnext-publish.yml \
  up -d

print_group Fix permissions
docker run \
  --rm \
  --user root \
  -v ${project_name}_sites-vol:/sites \
  -v ${project_name}_assets-vol:/assets \
  -v ${project_name}_logs-vol:/logs \
  frappe/erpnext-worker:test chown -R 1000:1000 /logs /sites /assets

print_group Create site
docker run \
  --rm \
  -e "SITE_NAME=$SITE_NAME" \
  -e "INSTALL_APPS=erpnext" \
  -v ${project_name}_sites-vol:/home/frappe/frappe-bench/sites \
  --network ${project_name}_default \
  frappe/erpnext-worker:test new

ping_site
rm .env
