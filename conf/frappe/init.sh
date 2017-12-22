#!/bin/bash

echo "----------------------- [ Install bench ] ---------------------------------"
git clone -b develop https://github.com/frappe/bench.git bench-repo
sudo pip install -e bench-repo
echo "----------------------- [ init bench ] ---------------------------------"
bench init frappe-bench --skip-bench-mkdir --skip-redis-config-generation
echo "----------------------- [ config bench ] ---------------------------------"
cd frappe-bench
mv /home/frappe/Procfile_docker /home/frappe/frappe-bench/Procfile
mv /home/frappe/common_site_config_docker.json /home/frappe/frappe-bench/sites/common_site_config.json
bench set-mariadb-host mariadb
echo "----------------------- [ new site ] ---------------------------------"
bench new-site site1.local --mariadb-root-password 123 --admin-password frappe
echo "----------------------- [ install erpnext ] ---------------------------------"
bench get-app erpnext https://github.com/frappe/erpnext
bench --site site1.local install-app erpnext
echo "----------------------- [ bench update ] ---------------------------------"
bench update
