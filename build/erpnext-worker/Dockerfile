ARG IMAGE_TAG=v10
ARG DOCKER_REGISTRY_PREFIX=frappe
FROM ${DOCKER_REGISTRY_PREFIX}/frappe-worker:${IMAGE_TAG}

ARG GIT_REPO=https://github.com/frappe/erpnext
ARG GIT_BRANCH=v10.x.x

RUN install_app erpnext ${GIT_REPO} ${GIT_BRANCH}
