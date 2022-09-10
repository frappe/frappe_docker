FROM frappe/bench:latest as assets_builder

USER root

WORKDIR /builds

RUN chown -R frappe:frappe /builds

USER frappe

ARG FRAPPE_VERSION
ARG FRAPPE_REPO=https://github.com/frappe/frappe
RUN bench init --version=${FRAPPE_VERSION} --frappe-path=${FRAPPE_REPO} --skip-redis-config-generation --verbose --skip-assets /builds/bench

WORKDIR /builds/bench


FROM assets_builder as frappe_assets

RUN bench setup requirements \
    && bench build --production --verbose --hard-link


FROM assets_builder as erpnext_assets

ARG ERPNEXT_VERSION
ARG ERPNEXT_REPO=https://github.com/frappe/erpnext
RUN bench get-app --branch=${ERPNEXT_VERSION} --skip-assets --resolve-deps erpnext ${ERPNEXT_REPO}\
    && bench build --production --verbose --hard-link


FROM alpine/git as bench

# Error pages
ARG BENCH_REPO=https://github.com/frappe/bench
RUN git clone --depth 1 ${BENCH_REPO} /tmp/bench \
    && mkdir /out \
    && mv /tmp/bench/bench/config/templates/502.html /out \
    && touch /out/.build

FROM nginxinc/nginx-unprivileged:1.23.1-alpine as frappe

# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/20-envsubst-on-templates.sh
COPY nginx-template.conf /etc/nginx/templates/default.conf.template
# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/docker-entrypoint.sh
COPY entrypoint.sh /docker-entrypoint.d/frappe-entrypoint.sh

COPY --from=bench /out /usr/share/nginx/html/
COPY --from=frappe_assets /builds/bench/sites/assets /usr/share/nginx/html/assets

USER 1000


FROM frappe as erpnext

COPY --from=erpnext_assets /builds/bench/sites/assets /usr/share/nginx/html/assets
