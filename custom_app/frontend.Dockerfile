ARG FRAPPE_VERSION=version-14
# Prepare builder image
FROM frappe/bench:latest as assets

ARG FRAPPE_VERSION=version-14
ARG ERPNEXT_VERSION=version-14
ARG APP_NAME

# Setup frappe-bench using FRAPPE_VERSION
RUN bench init --version=${FRAPPE_VERSION} --skip-redis-config-generation --verbose --skip-assets /home/frappe/frappe-bench
WORKDIR /home/frappe/frappe-bench

# Comment following if ERPNext is not required
RUN bench get-app --branch=${ERPNEXT_VERSION} --skip-assets --resolve-deps erpnext

# Copy custom app(s)
COPY --chown=frappe:frappe . apps/${APP_NAME}

# Setup dependencies
RUN bench setup requirements

# Build static assets, copy files instead of symlink
RUN if [ -z "${ERPNEXT_VERSION##*v14*}" ] || [ "$ERPNEXT_VERSION" = "develop" ]; then \
        export BUILD_OPTS="--production"; \
    fi \
    && FRAPPE_ENV=production bench build --verbose --hard-link ${BUILD_OPTS}


# Use frappe-nginx image with nginx template and env vars
FROM frappe/frappe-nginx:${FRAPPE_VERSION}

# Remove existing assets
USER root
RUN rm -fr /usr/share/nginx/html/assets

# Copy built assets
COPY --from=assets /home/frappe/frappe-bench/sites/assets /usr/share/nginx/html/assets

# Use non-root user
USER 1000
