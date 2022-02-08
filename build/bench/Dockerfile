FROM debian:bullseye-slim as bench

LABEL author=frappé

ARG GIT_REPO=https://github.com/frappe/bench.git
ARG GIT_BRANCH=develop

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    # For frappe framework
    git \
    mariadb-client \
    postgresql-client \
    gettext-base \
    wget \
    # for ERPNext v12
    # TODO: Remove after v12 is deprecated
    python2 \
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

# Detect arch and install wkhtmltopdf
ENV WKHTMLTOPDF_VERSION 0.12.6-1
RUN if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_$WKHTMLTOPDF_VERSION.buster_${ARCH}.deb \
    && wget -q https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && dpkg -i $downloaded_file \
    && rm $downloaded_file

# Create new user with home directory, improve docker compatibility with UID/GID 1000,
# add user to sudo group, allow passwordless sudo, switch to that user
# and change directory to user home directory
RUN groupadd -g 1000 frappe \
    && useradd --no-log-init -r -m -u 1000 -g 1000 -G sudo frappe \
    && echo "frappe ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER frappe
WORKDIR /home/frappe

# Install Python via pyenv
# Python 3.7 sits here for ERPNext version-12
# TODO: Remove Python 3.7 when version-12 will not be supported
ENV PYTHON_VERSION_V12=3.7.12
ENV PYTHON_VERSION=3.9.9
ENV PYENV_ROOT /home/frappe/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# From https://github.com/pyenv/pyenv#basic-github-checkout
RUN git clone --depth 1 https://github.com/pyenv/pyenv.git .pyenv \
    && pyenv install $PYTHON_VERSION_V12 \
    && pyenv install $PYTHON_VERSION \
    && pyenv global $PYTHON_VERSION $PYTHON_VERSION_V12 \
    && sed -Ei -e '/^([^#]|$)/ {a export PYENV_ROOT="/home/frappe/.pyenv" a export PATH="$PYENV_ROOT/bin:$PATH" a ' -e ':a' -e '$!{n;ba};}' ~/.profile \
    && echo 'eval "$(pyenv init --path)"' >>~/.profile \
    && echo 'eval "$(pyenv init -)"' >>~/.bashrc

# Clone and install bench in the local user home directory
# For development, bench source is located in ~/.bench
ENV PATH /home/frappe/.local/bin:$PATH
# Skip editable-bench warning
# https://github.com/frappe/bench/commit/20560c97c4246b2480d7358c722bc9ad13606138
RUN git clone ${GIT_REPO} --depth 1 -b ${GIT_BRANCH} .bench \
    && pip install --user -e .bench \
    && echo "export PATH=/home/frappe/.local/bin:\$PATH" >>/home/frappe/.bashrc \
    && echo "export BENCH_DEVELOPER=1" >>/home/frappe/.bashrc

# Install Node via nvm
ENV NODE_VERSION=14.18.1
ENV NODE_VERSION_FRAPPEV11=10.24.1
ENV NVM_DIR /home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

RUN wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION_FRAPPEV11} \
    && nvm use v${NODE_VERSION_FRAPPEV11} \
    && npm install -g yarn \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && echo 'export NVM_DIR="/home/frappe/.nvm"' >>~/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >> ~/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion' >> ~/.bashrc


EXPOSE 8000-8005 9000-9005 6787

FROM bench as bench-test

# Print version and verify bashrc is properly sourced so that everything works
# in the interactive shell and Dockerfile

RUN node --version \
    && npm --version \
    && yarn --version \
    && bench --help

RUN bash -c "node --version" \
    && bash -c "npm --version" \
    && bash -c "yarn --version" \
    && bash -c "bench --help"
