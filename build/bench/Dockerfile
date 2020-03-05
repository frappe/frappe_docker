# Frappe Bench Dockerfile

FROM debian:9.6-slim
LABEL author=frappé

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends locales \
  && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
  && dpkg-reconfigure --frontend=noninteractive locales \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set locale en_us.UTF-8 for mariadb and general locale data
ENV PYTHONIOENCODING=utf-8
ENV LANGUAGE=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Install all neccesary packages
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-suggests --no-install-recommends \
  build-essential cron curl git libffi-dev liblcms2-dev libldap2-dev libmariadbclient-dev libsasl2-dev libssl1.0-dev libtiff5-dev \
  libwebp-dev mariadb-client iputils-ping python3-dev python3-pip python3-setuptools python3-tk redis-tools rlwrap \
  software-properties-common sudo tk8.6-dev vim xfonts-75dpi xfonts-base wget wkhtmltopdf fonts-cantarell \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add frappe user and setup sudo
RUN groupadd -g 1000 frappe \
  && useradd -ms /bin/bash -u 1000 -g 1000 -G sudo frappe \
  && chown -R 1000:1000 /home/frappe \
  && echo '. "$NVM_DIR/nvm.sh"' >> /home/frappe/.bashrc

# Install nvm with node
ENV NVM_DIR /home/frappe/.nvm
ENV NODE_VERSION 12.16.1
RUN mkdir /home/frappe/.nvm \
    && wget -qO- https://raw.githubusercontent.com/creationix/nvm/v0.35.2/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm install 10.19.0 \
    && npm install yarn -g \
    && nvm alias default $NODE_VERSION \
    && nvm use default \
    && npm install yarn -g \
    && chown -R frappe:frappe /home/frappe
ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH $NVM_DIR/v$NODE_VERSION/bin:$PATH

# Install wkhtmltox correctly
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb
RUN dpkg -i wkhtmltox_0.12.5-1.stretch_amd64.deb && rm wkhtmltox_0.12.5-1.stretch_amd64.deb

# Install bench
RUN pip3 install -e git+https://github.com/frappe/bench.git#egg=bench --no-cache

USER frappe

WORKDIR /home/frappe/frappe-bench

EXPOSE 8000 9000 6787

VOLUME [ "/home/frappe/frappe-bench" ]
