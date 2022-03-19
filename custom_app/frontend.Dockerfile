ARG FRAPPE_VERSION
FROM frappe/assets-builder:${FRAPPE_VERSION} as prod_node_modules

ARG APP_NAME
COPY . apps/${APP_NAME}

# Install production node modules
RUN yarn --cwd apps/${APP_NAME} --prod



FROM prod_node_modules as assets

ARG APP_NAME

# Install development node modules
RUN yarn --cwd apps/${APP_NAME}

# Build assets
RUN echo "frappe\nerpnext\n${APP_NAME}" >sites/apps.txt \
    && yarn --cwd apps/frappe production --app ${APP_NAME} \
    && rm sites/apps.txt



FROM frappe/erpnext-nginx:${FRAPPE_VERSION}

ARG APP_NAME

# Copy all not built assets
COPY --from=prod_node_modules /root/frappe-bench/apps/${APP_NAME}/${APP_NAME}/public /usr/share/nginx/html/assets/${APP_NAME}
# Copy production node modules
COPY --from=prod_node_modules /root/frappe-bench/apps/${APP_NAME}/node_modules /usr/share/nginx/html/assets/${APP_NAME}/node_modules
# Copy built assets
COPY --from=assets /root/frappe-bench/sites /usr/share/nginx/html
