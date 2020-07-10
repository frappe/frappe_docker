import os
import frappe

from frappe.utils import cint, get_sites
from utils import get_config, save_config


def set_maintenance_mode(enable=True):
    conf = get_config()

    if enable:
        conf.update({"maintenance_mode": 1, "pause_scheduler": 1})
        save_config(conf)

    if not enable:
        conf.update({"maintenance_mode": 0, "pause_scheduler": 0})
        save_config(conf)


def migrate_sites(maintenance_mode=False):
    installed_sites = ":".join(get_sites())
    sites = os.environ.get("SITES", installed_sites).split(":")
    if not maintenance_mode:
        maintenance_mode = cint(os.environ.get("MAINTENANCE_MODE"))

    if maintenance_mode:
        set_maintenance_mode(True)

    for site in sites:
        print('Migrating', site)
        frappe.init(site=site)
        frappe.connect()
        try:
            from frappe.migrate import migrate
            migrate()
        finally:
            frappe.destroy()

    # Disable maintenance mode after migration
    set_maintenance_mode(False)


def main():
    migrate_sites()
    if frappe.redis_server:
        frappe.redis_server.connection_pool.disconnect()
    exit(0)


if __name__ == "__main__":
    main()
