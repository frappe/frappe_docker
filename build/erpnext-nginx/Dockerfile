ARG NODE_IMAGE_TAG=12-prod
FROM bitnami/node:${NODE_IMAGE_TAG}

COPY build/erpnext-nginx/install_app.sh /install_app

ARG GIT_BRANCH=develop
RUN /install_app erpnext https://github.com/frappe/erpnext ${GIT_BRANCH}

ARG GIT_BRANCH=develop
FROM frappe/frappe-nginx:${GIT_BRANCH}

COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
COPY --from=0 /rsync /rsync
RUN echo -n "\nerpnext" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
