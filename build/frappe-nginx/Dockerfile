# This image uses nvm and same base image as the worker image.
# This is done to ensures that node-sass binary remains common.
# node-sass is required to enable website theme feature used
# by Website Manager role in Frappe Framework
ARG IMAGE_TAG=v10
ARG DOCKER_REGISTRY_PREFIX=frappe
FROM ${DOCKER_REGISTRY_PREFIX}/frappe-worker:${IMAGE_TAG}

RUN npm i yarn -g \
    && cd /home/frappe/frappe-bench/apps/frappe \
    && rm -fr node_modules && yarn \
    && cd /home/frappe/frappe-bench/sites \
    && echo "frappe" > /home/frappe/frappe-bench/sites/apps.txt \
    && /home/frappe/frappe-bench/env/bin/python -c "import frappe; frappe.init(''); import frappe.build; frappe.build.setup(); frappe.build.make_asset_dirs(make_copy=True)" \
    && node --use_strict ../apps/frappe/frappe/build.js --build \
    && mkdir -p /home/frappe/sites \
    && cp -R assets /home/frappe/sites

RUN git clone --depth 1 https://github.com/frappe/bench /tmp/bench \
    && mkdir -p /home/frappe/www/error_pages \
    && cp -r /tmp/bench/bench/config/templates /home/frappe/www/error_pages

FROM nginx:latest
COPY --from=0 /home/frappe/sites /var/www/html
COPY --from=0 /home/frappe/www/error_pages /var/www/
COPY build/common/nginx-default.conf.template /etc/nginx/conf.d/default.conf.template
COPY build/frappe-nginx/docker-entrypoint.sh /

RUN apt-get update && apt-get install -y rsync && apt-get clean

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
