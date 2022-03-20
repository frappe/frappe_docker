ARG FRAPPE_VERSION
FROM frappe/erpnext-worker:${FRAPPE_VERSION}

USER root

ARG APP_NAME
COPY . ../apps/${APP_NAME}

RUN install-app ${APP_NAME}

# or with git:
# ARG APP_NAME
# ARG BRANCH
# ARG GIT_URL
# RUN install-assets ${APP_NAME} ${BRANCH} ${GIT_URL}

USER frappe
