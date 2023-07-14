#!/bin/bash

source ./ci/build.env

export APPS_JSON_BASE64=$(base64 -w 0 ./ci/apps.json)

TAG="${1:-selen_frappe:latest}"

aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 119186933498.dkr.ecr.ap-southeast-1.amazonaws.com

docker build \
  --build-arg FRAPPE_PATH="$FRAPPE_PATH" \
  --build-arg FRAPPE_BRANCH="$FRAPPE_BRANCH" \
  --build-arg PYTHON_VERSION="$PYTHON_VERSION" \
  --build-arg NODE_VERSION="$NODE_VERSION" \
  --build-arg APPS_JSON_BASE64="$APPS_JSON_BASE64" \
  --tag "$TAG"\
  ./ci

docker tag ${TAG} 119186933498.dkr.ecr.ap-southeast-1.amazonaws.com/selen_frappe:latest

docker push 119186933498.dkr.ecr.ap-southeast-1.amazonaws.com/selen_frappe:latest
