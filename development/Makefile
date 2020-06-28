clean-init:
	@sudo rm -R frappe-bench -f
	@bench init --skip-redis-config-generation --frappe-branch version-12 frappe-bench

install:
	@cd ./frappe-bench && \
	  bench set-mariadb-host mariadb && \
	  bench set-redis-cache-host redis-cache:6379 && \
	  bench set-redis-queue-host redis-queue:6379 && \
	  bench set-redis-socketio-host redis-socketio:6379 && \
	  bench new-site mysite.localhost --mariadb-root-password 123 --admin-password admin --no-mariadb-socket && \
	  bench get-app --branch version-12 erpnext https://github.com/frappe/erpnext.git && \
	  bench --site mysite.localhost install-app erpnext

drop:
	@cd ./frappe-bench && \
	  bench drop-site mysite.localhost --force
