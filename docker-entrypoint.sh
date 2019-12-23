#!/bin/bash

chown -R 500:500 "${BENCH}"

# Setup bench
if [[ ! -d "${BENCH}/sites" ]]; then
    su-exec frappe bench init "${BENCH}" --ignore-exist --skip-redis-config-generation --verbose
fi

# Make sure Redis is up
dockerize -wait "tcp://${REDIS_CACHE_HOST}:13000" -wait "tcp://${REDIS_QUEUE_HOST}:11000" -wait "tcp://${REDIS_SOCKETIO_HOST}:12000"
# Make sure MariaDB is up
dockerize -wait "tcp://${MARIADB_HOST}:3306"

# Individualy add bench config file
dockerize -template /home/frappe/templates/procfile.tmpl:${BENCH}/Procfile # Procfile
dockerize -template /home/frappe/templates/common_site_config.tmpl:${BENCH}/sites/common_site_config.json # common_site_config.json
dockerize -template /home/frappe/templates/nginx.tmpl:/etc/nginx/conf.d/frappe.conf # Nginx config for Frappe
dockerize -template /home/frappe/templates/supervisord.tmpl:/etc/supervisor/conf.d/frappe.conf # Supervisor config for Frappe Services

cd "${BENCH}" || exit 1

# Add a site if its not there (useful if you're doing multitenancy)
if [[ ! -d "${BENCH}/sites/${SITE_NAME}" ]]; then
     su-exec frappe bench new-site "${SITE_NAME}" --verbose
fi

# Make sure frappe is built
su-exec frappe bench build

# Print all configuration
function output () {
    TITLE=$2 NAME=${3:-$(echo "$1" | grep -o '\([^\/\\]\+\.\w\+\)$')} awk 'BEGIN{print "\033[1;36m" ENVIRON["TITLE"] \
    ":\n\033[0;31m" ENVIRON["NAME"] "\t|\033[1;31m ------------------------------------------------------------------------\033[0m"} \
    {print "\033[0;31m" ENVIRON["NAME"] "\t| \033[0m" $0} END{print "\033[0;31m" \
    ENVIRON["NAME"] "\t|\033[1;31m ------------------------------------------------------------------------\033[0m\n"}' $1
}

echo -e "\n\033[1;36mConfiguration:"
output ${BENCH}/Procfile "Bench Procfile"
output ${BENCH}/sites/common_site_config.json "Bench Common Site Config"
output /etc/nginx/nginx.conf "Nginx config"
output /etc/nginx/conf.d/frappe.conf "Nginx frappe conf"
output /etc/supervisor/supervisord.conf "Supervisord config"
output /etc/supervisor/conf.d/frappe.conf "Supervisord frappe conf"

trap "killall \"supervisord\"" HUP INT QUIT TERM

# Start all services
exec supervisord
