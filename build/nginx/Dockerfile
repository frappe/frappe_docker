FROM node:14-bullseye-slim as base

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    git \
    build-essential \
    python \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/frappe-bench
RUN mkdir -p apps sites/assets/frappe

ARG FRAPPE_VERSION
RUN git clone --depth 1 -b ${FRAPPE_VERSION} https://github.com/frappe/frappe apps/frappe \
    && echo "frappe" >sites/apps.txt

WORKDIR /root/frappe-bench/apps/frappe


FROM base as frappe_node_modules

RUN yarn --prod


FROM frappe_node_modules as frappe_assets

RUN if [ "$(uname -m)" = "aarch64" ]; then \
    yarn remove svg-sprite || true \
    && yarn add sass; \
    fi \
    && yarn

RUN yarn run production \
    && cp -R frappe/public/* ../../sites/assets/frappe \
    && rm ../../sites/apps.txt

# Get rid of development node modules
COPY --from=frappe_node_modules /root/frappe-bench/apps/frappe/node_modules /root/frappe-bench/sites/assets/frappe/


FROM base as erpnext_node_modules

ARG ERPNEXT_VERSION
RUN cd ../.. \
    && git clone --depth 1 -b ${ERPNEXT_VERSION} https://github.com/frappe/erpnext apps/erpnext \
    && echo "frappe\nerpnext" >sites/apps.txt

RUN yarn --cwd ../erpnext --prod


FROM erpnext_node_modules as erpnext_assets

RUN mkdir -p ../../sites/assets/erpnext
RUN yarn --cwd ../erpnext

# Reuse development node_modules from frappe_assets
COPY --from=frappe_assets /root/frappe-bench/apps/frappe/node_modules /root/frappe-bench/apps/frappe/node_modules
COPY --from=frappe_assets /root/frappe-bench/apps/frappe/package.json /root/frappe-bench/apps/frappe/yarn.lock /root/frappe-bench/apps/frappe/

RUN yarn run production --app erpnext \
    && cp -R ../erpnext/erpnext/public/* ../../sites/assets/erpnext \
    && rm ../../sites/apps.txt

# Get rid of development node modules
COPY --from=erpnext_node_modules /root/frappe-bench/apps/erpnext/node_modules /root/frappe-bench/apps/erpnext/node_modules


FROM base as error_pages

RUN git clone --depth 1 https://github.com/frappe/bench /root/bench


FROM nginx:1.21-alpine as frappe

COPY --from=error_pages /root/bench/bench/config/templates/502.html /usr/share/nginx/html
COPY --from=frappe_assets /root/frappe-bench/sites /usr/share/nginx/html
COPY nginx-template.conf /

CMD [ "/bin/sh" , "-c" , "envsubst '${BACKEND} ${SOCKETIO} ${FRAPPE_SITE_NAME_HEADER}' </nginx-template.conf >/etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'" ]


FROM frappe as erpnext

COPY --from=erpnext_assets /root/frappe-bench/sites /usr/share/nginx/html
