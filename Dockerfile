
#bench Dockerfile

FROM ubuntu:18.04
MAINTAINER Facgure

USER root
RUN apt-get update -y
RUN apt-get install -y iputils-ping
RUN apt-get install -y git build-essential python-setuptools python-dev libffi-dev libssl-dev
RUN apt-get install -y redis-tools software-properties-common libxrender1 libxext6 xfonts-75dpi xfonts-base

RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install tzdata
RUN ln -fs /usr/share/zoneinfo/Asia/Bangkok /etc/localtime
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN apt-get install -y libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev python-tk apt-transport-https libsasl2-dev libldap2-dev libtiff5-dev tcl8.6-dev tk8.6-dev
RUN apt-get install -y wget wkhtmltopdf curl rlwrap vim

RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py
RUN pip install --upgrade setuptools pip

# Add user frappe and set as sudoers
RUN apt-get install -y sudo
RUN useradd -ms /bin/bash frappe
RUN usermod -aG sudo frappe
RUN printf '# User rules for frappe\nfrappe ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/frappe

# Generate locale C.UTF-8 for mariadb and general locale data
ENV LANG C.UTF-8

#nodejs
RUN curl --silent --location https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install -y nodejs

USER frappe
WORKDIR /home/frappe
RUN git clone -b master https://github.com/frappe/bench.git bench-repo

USER root
RUN pip install -e bench-repo
RUN apt-get install -y libmysqlclient-dev mariadb-client mariadb-common
RUN npm install -g yarn
RUN chown -R frappe:frappe /home/frappe/*

USER frappe
WORKDIR /home/frappe/frappe-bench
