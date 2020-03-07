# Frappe Bench Dockerfile
FROM bitnami/minideb:latest
LABEL author=frappé


WORKDIR /home/frappe/frappe-bench
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
    python3-tk


# Install wkhtmltox correctly
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb
RUN dpkg -i wkhtmltox_0.12.5-1.stretch_amd64.deb && rm wkhtmltox_0.12.5-1.stretch_amd64.deb



# Add frappe user and setup sudo
RUN groupadd -g 1000 frappe \
  && useradd -ms /bin/bash -u 1000 -g 1000 -G sudo frappe \
  && chown -R 1000:1000 /home/frappe

# Install nvm with node
ENV NODE_VERSION=13.10.1
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version
RUN npm install -g yarn
RUN yarn --version
RUN echo '. "$NVM_DIR/nvm.sh"' >> /home/frappe/.bashrc

# Install bench
RUN pip3 install -e git+https://github.com/frappe/bench.git#egg=bench --no-cache

USER frappe

WORKDIR /home/frappe/frappe-bench

EXPOSE 8000 9000 6787

VOLUME [ "/home/frappe/frappe-bench" ]
