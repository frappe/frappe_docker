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
RUN mkdir -p /home/frappe/frappe-bench/apps /home/frappe/frappe-bench/logs /home/frappe/frappe-bench/sites /home/frappe/frappe-bench/config
WORKDIR /home/frappe/frappe-bench

USER root
RUN pip install --no-cache-dir -U pip wheel \
    && python -m venv env \
    && env/bin/pip install --no-cache-dir -U pip wheel

COPY install-app.sh /usr/local/bin/install-app


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


FROM build_deps as frappe_builder

ARG FRAPPE_VERSION
ARG FRAPPE_REPO=https://github.com/frappe/frappe
RUN --mount=type=cache,target=/root/.cache/pip \
    git clone --depth 1 -b ${FRAPPE_VERSION} ${FRAPPE_REPO} apps/frappe \
    && install-app frappe \
    && env/bin/pip install -U gevent \
    # Link Frappe's node_modules/ to make Website Theme work
    && mkdir -p /home/frappe/frappe-bench/sites/assets/frappe/node_modules \
    && ln -s /home/frappe/frappe-bench/sites/assets/frappe/node_modules /home/frappe/frappe-bench/apps/frappe/node_modules


FROM frappe_builder as erpnext_builder

ARG PAYMENTS_VERSION=develop
ARG PAYMENTS_REPO=https://github.com/frappe/payments
ARG ERPNEXT_VERSION
ARG ERPNEXT_REPO=https://github.com/frappe/erpnext
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ -z "${ERPNEXT_VERSION##*v14*}" ] || [ "$ERPNEXT_VERSION" = "develop" ]; then \
        git clone --depth 1 -b ${PAYMENTS_VERSION} ${PAYMENTS_REPO} apps/payments && install-app payments; \
    fi \
    && git clone --depth 1 -b ${ERPNEXT_VERSION} ${ERPNEXT_REPO} apps/erpnext \
    && install-app erpnext

FROM base as configured_base

ARG WKHTMLTOPDF_VERSION=0.12.6-1
ARG NODE_VERSION
ENV NVM_DIR=/home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}
RUN apt-get update \
    # Setup Node lists
    && apt-get install --no-install-recommends -y curl git \
    # NodeJS with NVM
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && echo 'export NVM_DIR="/home/frappe/.nvm"' >>~/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >> ~/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion' >> ~/.bashrc \
    # Install wkhtmltopdf with patched qt
    && if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_$WKHTMLTOPDF_VERSION.buster_${ARCH}.deb \
    && curl -sLO https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && apt-get install -y ./$downloaded_file \
    && rm $downloaded_file \
    # Cleanup
    && apt-get purge -y --auto-remove curl \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    # MariaDB
    mariadb-client \
    # Postgres
    postgresql-client \
    # For healthcheck
    wait-for-it \
    jq \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

COPY pretend-bench.sh /usr/local/bin/bench
COPY push_backup.py /usr/local/bin/push-backup
COPY configure.py patched_bench_helper.py /usr/local/bin/
COPY gevent_patch.py /opt/patches/

WORKDIR /home/frappe/frappe-bench/sites

CMD [ "/home/frappe/frappe-bench/env/bin/gunicorn", \
  "--bind=0.0.0.0:8000", \
  "--threads=4", \
  "--workers=2", \
  "--worker-class=gthread", \
  "--worker-tmp-dir=/dev/shm", \
  "--timeout=120", \
  "--preload", \
  "frappe.app:application" \
]


FROM configured_base as frappe

COPY --from=frappe_builder /home/frappe/frappe-bench/apps/frappe /home/frappe/frappe-bench/apps/frappe
COPY --from=frappe_builder /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env
COPY --from=frappe_builder /home/frappe/frappe-bench/sites/apps.txt /home/frappe/frappe-bench/sites/

USER frappe


# Split frappe and erpnext to reduce image size (because of frappe-bench/env/ directory)
FROM configured_base as erpnext

COPY --from=erpnext_builder --chown=frappe:frappe /home/frappe/frappe-bench/apps /home/frappe/frappe-bench/apps
COPY --from=erpnext_builder --chown=frappe:frappe /home/frappe/frappe-bench/env /home/frappe/frappe-bench/env
COPY --from=erpnext_builder --chown=frappe:frappe /home/frappe/frappe-bench/sites/apps.txt /home/frappe/frappe-bench/sites/


USER frappe
