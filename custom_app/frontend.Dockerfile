ARG FRAPPE_VERSION
ARG ERPNEXT_VERSION

FROM frappe/assets-builder:${FRAPPE_VERSION} as assets

ARG APP_NAME
COPY . apps/${APP_NAME}
RUN install-app ${APP_NAME}

# or with git:
# ARG APP_NAME
# ARG BRANCH
# ARG GIT_URL
# RUN install-app ${APP_NAME} ${BRANCH} ${GIT_URL}


FROM frappe/erpnext-nginx:${ERPNEXT_VERSION}

COPY --from=assets /out /usr/share/nginx/html
