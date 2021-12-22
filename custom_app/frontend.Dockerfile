ARG FRAPPE_VERSION
FROM node:14-bullseye-slim as prod_node_modules

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

RUN yarn --cwd apps/frappe


ARG APP_NAME
COPY . apps/${APP_NAME}

# Install production node modules
RUN yarn --cwd apps/${APP_NAME} --prod



FROM prod_node_modules as assets

ARG APP_NAME

# Install development node modules
RUN yarn --cwd apps/${APP_NAME}

# Build assets
RUN echo "frappe\n${APP_NAME}" >sites/apps.txt \
    && yarn --cwd apps/frappe production --app ${APP_NAME} \
    && rm sites/apps.txt



FROM frappe/frappe-nginx:${FRAPPE_VERSION}

ARG APP_NAME

# Copy all not built assets
COPY --from=prod_node_modules /root/frappe-bench/apps/${APP_NAME}/${APP_NAME}/public /usr/share/nginx/html/assets/${APP_NAME}
# Copy production node modules
COPY --from=prod_node_modules /root/frappe-bench/apps/${APP_NAME}/node_modules /usr/share/nginx/html/assets/${APP_NAME}/node_modules
# Copy built assets
COPY --from=assets /root/frappe-bench/sites /usr/share/nginx/html
