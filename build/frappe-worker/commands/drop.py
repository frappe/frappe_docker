import os
import frappe

from frappe.commands.site import _drop_site
from constants import ARCHIVE_SITES_PATH
from utils import get_password


def main():
    site_name = os.environ.get("SITE_NAME", 'site1.localhost')
    db_root_username = os.environ.get("DB_ROOT_USER", 'root')
    mariadb_root_password = get_password("MYSQL_ROOT_PASSWORD", 'admin')
    postgres_root_password = get_password("POSTGRES_PASSWORD")
    db_root_password = mariadb_root_password

    if postgres_root_password:
        db_root_password = postgres_root_password

    force = True if os.environ.get("FORCE", None) else False
    no_backup = True if os.environ.get("NO_BACKUP", None) else False
    frappe.init(site_name, new_site=True)

    _drop_site(
        site=site_name,
        root_login=db_root_username,
        root_password=db_root_password,
        archived_sites_path=ARCHIVE_SITES_PATH,
        force=force,
        no_backup=no_backup
    )

    if frappe.redis_server:
        frappe.redis_server.connection_pool.disconnect()

    exit(0)


if __name__ == "__main__":
    main()
