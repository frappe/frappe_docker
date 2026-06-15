#!/bin/bash
bin/bench.sh new-site ranch.localhost \
  --db-root-username=root \
  --db-host=db \
  --db-type=mariadb \
  --mariadb-user-host-login-scope=% \
  --db-root-password=123 \
  --admin-password=123

bin/bench.sh --site ranch.localhost set-config developer_mode true

bin/bench.sh --site ranch.localhost install-app erpnext

for app in $(find apps -mindepth 1 -maxdepth 1 -type d | xargs -n1 basename); do
  docker compose -p ranch exec backend bash -lc "cd /home/frappe/frappe-bench && ./env/bin/pip install -e apps/${app}"
  docker compose -p ranch exec backend bash -lc "cd /home/frappe/frappe-bench; grep -qxF ${app} sites/apps.txt || printf '%s\\n' '${app}' >> sites/apps.txt"
  bin/bench.sh --site ranch.localhost install-app "${app}"
done

bin/bench.sh --site ranch.localhost migrate
bin/bench.sh --site ranch.localhost clear-cache
docker compose -p ranch restart backend queue-short queue-long scheduler

echo "Done! Access your local dev environment at http://ranch.localhost"
