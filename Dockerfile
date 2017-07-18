
#bench Dockerfile

FROM ubuntu:16.04
MAINTAINER Vishal Seshagiri

USER root
RUN apt-get update
RUN apt-get install -y git build-essential python-setuptools python-dev libffi-dev libssl-dev
RUN apt-get install -y redis-tools software-properties-common libxrender1 libxext6 xfonts-75dpi xfonts-base
RUN apt-get install -y libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev python-tk apt-transport-https libsasl2-dev libldap2-dev libtiff5-dev tcl8.6-dev tk8.6-dev
RUN apt-get install -y wget
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py
RUN pip install --upgrade setuptools pip
RUN useradd -ms /bin/bash frappe
RUN apt-get install -y curl
RUN apt-get install -y rlwrap
RUN apt-get install redis-server
RUN apt-get install -y nano

#nodejs
RUN apt-get install curl
RUN curl https://deb.nodesource.com/node_6.x/pool/main/n/nodejs/nodejs_6.7.0-1nodesource1~xenial1_amd64.deb > node.deb \
 && dpkg -i node.deb \
 && rm node.deb
RUN apt-get install -y wkhtmltopdf

USER frappe
WORKDIR /home/frappe
RUN git clone https://github.com/frappe/bench bench-repo

USER root
RUN pip install -e bench-repo
RUN apt-get install -y libmysqlclient-dev mariadb-client mariadb-common

#Scripts to be added to docker file
#USER frappe
#RUN bench init frappe-bench && cd frappe-bench

#USER root
#RUN cd /home/frappe
#RUN ls -l
# frappe-bench apps sites
#

# On the host machine run
# docker ps - to get the id of mariadb container
# docker inspect <mariadb-container-id>
# get the IP address of the mariadb container which looks similar to this

# In the docker frappe container run
# bench set-mariadb-host 172.20.0.2


#RUN bench new-site site1
#RUN bench get-app erpnext https://github.com/frappe/erpnext
#RUN bench --site site1 install-app erpnext
#RUN bench start

