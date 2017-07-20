db_ip=`getent hosts mariadb | awk '{ print $1 }'`
bench set-mariadb-host $db_ip 
bench new-site site1
bench get-app erpnext https://github.com/frappe/erpnext
bench --site site1 install-app erpnext
bench start

