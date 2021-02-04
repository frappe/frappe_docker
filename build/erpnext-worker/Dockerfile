ARG GIT_BRANCH=version-12
ARG DOCKER_REGISTRY_PREFIX=graficheaquilane
FROM ${DOCKER_REGISTRY_PREFIX}/frappe-worker:${GIT_BRANCH}

ARG GIT_BRANCH
RUN sed -i 's/\r$//' /usr/local/bin/install_app
RUN bash install_app erpnext https://github.com/GraficheAquilane2021/erpnext ${GIT_BRANCH}