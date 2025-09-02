FROM frappe/erpnext:v15.74.0

# Install frappe_wiki
RUN bench get-app https://github.com/frappe/wiki