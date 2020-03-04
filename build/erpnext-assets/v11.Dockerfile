FROM bitnami/node:10-prod

COPY build/erpnext-assets/install_app.sh /install_app

RUN /install_app erpnext https://github.com/frappe/erpnext version-11

FROM frappe/frappe-assets:v11
RUN cp /home/frappe/frappe-bench/sites/apps.txt /home/frappe/frappe-bench/sites/apps.bak
COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
RUN mv /home/frappe/frappe-bench/sites/apps.bak /home/frappe/frappe-bench/sites/apps.txt \
  && echo -n "\nerpnext" >> /home/frappe/frappe-bench/sites/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
