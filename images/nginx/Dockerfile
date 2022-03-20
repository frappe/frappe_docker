FROM node:14-bullseye-slim as assets_builder

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    git \
    build-essential \
    python \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /frappe-bench

RUN mkdir -p sites/assets /out/assets \
    && echo frappe >sites/apps.txt

ARG FRAPPE_VERSION
RUN git clone --depth 1 -b ${FRAPPE_VERSION} https://github.com/frappe/frappe apps/frappe

# Install development node modules
RUN yarn --cwd apps/frappe \
    # TODO: Currently `yarn run production` doesn't create .build on develop branch: https://github.com/frappe/frappe/issues/15396
    && if [ ! -f sites/.build ]; then touch sites/.build; fi \
    && cp sites/.build /out

COPY install-app.sh /usr/local/bin/install-app


FROM assets_builder as frappe_assets

RUN install-app frappe


FROM assets_builder as erpnext_assets

ARG ERPNEXT_VERSION
RUN install-app erpnext ${ERPNEXT_VERSION} https://github.com/frappe/erpnext


FROM alpine/git as bench

# Error pages
RUN git clone --depth 1 https://github.com/frappe/bench /tmp/bench \
    && mkdir /out \
    && mv /tmp/bench/bench/config/templates/502.html /out/


FROM nginxinc/nginx-unprivileged:1.21.6-alpine as frappe

# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/20-envsubst-on-templates.sh
COPY nginx-template.conf /etc/nginx/templates/default.conf.template
# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/docker-entrypoint.sh
COPY entrypoint.sh /docker-entrypoint.d/frappe-entrypoint.sh

COPY --from=bench /out /usr/share/nginx/html/
COPY --from=frappe_assets /out /usr/share/nginx/html

USER 1000


FROM frappe as erpnext

COPY --from=erpnext_assets /out /usr/share/nginx/html
