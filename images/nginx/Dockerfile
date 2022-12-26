FROM frappe/bench:latest as assets_builder

ARG FRAPPE_VERSION
ARG FRAPPE_REPO=https://github.com/frappe/frappe
ARG PYTHON_VERSION
ARG NODE_VERSION
ENV NVM_DIR=/home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}
RUN PYENV_VERSION=${PYTHON_VERSION} bench init --version=${FRAPPE_VERSION} --frappe-path=${FRAPPE_REPO} --skip-redis-config-generation --verbose --skip-assets /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench


FROM assets_builder as frappe_assets

RUN bench setup requirements \
    && if [ -z "${FRAPPE_VERSION##*v14*}" ] || [ "$FRAPPE_VERSION" = "develop" ]; then \
        export BUILD_OPTS="--production";\
    fi \
    && FRAPPE_ENV=production bench build --verbose --hard-link ${BUILD_OPTS}


FROM assets_builder as erpnext_assets

ARG ERPNEXT_VERSION
ARG ERPNEXT_REPO=https://github.com/frappe/erpnext
RUN bench get-app --branch=${ERPNEXT_VERSION} --skip-assets --resolve-deps erpnext ${ERPNEXT_REPO}\
    && if [ -z "${ERPNEXT_VERSION##*v14*}" ] || [ "$ERPNEXT_VERSION" = "develop" ]; then \
        export BUILD_OPTS="--production"; \
    fi \
    && FRAPPE_ENV=production bench build --verbose --hard-link ${BUILD_OPTS}


FROM alpine/git as bench

# Error pages
ARG BENCH_REPO=https://github.com/frappe/bench
RUN git clone --depth 1 ${BENCH_REPO} /tmp/bench \
    && mkdir /out \
    && mv /tmp/bench/bench/config/templates/502.html /out \
    && touch /out/.build

FROM nginxinc/nginx-unprivileged:1.23.3-alpine as frappe

# Set default ENV variables for backwards compatibility
ENV PROXY_READ_TIMOUT=120
ENV CLIENT_MAX_BODY_SIZE=50m

# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/20-envsubst-on-templates.sh
COPY nginx-template.conf /etc/nginx/templates/default.conf.template
# https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/stable/alpine/docker-entrypoint.sh
COPY entrypoint.sh /docker-entrypoint.d/frappe-entrypoint.sh

COPY --from=bench /out /usr/share/nginx/html/
COPY --from=frappe_assets /home/frappe/frappe-bench/sites/assets /usr/share/nginx/html/assets

USER 1000


FROM frappe as erpnext

COPY --from=erpnext_assets /home/frappe/frappe-bench/sites/assets /usr/share/nginx/html/assets
