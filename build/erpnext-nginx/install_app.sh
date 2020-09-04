#!/bin/bash

APP_NAME=${1}
APP_REPO=${2}
APP_BRANCH=${3}

[ "${APP_BRANCH}" ] && BRANCH="-b ${APP_BRANCH}"

mkdir -p /home/frappe/frappe-bench/sites/assets
cd /home/frappe/frappe-bench
echo -e "frappe\n${APP_NAME}" > /home/frappe/frappe-bench/sites/apps.txt

install_packages git python2

mkdir -p apps
cd apps
git clone --depth 1 https://github.com/frappe/frappe ${BRANCH}
git clone --depth 1 ${APP_REPO} ${BRANCH}

cd /home/frappe/frappe-bench/apps/frappe
yarn
yarn production --app ${APP_NAME}
rm -fr node_modules
yarn install --production=true
yarn add node-sass

mkdir -p /home/frappe/frappe-bench/sites/assets/${APP_NAME}
cp -R /home/frappe/frappe-bench/apps/${APP_NAME}/${APP_NAME}/public/* /home/frappe/frappe-bench/sites/assets/${APP_NAME}

# Add frappe and all the apps available under in frappe-bench here
echo "rsync -a --delete /var/www/html/assets/frappe /assets" > /rsync
echo "rsync -a --delete /var/www/html/assets/${APP_NAME} /assets" >> /rsync
chmod +x /rsync

rm /home/frappe/frappe-bench/sites/apps.txt
