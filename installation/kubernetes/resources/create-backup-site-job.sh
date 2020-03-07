#!/bin/bash
set -e

if [[ -z "$SITE_NAME" ]]; then
    echo "SITE_NAME is not set"
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

envsubst '${TIMESTAMP}
    ${SITE_NAME}
    ${VERSION}
    ${SITES_PVC}' \
    < ./backupsitejob.yaml.template > backupsitejob-$SITE_NAME-$TIMESTAMP.yaml
