ARG GIT_BRANCH=develop
FROM frappe/frappe-worker-arm:${GIT_BRANCH}

ARG GIT_BRANCH
RUN pip install bootstrapped --no-deps
RUN install_app erpnext https://github.com/frappe/erpnext ${GIT_BRANCH}
