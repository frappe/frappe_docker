ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim-bullseye as base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # MariaDB
    mariadb-client \
    # Postgres
    postgresql-client \
    libpq-dev \
    # wkhtmltopdf
    xvfb \
    libfontconfig \
    wkhtmltopdf \
    # For healthcheck.sh in helm chart
    wait-for-it \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash frappe
USER frappe
RUN mkdir -p /home/frappe/frappe-bench/apps /home/frappe/frappe-bench/logs /home/frappe/frappe-bench/sites
WORKDIR /home/frappe/frappe-bench

RUN pip install --no-cache-dir -U pip wheel \
    && python -m venv env \
    && env/bin/pip install --no-cache-dir -U pip wheel


FROM base as frappe_builder

USER root
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # Install git here because it is not required in production
    git \
    # gcc and g++ are required for building different packages across different versions
    # of Frappe and ERPNext and also on different platforms (for example, linux/arm64).
    # It is safe to install build deps even if they are not required
    # because they won't be included in final images.
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*
USER frappe

ARG FRAPPE_VERSION
RUN git clone --depth 1 -b ${FRAPPE_VERSION} https://github.com/frappe/frappe apps/frappe \
    && env/bin/pip install --no-cache-dir -e apps/frappe \
    && rm -r apps/frappe/.git


FROM frappe_builder as erpnext_builder

ARG ERPNEXT_VERSION
RUN git clone --depth 1 -b ${ERPNEXT_VERSION} https://github.com/frappe/erpnext apps/erpnext \
    && env/bin/pip install --no-cache-dir -e apps/erpnext \
    && rm -r apps/erpnext/.git


FROM base as configured_base

COPY pretend-bench.sh /usr/local/bin/bench
# healthcheck.sh used in helm chart
COPY entrypoint.sh patched_bench_helper.py healthcheck.sh /usr/local/bin/

WORKDIR /home/frappe/frappe-bench/sites

VOLUME [ "/home/frappe/frappe-bench/sites", "/home/frappe/frappe-bench/logs" ]

ENTRYPOINT [ "entrypoint.sh" ]

CMD [ "/home/frappe/frappe-bench/env/bin/gunicorn", "-b", "0.0.0.0:8000", "frappe.app:application", "--access-logfile", "-" ]


FROM configured_base as frappe

RUN echo "frappe" >/home/frappe/frappe-bench/sites/apps.txt
COPY --from=frappe_builder /home/frappe/frappe-bench/apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --from=frappe_builder /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env


FROM configured_base as erpnext

RUN echo "frappe\nerpnext" >/home/frappe/frappe-bench/sites/apps.txt
COPY --from=frappe_builder /home/frappe/frappe-bench/apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --from=erpnext_builder /home/frappe/frappe-bench/apps/erpnext /home/frappe/frappe-bench/apps/erpnext
COPY --from=erpnext_builder /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env
