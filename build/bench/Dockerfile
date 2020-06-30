# Frappe Bench Dockerfile
FROM bitnami/minideb:latest
LABEL author=frappé

RUN install_packages \
    git \
    wkhtmltopdf \
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
    software-properties-common \
    bash-completion \
    # For psycopg2
    libpq-dev \
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
    ssh-client \
    # VSCode container requirements
    net-tools \
    # PYTHON
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-tk \
    python-virtualenv \
    less

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
  && dpkg-reconfigure --frontend=noninteractive locales

# Install wkhtmltox correctly
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.buster_amd64.deb
RUN dpkg -i wkhtmltox_0.12.5-1.buster_amd64.deb && rm wkhtmltox_0.12.5-1.buster_amd64.deb

# Create new user with home directory, improve docker compatibility with UID/GID 1000, add user to sudo group, allow passwordless sudo, switch to that user and change directory to user home directory
RUN groupadd -g 1000 frappe
RUN useradd --no-log-init -r -m -u 1000 -g 1000 -G  sudo frappe
RUN echo "frappe ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER frappe
WORKDIR /home/frappe

# Clone and install bench in the local user home directory
# For development, bench source is located in ~/.bench
RUN git clone https://github.com/frappe/bench.git .bench \
    && pip3 install --user -e .bench

# Export python executables for Dockerfile
ENV PATH=/home/frappe/.local/bin:$PATH
# Export python executables for interactive shell
RUN echo "export PATH=/home/frappe/.local/bin:\$PATH" >> /home/frappe/.bashrc

# Print version and verify bashrc is properly sourced so that everything works in the Dockerfile
RUN bench --version
# Print version and verify bashrc is properly sourced so that everything works in the interactive shell
RUN bash -c "bench --version"

# !!! UPDATE NODEJS PERIODICALLY WITH LATEST VERSIONS !!!
# https://nodejs.org/en/about/releases/
# https://nodejs.org/download/release/latest-v10.x/
# https://nodejs.org/download/release/latest-v12.x/
# https://nodejs.org/download/release/latest-v13.x/
ENV NODE_VERSION=12.18.2
ENV NODE_VERSION_FRAPPEV11=10.21.0

# Install nvm with node
RUN wget https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh
RUN chmod +x install.sh
RUN ./install.sh
ENV NVM_DIR=/home/frappe/.nvm

# Install node for Frappe V11, install yarn
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION_FRAPPEV11}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION_FRAPPEV11} && npm install -g yarn
# Install node for latest frappe, set as default, install node
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}  && npm install -g yarn
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"

# Print version and verify bashrc is properly sourced so that everything works in the Dockerfile
RUN node --version \
    && npm --version \
    && yarn --version
# Print version and verify bashrc is properly sourced so that everything works in the interactive shell
RUN bash -c "node --version" \
    && bash -c "npm --version" \
    && bash -c "yarn --version"

EXPOSE 8000-8005 9000-9005 6787
