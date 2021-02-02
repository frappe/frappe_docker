ARG GIT_BRANCH=develop
FROM graficheaquilane/frappe-worker:${GIT_BRANCH}

ARG GIT_BRANCH
RUN install_app erpnext https://github.com/GraficheAquilane2021/erpnext ${GIT_BRANCH}
