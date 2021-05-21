FROM python:3.7-slim-buster

# Add non root user without password
RUN useradd -ms /bin/bash frappe

ARG GIT_REPO=https://github.com/frappe/frappe
ARG GIT_BRANCH=develop
ARG ARCH=amd64
ENV PYTHONUNBUFFERED 1
ENV NVM_DIR=/home/frappe/.nvm
ENV NODE_VERSION=14.17.0
ENV PATH="/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"

# Install dependencies
WORKDIR /home/frappe/frappe-bench
RUN apt-get update -y && apt-get install \
    # for frappe framework
    git \
    mariadb-client \
    postgresql-client \
    gettext-base \
    wget \
    wait-for-it \
    # for PDF
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
    gcc \
    g++ -y \
    # Detect arch, download and install wkhtmltox
    && if [ `uname -m` = 'aarch64' ]; then export ARCH=arm64; fi \
    && if [ `uname -m` = 'x86_64' ]; then export ARCH=amd64; fi \
    && wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_${ARCH}.deb \
    && dpkg -i wkhtmltox_0.12.6-1.buster_${ARCH}.deb && rm wkhtmltox_0.12.6-1.buster_${ARCH}.deb \
    && wget https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh \
    && chown -R frappe:frappe /home/frappe

# Setup docker-entrypoint
COPY build/common/worker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat

USER frappe
# Install nvm with node
RUN bash install.sh \
    && . "$NVM_DIR/nvm.sh" \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && nvm alias default v${NODE_VERSION}

# Create frappe-bench directories
RUN mkdir -p apps logs commands sites /home/frappe/backups

# Setup python environment
RUN python -m venv env \
    && . env/bin/activate \
    && pip3 install --upgrade pip \
    && pip3 install gevent \
    && cd apps \
    && git clone --depth 1 -o upstream ${GIT_REPO} --branch ${GIT_BRANCH} \
    && pip3 install --no-cache-dir -e /home/frappe/frappe-bench/apps/frappe

# Copy scripts and templates
COPY build/common/commands/* /home/frappe/frappe-bench/commands/
COPY build/common/common_site_config.json.template /opt/frappe/common_site_config.json.template
COPY build/common/worker/install_app.sh /usr/local/bin/install_app
COPY build/common/worker/bench /usr/local/bin/bench
COPY build/common/worker/healthcheck.sh /usr/local/bin/healthcheck.sh

# Use sites volume as working directory
WORKDIR /home/frappe/frappe-bench/sites

VOLUME [ "/home/frappe/frappe-bench/sites", "/home/frappe/backups", "/home/frappe/frappe-bench/logs" ]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
