ARG FRAPPE_VERSION
FROM frappe/erpnext-worker:${FRAPPE_VERSION}

ARG APP_NAME
COPY --chown=frappe . ../apps/${APP_NAME}

RUN echo "frappe\nerpnext\n${APP_NAME}" >/home/frappe/frappe-bench/sites/apps.txt \
    && ../env/bin/pip install --no-cache-dir -e ../apps/${APP_NAME}
