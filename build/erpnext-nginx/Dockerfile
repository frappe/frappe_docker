ARG IMAGE_TAG=v10
ARG DOCKER_REGISTRY_PREFIX=frappe
FROM ${DOCKER_REGISTRY_PREFIX}/erpnext-worker:${IMAGE_TAG}

COPY build/erpnext-nginx/install_app.sh /install_app

RUN /install_app

FROM ${DOCKER_REGISTRY_PREFIX}/frappe-nginx:${IMAGE_TAG}

COPY --from=0 /home/frappe/sites /var/www/html
RUN echo "erpnext" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
