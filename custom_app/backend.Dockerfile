# syntax=docker/dockerfile:1.3

ARG ERPNEXT_VERSION
FROM frappe/erpnext-worker:${ERPNEXT_VERSION}

USER root

ARG APP_NAME
COPY . ../apps/${APP_NAME}

RUN --mount=type=cache,target=/root/.cache/pip \
    install-app ${APP_NAME}

USER frappe
