#!/bin/bash
set -e

if [[ -z "$SITE_NAME" ]]; then
    echo "SITE_NAME is not set"
    exit 1
fi
if [[ -z "$DB_ROOT_USER" ]]; then
    echo "DB_ROOT_USER is not set"
    exit 1
fi
if [[ -z "$ADMIN_PASSWORD" ]]; then
    echo "ADMIN_PASSWORD is not set"
    exit 1
fi
if [[ -z "$SITES_PVC" ]]; then
    echo "SITES_PVC is not set"
    exit 1
fi
if [[ -z "$VERSION" ]]; then
    echo "VERSION is not set"
    exit 1
fi

export TIMESTAMP=$(date +%s)

envsubst '${SITE_NAME}
    ${DB_ROOT_USER}
    ${ADMIN_PASSWORD}
    ${SITES_PVC}
    ${SITE_NAME}
    ${VERSION}' \
    < ./newsitejob.yaml.template > newsitejob-$SITE_NAME-$TIMESTAMP.yaml
