#!/bin/bash
set -e
set -x

APP=$1

cd /home/frappe/frappe-bench

env/bin/pip install -e "apps/$APP"

echo "$APP" >>sites/apps.txt
