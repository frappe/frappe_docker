#!/bin/bash

APP_NAME=${1}
APP_REPO=${2}

cd /home/frappe/frappe-bench/

. env/bin/activate

cd apps

git clone --depth 1 -o upstream ${APP_REPO}
pip3 install --no-cache-dir -e /home/frappe/frappe-bench/apps/APP_NAME