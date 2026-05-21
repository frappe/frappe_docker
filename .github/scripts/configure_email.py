import os, sys

# bench creates these on startup; raw Python does not
for _p in ('/home/frappe/logs', '/home/frappe/frappe-bench/logs'):
    os.makedirs(_p, exist_ok=True)

import frappe

site     = os.environ.get('SITE_NAME', '')
login    = os.environ.get('MAIL_LOGIN', '')
server   = os.environ.get('MAIL_SERVER', '')
port     = int(os.environ.get('MAIL_PORT', '587'))
use_tls  = int(os.environ.get('MAIL_USE_TLS', '1'))
password = os.environ.get('MAIL_PASSWORD', '')
sender   = os.environ.get('MAIL_DEFAULT_SENDER') or login

if not (site and login and server):
    sys.exit(0)

frappe.init(site=site, sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

existing = frappe.db.get_value('Email Account', {'email_id': login}, 'name')
if existing:
    doc = frappe.get_doc('Email Account', existing)
else:
    doc = frappe.new_doc('Email Account')
    doc.email_account_name = 'System Notifications'
    doc.email_id = login

doc.smtp_server = server
doc.smtp_port = port
doc.use_tls = use_tls
doc.password = password
doc.enable_outgoing = 1
doc.default_outgoing = 1

if existing:
    doc.save(ignore_permissions=True)
else:
    doc.insert(ignore_permissions=True)

frappe.db.commit()
frappe.destroy()
print('Email account configured as default outgoing.')