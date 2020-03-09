# Frappe Bench Dockerfile
FROM bitnami/minideb:latest
LABEL author=frappé

RUN install_packages \
    git \
    wkhtmltopdf \
    mariadb-client \
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
    software-properties-common \
    # For psycopg2
    libpq-dev \
    build-essential \ 
    # Other
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadbclient-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    redis-tools \
    rlwrap \
    tk8.6-dev \
    fonts-cantarell \
    # VSCode container requirements
    net-tools \
    # PYTHON
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-tk \
    python-virtualenv

# Install wkhtmltox correctly
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb
RUN dpkg -i wkhtmltox_0.12.5-1.stretch_amd64.deb && rm wkhtmltox_0.12.5-1.stretch_amd64.deb

# Create new user with directory, add user to sudo group, allow passwordless sudo, switch to that user and change directory to user home directory
RUN useradd --no-log-init -r -m -g  sudo frappe
RUN echo "frappe ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER frappe
WORKDIR /home/frappe

# Install bench in the local user home directory
RUN pip3 install --user  git+https://github.com/frappe/bench.git#egg=bench --no-cache

# Export python executables for Dockerfile
ENV PATH=/home/frappe/.local/bin/:$PATH
# Export python executables for interactive shell
RUN echo "export PATH=/home/frappe/.local/bin/:\$PATH" >> /home/frappe/.bashrc

# Print version and verify bashrc is properly sourced so that everything works in the Dockerfile
RUN bench --version
# Print version and verify bashrc is properly sourced so that everything works in the interactive shell
RUN bash -c "bench --version"

# !!! UPDATE NODEJS PERIODICALLY WITH LATEST VERSIONS !!!
# https://nodejs.org/en/about/releases/
# https://nodejs.org/download/release/latest-v10.x/
# https://nodejs.org/download/release/latest-v12.x/
# https://nodejs.org/download/release/latest-v13.x/
ENV NODE_VERSION=12.16.1
ENV NODE_VERSION_FRAPPEV11=10.19.0

# Install nvm with node
RUN wget https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh
RUN chmod +x install.sh
RUN ./install.sh

ENV NVM_DIR=/home/frappe/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION_FRAPPEV11}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
# Add NVM path for user in Dockerfile, interactive shell is already managed by the NVM install script
ENV PATH="/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"

# Install yarn
RUN npm install -g yarn

# Print version and verify bashrc is properly sourced so that everything works in the Dockerfile
RUN node --version \
    && npm --version \ 
    && yarn --version
# Print version and verify bashrc is properly sourced so that everything works in the interactive shell
RUN bash -c "node --version" \
    && bash -c "npm --version" \
    && bash -c "yarn --version"


WORKDIR /home/frappe/frappe-bench
EXPOSE 8000 9000 6787