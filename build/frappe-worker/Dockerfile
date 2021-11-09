ARG PYTHON_VERSION=3.9
FROM python:${PYTHON_VERSION}-slim-bullseye

# Add non root user without password
RUN useradd -ms /bin/bash frappe

ARG GIT_REPO=https://github.com/frappe/frappe
ARG GIT_BRANCH=develop

ARG ARCH=amd64
ENV PYTHONUNBUFFERED 1

ENV NODE_VERSION=14.18.1
ENV NVM_DIR /home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}
ENV WKHTMLTOPDF_VERSION 0.12.6-1

# Install apt dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # For frappe framework
    git \
    mariadb-client \
    postgresql-client \
    gettext-base \
    wget \
    wait-for-it \
    # For PDF
    libjpeg62-turbo \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libssl-dev \
    fonts-cantarell \
    xfonts-75dpi \
    xfonts-base \
    libxml2 \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    # For psycopg2
    libpq-dev \
    # For arm64 python wheel builds
    && if [ "$(uname -m)" = "aarch64" ]; then \
    apt-get install --no-install-recommends -y \
    gcc \
    g++; \
    fi \
    # Install additional requirements for develop branch
    && if [ "${GIT_BRANCH}" = 'develop' ]; then \
    apt-get install --no-install-recommends -y \
    libcairo2 \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0; \
    fi \
    && rm -rf /var/lib/apt/lists/*

# Detect arch, download and install wkhtmltopdf
RUN if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_$WKHTMLTOPDF_VERSION.buster_${ARCH}.deb \
    && wget -q https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && dpkg -i $downloaded_file \
    && rm $downloaded_file

RUN chown -R frappe:frappe /home/frappe

# Setup docker-entrypoint
COPY build/frappe-worker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat

USER frappe
WORKDIR /home/frappe/frappe-bench

# Create frappe-bench directories
RUN mkdir -p apps logs commands sites /home/frappe/backups

# Setup python environment
RUN python -m venv env
RUN env/bin/pip install --no-cache-dir wheel gevent

# Install nvm with node
RUN wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache

# Install Frappe
RUN git clone --depth 1 -o upstream -b ${GIT_BRANCH} ${GIT_REPO} apps/frappe \
    && env/bin/pip install --no-cache-dir -e apps/frappe

# Copy scripts and templates
COPY build/frappe-worker/commands/* /home/frappe/frappe-bench/commands/
COPY build/frappe-worker/common_site_config.json.template /opt/frappe/common_site_config.json.template
COPY build/frappe-worker/install_app.sh /usr/local/bin/install_app
COPY build/frappe-worker/bench /usr/local/bin/bench
COPY build/frappe-worker/healthcheck.sh /usr/local/bin/healthcheck.sh

# Use sites volume as working directory
WORKDIR /home/frappe/frappe-bench/sites

VOLUME [ "/home/frappe/frappe-bench/sites", "/home/frappe/backups", "/home/frappe/frappe-bench/logs" ]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
