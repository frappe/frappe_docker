FROM bitnami/node:10-prod

COPY build/erpnext-nginx/install_app.sh /install_app

RUN /install_app erpnext https://github.com/frappe/erpnext version-11

FROM frappe/frappe-nginx:v11

COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
COPY --from=0 /rsync /rsync
RUN echo -n "\nerpnext" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
