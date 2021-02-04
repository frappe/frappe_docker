ARG NODE_IMAGE_TAG=12-buster-slim
ARG GIT_BRANCH=version-12
ARG DOCKER_REGISTRY_PREFIX=graficheaquilane
FROM node:${NODE_IMAGE_TAG}

ARG GIT_BRANCH
COPY build/erpnext-nginx/install_app.sh /install_app
RUN chmod +x /install_app && \
  apt-get update -y && \
  apt-get install build-essential git python2 -y && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

RUN sed -i 's/\r$//' install_app
RUN bash /install_app erpnext https://github.com/GraficheAquilane2021/erpnext ${GIT_BRANCH}

FROM ${DOCKER_REGISTRY_PREFIX}/frappe-nginx:${GIT_BRANCH}

COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
COPY --from=0 /rsync /rsync
RUN echo "erpnext" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]