ARG IMAGE_TAG=develop
ARG DOCKER_REGISTRY_PREFIX=frappe
FROM ${DOCKER_REGISTRY_PREFIX}/frappe-worker:${IMAGE_TAG}

ARG GIT_REPO=https://github.com/frappe/erpnext
ARG GIT_BRANCH=develop

USER root
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

USER frappe
RUN install_app erpnext ${GIT_REPO} ${GIT_BRANCH}
