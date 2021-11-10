FROM python:3.10.0-slim-bullseye as build

LABEL author=frappé

ARG GIT_REPO=https://github.com/frappe/bench.git
ARG GIT_BRANCH=develop

ENV NODE_VERSION=14.18.1
ENV NODE_VERSION_FRAPPEV11=10.24.1
ENV NVM_DIR /home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}
ENV WKHTMLTOPDF_VERSION 0.12.6-1

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    # For frappe framework
    git \
    mariadb-client \
    postgresql-client \
    gettext-base \
    wget \
    # for PDF
    libssl-dev \
    fonts-cantarell \
    xfonts-75dpi \
    xfonts-base \
    # to work inside the container
    locales \
    build-essential \
    cron \
    curl \
    vim \
    sudo \
    iputils-ping \
    watch \
    tree \
    nano \
    less \
    software-properties-common \
    bash-completion \
    # For psycopg2
    libpq-dev \
    # Other
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    redis-tools \
    rlwrap \
    tk8.6-dev \
    ssh-client \
    # VSCode container requirements
    net-tools \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales

# Detect arch, download and install wkhtmltopdf
RUN if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_$WKHTMLTOPDF_VERSION.buster_${ARCH}.deb \
    && wget -q https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && dpkg -i $downloaded_file \
    && rm $downloaded_file

# Create new user with home directory, improve docker compatibility with UID/GID 1000, add user to sudo group, allow passwordless sudo, switch to that user and change directory to user home directory
RUN groupadd -g 1000 frappe \
    && useradd --no-log-init -r -m -u 1000 -g 1000 -G sudo frappe \
    && echo "frappe ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER frappe
WORKDIR /home/frappe

# Clone and install bench in the local user home directory
# For development, bench source is located in ~/.bench
RUN git clone ${GIT_REPO} --depth 1 -b ${GIT_BRANCH} .bench \
    && pip install --user -e .bench

# Export python executables for Dockerfile
ENV PATH /home/frappe/.local/bin:$PATH
# Export python executables for interactive shell
RUN echo "export PATH=/home/frappe/.local/bin:\$PATH" >> /home/frappe/.bashrc

# Install nvm with node
RUN wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    # Install node for Frappe V11, install yarn
    && nvm install ${NODE_VERSION_FRAPPEV11} \
    && nvm use v${NODE_VERSION_FRAPPEV11} \
    && npm install -g yarn \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache

EXPOSE 8000-8005 9000-9005 6787

FROM build as test

# Print version and verify bashrc is properly sourced so that everything works in the Dockerfile
RUN node --version \
    && npm --version \
    && yarn --version
# Print version and verify bashrc is properly sourced so that everything works in the interactive shell
RUN bash -c "node --version" \
    && bash -c "npm --version" \
    && bash -c "yarn --version"

RUN bench --help
RUN bash -c "bench --help"