#!/bin/bash
set -e

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
    ${VERSION}
    ${SITES_PVC}' \
    < ./migratesitesjob.yaml.template > migratesitesjob-$TIMESTAMP.yaml
