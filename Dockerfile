
#bench Dockerfile

FROM ubuntu:16.04
LABEL MAINTAINER frappé

USER root
RUN apt-get update
RUN apt-get install -y iputils-ping git build-essential python-setuptools python-dev libffi-dev libssl-dev \
  redis-tools redis-server software-properties-common libxrender1 libxext6 xfonts-75dpi xfonts-base \
  libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev python-tk apt-transport-https libsasl2-dev libldap2-dev libtiff5-dev \
  tcl8.6-dev tk8.6-dev wget libmysqlclient-dev mariadb-client mariadb-common curl rlwrap redis-tools nano wkhtmltopdf python-pip
RUN pip install --upgrade setuptools pip

# Generate locale C.UTF-8 for mariadb and general locale data
ENV LANG C.UTF-8

#nodejs
RUN curl https://deb.nodesource.com/node_10.x/pool/main/n/nodejs/nodejs_10.10.0-1nodesource1_amd64.deb > node.deb \
 && dpkg -i node.deb \
 && rm node.deb

USER frappe
WORKDIR /home/frappe
RUN git clone -b master https://github.com/frappe/bench.git bench-repo

USER root
RUN pip install -e bench-repo \
  && npm install -g yarn \
  && chown -R frappe:frappe /home/frappe/* \
  && && rm -rf /var/lib/apt/lists/*

USER frappe
WORKDIR /home/frappe/frappe-bench
