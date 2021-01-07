ARG NODE_IMAGE_TAG=12-prod
ARG GIT_BRANCH=develop
FROM bitnami/node:${NODE_IMAGE_TAG}

ARG GIT_BRANCH
COPY build/erpnext-nginx/install_app.sh /install_app

RUN /install_app erpnext https://github.com/frappe/erpnext ${GIT_BRANCH}

FROM frappe/frappe-nginx:${GIT_BRANCH}

COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
COPY --from=0 /rsync /rsync
RUN echo "erpnext" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
