import os, frappe, json

from frappe.commands.site import _new_site
from check_connection import get_config, get_site_config

def main():
    site_name = os.environ.get("SITE_NAME", 'site1.localhost')
    mariadb_root_username = os.environ.get("DB_ROOT_USER", 'root')
    mariadb_root_password = os.environ.get("MYSQL_ROOT_PASSWORD", 'admin')
    force = True if os.environ.get("FORCE", None) else False
    install_apps = os.environ.get("INSTALL_APPS", None)
    install_apps = install_apps.split(',') if install_apps else []
    frappe.init(site_name, new_site=True)

    _new_site(
        None,
        site_name,
        mariadb_root_username=mariadb_root_username,
        mariadb_root_password=mariadb_root_password,
        admin_password=os.environ.get("ADMIN_PASSWORD", 'admin'),
        verbose=True,
        install_apps=install_apps,
        source_sql=None,
        force=force,
        reinstall=False,
    )

    config = get_config()

    site_config = get_site_config(site_name)

    mysql_command = 'mysql -h{db_host} -u{mariadb_root_username} -p{mariadb_root_password} -e '.format(
        db_host=config.get('db_host'),
        mariadb_root_username=mariadb_root_username,
        mariadb_root_password=mariadb_root_password
    )

    # update User's host to '%' required to connect from any container
    command = mysql_command + "\"UPDATE mysql.user SET Host = '%' where User = '{db_name}'; FLUSH PRIVILEGES;\"".format(
        db_name=site_config.get('db_name')
    )
    os.system(command)

    # Set db password
    command = mysql_command + "\"UPDATE mysql.user SET authentication_string = PASSWORD('{db_password}') WHERE User = \'{db_name}\' AND Host = \'%\';\"".format(
        db_name=site_config.get('db_name'),
        db_password=site_config.get('db_password')
    )
    os.system(command)

    # Grant permission to database
    command = mysql_command + "\"GRANT ALL PRIVILEGES ON \`{db_name}\`.* TO '{db_name}'@'%'; FLUSH PRIVILEGES;\"".format(
        db_name=site_config.get('db_name')
    )
    os.system(command)
    exit(0)

if __name__ == "__main__":
    main()
