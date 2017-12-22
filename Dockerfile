FROM ubuntu:16.04
MAINTAINER frappé

#install pre-requisites
USER root
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    build-essential \
    curl \
    git \
    iputils-ping \
    libffi-dev \
    libfreetype6-dev \
    libjpeg8-dev \
    liblcms2-dev \
    libldap2-dev \
    libmysqlclient-dev \
    libsasl2-dev \
    libssl-dev \
    libtiff5-dev \
    libwebp-dev \
    libxext6 \
    libxrender1 \
    mariadb-client \
    mariadb-common \
    nano \
    python-dev \
    python-setuptools \
    python-tk \
    redis-tools \
    rlwrap \
    software-properties-common \
    sudo \
    tcl8.6-dev \
    tk8.6-dev \
    wget \
    wkhtmltopdf \
    xfonts-75dpi \
    xfonts-base \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

#install pip
RUN wget https://bootstrap.pypa.io/get-pip.py \
    && python get-pip.py \
    && pip install --upgrade setuptools pip

#install nodejs
RUN curl https://deb.nodesource.com/node_6.x/pool/main/n/nodejs/nodejs_6.7.0-1nodesource1~xenial1_amd64.deb > node.deb  \
    && dpkg -i node.deb \
    && rm node.deb

#add users &  sudoers
RUN useradd -ms /bin/bash frappe \
    && usermod -aG sudo frappe \
    && printf '# User rules for frappe\nfrappe ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/frappe \
    && mkdir /home/frappe/frappe-bench \
    && chown -R frappe:frappe /home/frappe/*

COPY ./conf/frappe/* /home/frappe/

USER frappe
WORKDIR /home/frappe/frappe-bench
