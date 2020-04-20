#!/bin/bash
set -e

if [[ -z "$INGRESS_NAME" ]]; then
    echo "INGRESS_NAME is not set"
    exit 1
fi
if [[ -z "$FRAPPE_SERVICE" ]]; then
    echo "FRAPPE_SERVICE is not set"
    exit 1
fi
if [[ -z "$SITE_NAME" ]]; then
    echo "SITE_NAME is not set"
    exit 1
fi
if [[ -z "$TLS_SECRET_NAME" ]]; then
    echo "TLS_SECRET_NAME is not set"
    exit 1
fi

envsubst '${INGRESS_NAME}
    ${FRAPPE_SERVICE}
    ${SITE_NAME}
    ${TLS_SECRET_NAME}' \
    < ./newsiteingress.yaml.template > newsiteingress_$SITE_NAME.yaml
