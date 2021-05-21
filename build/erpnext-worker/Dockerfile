ARG IMAGE_TAG=develop
ARG DOCKER_REGISTRY_PREFIX=frappe
FROM ${DOCKER_REGISTRY_PREFIX}/frappe-worker:${IMAGE_TAG}

ARG GIT_REPO=https://github.com/frappe/erpnext
ARG GIT_BRANCH=develop

RUN install_app erpnext ${GIT_REPO} ${GIT_BRANCH}
