#!/bin/bash

SITE_CONFIG_PATH="/home/frappe/frappe-bench/sites/site1.local/site_config.json"

echo "ERPNext başlangıç betiği başlatılıyor..."

if [ ! -f "$SITE_CONFIG_PATH" ]; then
    echo "Yeni bir ERPNext sitesi oluşturuluyor: site1.local"
    bench init frappe-bench --skip-redis-config-generation --frappe-branch version-14

    cd /home/frappe/frappe-bench

    bench get-app erpnext --branch version-14
    bench new-site site1.local \
        --mariadb-root-password root \
        --admin-password admin \
        --install-app erpnext

    echo "ERPNext sitesi başarıyla oluşturuldu."
else
    echo "'site1.local' zaten mevcut."
fi

cd /home/frappe/frappe-bench
echo "ERPNext başlatılıyor..."
bench start
