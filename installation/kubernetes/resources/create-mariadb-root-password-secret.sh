#!/bin/bash
set -e

if [[ -z "$BASE64_PASSWORD" ]]; then
    echo "BASE64_PASSWORD is not set"
    exit 1
fi

envsubst '${BASE64_PASSWORD}' \
    < ./mariadbrootpasswordsecret.yaml.template > ./mariadbrootpasswordsecret.yaml
