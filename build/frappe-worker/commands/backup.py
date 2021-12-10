import os
import frappe
from frappe.utils.backups import scheduled_backup
from frappe.utils import cint, get_sites, now


def backup(sites, with_files=False):
    for site in sites:
        frappe.init(site)
        frappe.connect()
        odb = scheduled_backup(
            ignore_files=not with_files,
            backup_path_db=None,
            backup_path_files=None,
            backup_path_private_files=None,
            force=True
        )
        print("database backup taken -", odb.backup_path_db, "- on", now())
        if with_files:
            print("files backup taken -", odb.backup_path_files, "- on", now())
            print("private files backup taken -", odb.backup_path_private_files, "- on", now())
        frappe.destroy()


def main():
    installed_sites = ":".join(get_sites())
    sites = os.environ.get("SITES", installed_sites).split(":")
    with_files = cint(os.environ.get("WITH_FILES"))

    backup(sites, with_files)

    if frappe.redis_server:
        frappe.redis_server.connection_pool.disconnect()

    exit(0)


if __name__ == "__main__":
    main()
