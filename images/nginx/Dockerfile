FROM node:14-bullseye-slim as base

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    git \
    build-essential \
    python \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/frappe-bench
RUN mkdir -p sites/assets

ARG FRAPPE_VERSION
RUN git clone --depth 1 -b ${FRAPPE_VERSION} https://github.com/frappe/frappe apps/frappe



FROM base as frappe_prod_node_modules

# Install production node modules
RUN yarn --cwd apps/frappe --prod



FROM frappe_prod_node_modules as frappe_assets

# Install development node modules
RUN yarn --cwd apps/frappe

# Build assets they're stored in frappe-bench/sites/assets
RUN echo "frappe" >sites/apps.txt \
    && yarn --cwd apps/frappe run production \
    && rm sites/apps.txt \
    # TODO: Currently `yarn run production` doesn't create .build on develop branch: https://github.com/frappe/frappe/issues/15396
    && if [ ! -f sites/.build ]; then touch sites/.build; fi



FROM base as erpnext_prod_node_modules

ARG ERPNEXT_VERSION
RUN git clone --depth 1 -b ${ERPNEXT_VERSION} https://github.com/frappe/erpnext apps/erpnext

RUN yarn --cwd apps/erpnext --prod



FROM erpnext_prod_node_modules as erpnext_assets

RUN yarn --cwd apps/erpnext

COPY --from=frappe_assets /root/frappe-bench/apps/frappe/node_modules /root/frappe-bench/apps/frappe/node_modules
COPY --from=frappe_assets /root/frappe-bench/apps/frappe/package.json /root/frappe-bench/apps/frappe/yarn.lock /root/frappe-bench/apps/frappe/

RUN echo "frappe\nerpnext" >sites/apps.txt \
    && yarn --cwd apps/frappe run production --app erpnext \
    && rm sites/apps.txt



FROM base as error_pages

RUN git clone --depth 1 https://github.com/frappe/bench /root/bench



FROM nginxinc/nginx-unprivileged:1.21.6-alpine as frappe

COPY --from=error_pages /root/bench/bench/config/templates/502.html /usr/share/nginx/html
COPY --from=base /root/frappe-bench/apps/frappe/frappe/public /usr/share/nginx/html/assets/frappe
COPY --from=frappe_prod_node_modules /root/frappe-bench/apps/frappe/node_modules /usr/share/nginx/html/assets/frappe/node_modules
COPY --from=frappe_assets /root/frappe-bench/sites /usr/share/nginx/html

# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/20-envsubst-on-templates.sh
COPY nginx-template.conf /etc/nginx/templates/default.conf.template
# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/docker-entrypoint.sh
COPY entrypoint.sh /docker-entrypoint.d/frappe-entrypoint.sh

USER 1000



FROM frappe as erpnext

COPY --from=erpnext_prod_node_modules /root/frappe-bench/apps/erpnext/erpnext/public /usr/share/nginx/html/assets/erpnext
COPY --from=erpnext_prod_node_modules /root/frappe-bench/apps/erpnext/node_modules /usr/share/nginx/html/assets/erpnext/node_modules
COPY --from=erpnext_assets /root/frappe-bench/sites /usr/share/nginx/html
