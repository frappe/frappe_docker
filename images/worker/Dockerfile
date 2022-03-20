# syntax=docker/dockerfile:1.3

ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim-bullseye as base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # Postgres
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash frappe
USER frappe
RUN mkdir -p /home/frappe/frappe-bench/apps /home/frappe/frappe-bench/logs /home/frappe/frappe-bench/sites
WORKDIR /home/frappe/frappe-bench

USER root
RUN pip install -U pip wheel \
    && python -m venv env \
    && env/bin/pip install -U pip wheel


FROM base as build_deps

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
    # Make is required to build wheels of ERPNext deps in develop branch for linux/arm64
    make \
    && rm -rf /var/lib/apt/lists/*

COPY install-app.sh /usr/local/bin/install-app


FROM build_deps as frappe_builder

ARG FRAPPE_VERSION
RUN --mount=type=cache,target=/root/.cache/pip \
    install-app frappe ${FRAPPE_VERSION} https://github.com/frappe/frappe \
    && env/bin/pip install -U gevent \
    # Link Frappe's node_modules/ to make Website Theme work
    && mkdir -p /home/frappe/frappe-bench/sites/assets/frappe/node_modules \
    && ln -s /home/frappe/frappe-bench/sites/assets/frappe/node_modules /home/frappe/frappe-bench/apps/frappe/node_modules


FROM frappe_builder as erpnext_builder

ARG ERPNEXT_VERSION
RUN --mount=type=cache,target=/root/.cache/pip \
    install-app erpnext ${ERPNEXT_VERSION} https://github.com/frappe/erpnext


FROM base as configured_base

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get purge -y --auto-remove curl \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    # MariaDB
    mariadb-client \
    # Postgres
    postgresql-client \
    # wkhtmltopdf
    xvfb \
    libfontconfig \
    wkhtmltopdf \
    # For healthcheck
    wait-for-it \
    jq \
    # other
    nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY pretend-bench.sh /usr/local/bin/bench
COPY push_backup.py /usr/local/bin/push-backup
COPY configure.py patched_bench_helper.py /usr/local/bin/
COPY gevent_patch.py /opt/patches/

WORKDIR /home/frappe/frappe-bench/sites

CMD [ "/home/frappe/frappe-bench/env/bin/gunicorn", "-b", "0.0.0.0:8000", "frappe.app:application" ]


FROM configured_base as frappe

COPY --from=frappe_builder /home/frappe/frappe-bench/apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --from=frappe_builder /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env
COPY --from=erpnext_builder /home/frappe/frappe-bench/sites/apps.txt /home/frappe/frappe-bench/sites/

USER frappe


# Split frappe and erpnext to reduce image size (because of frappe-bench/env/ directory)
FROM configured_base as erpnext

COPY --from=frappe_builder /home/frappe/frappe-bench/apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --from=erpnext_builder /home/frappe/frappe-bench/apps/erpnext /home/frappe/frappe-bench/apps/erpnext
COPY --from=erpnext_builder /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env
COPY --from=erpnext_builder /home/frappe/frappe-bench/sites/apps.txt /home/frappe/frappe-bench/sites/

USER frappe
