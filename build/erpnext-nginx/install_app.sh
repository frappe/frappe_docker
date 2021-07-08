#!/bin/bash

npm i yarn -g
cd /home/frappe/frappe-bench/apps/frappe
rm -fr node_modules && yarn
cd /home/frappe/frappe-bench/sites
echo "frappe" > /home/frappe/frappe-bench/sites/apps.txt
echo "erpnext" >> /home/frappe/frappe-bench/sites/apps.txt
/home/frappe/frappe-bench/env/bin/python -c "import frappe; frappe.init(''); import frappe.build; frappe.build.setup(); frappe.build.make_asset_dirs(make_copy=True)"
node --use_strict ../apps/frappe/frappe/build.js --build
mkdir -p /home/frappe/sites
cp -R assets /home/frappe/sites
