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

RUN --mount=type=cache,target=/home/frappe/.cache/pip \
    pip install -U pip wheel \
    && python -m venv env \
    && env/bin/pip install -U pip wheel
USER root



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
USER frappe



FROM build_deps as frappe_builder

ARG FRAPPE_VERSION
RUN --mount=type=cache,target=/home/frappe/.cache/pip \
    git clone --depth 1 -b ${FRAPPE_VERSION} https://github.com/frappe/frappe apps/frappe \
    && env/bin/pip install -e apps/frappe \
    && env/bin/pip install -U gevent \
    && rm -r apps/frappe/.git



# We split ERPNext wheels build in separate stage to achieve concurrency with Frappe build
FROM build_deps as erpnext_wheels

ARG ERPNEXT_VERSION
RUN git clone --depth 1 -b ${ERPNEXT_VERSION} https://github.com/frappe/erpnext apps/erpnext \
    && rm -r apps/erpnext/.git

RUN --mount=type=cache,target=/home/frappe/.cache/pip \
    pip wheel --wheel-dir /home/frappe/erpnext-wheels -r apps/erpnext/requirements.txt



FROM frappe_builder as erpnext_builder

COPY --from=erpnext_wheels --chown=frappe /home/frappe/frappe-bench/apps/erpnext /home/frappe/frappe-bench/apps/erpnext
RUN --mount=type=bind,target=/home/frappe/erpnext-wheels,source=/home/frappe/erpnext-wheels,from=erpnext_wheels \
    --mount=type=cache,target=/home/frappe/.cache/pip \
    --mount=type=cache,target=/home/frappe/.cache/pip,source=/home/frappe/.cache/pip,from=erpnext_wheels \
    env/bin/pip install --find-links=/home/frappe/erpnext-wheels -e apps/erpnext



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
USER frappe

COPY pretend-bench.sh /usr/local/bin/bench
COPY push_backup.py /usr/local/bin/push-backup
COPY configure.py patched_bench_helper.py /usr/local/bin/
COPY gevent_patch.py /opt/patches/

WORKDIR /home/frappe/frappe-bench/sites

CMD [ "/home/frappe/frappe-bench/env/bin/gunicorn", "-b", "0.0.0.0:8000", "frappe.app:application" ]


FROM configured_base as frappe

RUN echo "frappe" >/home/frappe/frappe-bench/sites/apps.txt
COPY --from=frappe_builder /home/frappe/frappe-bench/apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --from=frappe_builder /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env


FROM configured_base as erpnext

RUN echo "frappe\nerpnext" >/home/frappe/frappe-bench/sites/apps.txt
COPY --from=frappe_builder /home/frappe/frappe-bench/apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --from=erpnext_builder /home/frappe/frappe-bench/apps/erpnext /home/frappe/frappe-bench/apps/erpnext
COPY --from=erpnext_builder /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env
