#!/bin/bash

APP_NAME=${1}
APP_REPO=${2}
APP_BRANCH=${3}

cd /home/frappe/frappe-bench/

. env/bin/activate

cd ./apps

[ "${APP_BRANCH}" ] && BRANCH="-b ${APP_BRANCH}"

git clone --depth 1 -o upstream ${APP_REPO} ${BRANCH}
pip3 install --no-cache-dir -e /home/frappe/frappe-bench/apps/${APP_NAME}