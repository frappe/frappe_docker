# This image uses nvm and same base image as the worker image.
# This is done to ensures that node-sass binary remains common.
# node-sass is required to enable website theme feature used
# by Website Manager role in Frappe Framework
ARG PYTHON_VERSION=3.9
FROM python:${PYTHON_VERSION}-slim-bullseye as builder

ARG GIT_REPO=https://github.com/frappe/frappe
ARG GIT_BRANCH=develop

ENV NODE_VERSION=14.18.1
ENV NVM_DIR=/root/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    git \
    build-essential \
    wget \
    python2 \
    && rm -rf /var/lib/apt/lists/*

# Install nvm with node and yarn
RUN wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && npm install -g yarn \
    && rm -rf ${NVM_DIR}/.cache

WORKDIR /home/frappe/frappe-bench

RUN mkdir -p apps sites/assets/css sites/assets/frappe /var/www/error_pages
RUN echo "frappe" > sites/apps.txt

RUN git clone --depth 1 -b ${GIT_BRANCH} ${GIT_REPO} apps/frappe
RUN cd apps/frappe \
    && yarn \
    && yarn run production \
    && yarn install --production=true

RUN git clone --depth 1 https://github.com/frappe/bench /tmp/bench \
    && cp -r /tmp/bench/bench/config/templates /var/www/error_pages

RUN cp -R apps/frappe/frappe/public/* sites/assets/frappe \
    && cp -R apps/frappe/node_modules sites/assets/frappe/

FROM nginx:latest

COPY --from=builder /home/frappe/frappe-bench/sites /var/www/html/
COPY --from=builder /var/www/error_pages /var/www/
COPY build/frappe-nginx/nginx-default.conf.template /etc/nginx/conf.d/default.conf.template
COPY build/frappe-nginx/docker-entrypoint.sh /

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    rsync \
    && rm -rf /var/lib/apt/lists/*

RUN echo "#!/bin/bash" > /rsync \
    && chmod +x /rsync

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
