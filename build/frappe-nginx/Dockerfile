# This image uses nvm and same base image as the worker image.
# This is done to ensures that node-sass binary remains common.
# node-sass is required to enable website theme feature used
# by Website Manager role in Frappe Framework
FROM python:3.7-slim-buster

ARG GIT_REPO=https://github.com/frappe/frappe
ARG GIT_BRANCH=develop

ENV NVM_DIR=/root/.nvm
ENV NODE_VERSION=14.17.0
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN apt-get update -y \
    && apt-get install wget python2 git build-essential -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && wget https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh \
    && chmod +x install.sh \
    && ./install.sh \
    && . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} && npm install -g yarn

WORKDIR /home/frappe/frappe-bench
RUN mkdir -p /home/frappe/frappe-bench/sites \
    && echo "frappe" > /home/frappe/frappe-bench/sites/apps.txt

RUN mkdir -p apps sites/assets/css  \
    && cd apps \
    && git clone --depth 1 ${GIT_REPO} --branch $GIT_BRANCH

RUN cd /home/frappe/frappe-bench/apps/frappe \
    && yarn \
    && yarn run production \
    && yarn install --production=true

RUN node --version \
    && npm --version \
    && yarn --version

RUN git clone --depth 1 https://github.com/frappe/bench /tmp/bench \
    && mkdir -p /var/www/error_pages \
    && cp -r /tmp/bench/bench/config/templates /var/www/error_pages

RUN mkdir -p /home/frappe/frappe-bench/sites/assets/frappe/ \
    && cp -R /home/frappe/frappe-bench/apps/frappe/frappe/public/* /home/frappe/frappe-bench/sites/assets/frappe \
    && cp -R /home/frappe/frappe-bench/apps/frappe/node_modules /home/frappe/frappe-bench/sites/assets/frappe/

FROM nginx:latest
COPY --from=0 /home/frappe/frappe-bench/sites /var/www/html/
COPY --from=0 /var/www/error_pages /var/www/
COPY build/common/nginx-default.conf.template /etc/nginx/conf.d/default.conf.template
COPY build/frappe-nginx/docker-entrypoint.sh /

RUN apt-get update && apt-get install -y rsync && apt-get clean \
    && echo "#!/bin/bash" > /rsync \
    && chmod +x /rsync

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
