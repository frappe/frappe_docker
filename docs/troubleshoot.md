1. [Fixing MariaDB issues after rebuilding the container](#fixing-mariadb-issues-after-rebuilding-the-container)
1. [Letsencrypt companion not working](#letsencrypt-companion-not-working)
1. [docker-compose does not recognize variables from `.env` file](#docker-compose-does-not-recognize-variables-from-env-file)
1. [Windows Based Installation](#windows-based-installation)

### Fixing MariaDB issues after rebuilding the container

For any reason after rebuilding the container if you are not be able to access MariaDB correctly with the previous configuration. Follow these instructions.

The parameter `'db_name'@'%'` needs to be set in MariaDB and permission to the site database suitably assigned to the user.

This step has to be repeated for all sites available under the current bench.
Example shows the queries to be executed for site `localhost`

Open sites/localhost/site_config.json:

```shell
code sites/localhost/site_config.json
```

and take note of the parameters `db_name` and `db_password`.

Enter MariaDB Interactive shell:

```shell
mysql -uroot -p123 -hmariadb
```

Execute following queries replacing `db_name` and `db_password` with the values found in site_config.json.

```sql
UPDATE mysql.user SET Host = '%' where User = 'db_name'; FLUSH PRIVILEGES;
SET PASSWORD FOR 'db_name'@'%' = PASSWORD('db_password'); FLUSH PRIVILEGES;
GRANT ALL PRIVILEGES ON `db_name`.* TO 'db_name'@'%'; FLUSH PRIVILEGES;
EXIT;
```

### Letsencrypt companion not working

- Nginx Letsencrypt Companion needs to be setup before starting ERPNext services.
- Are domain names in `SITES` variable correct?
- Is DNS record configured? `A Name` record needs to point to Public IP of server.
- Try Restarting containers.

### docker-compose does not recognize variables from `.env` file

If you are using old version of `docker-compose` the .env file needs to be located in directory from where the docker-compose command is executed. There may also be difference in official `docker-compose` and the one packaged by distro.

### Windows Based Installation

- Set environment variable `COMPOSE_CONVERT_WINDOWS_PATHS` e.g. `set COMPOSE_CONVERT_WINDOWS_PATHS=1`
- Make the `frappe-mariadb.cnf` read-only for mariadb container to pick it up.
- While using docker machine, port-forward the port 80 of VM to port 80 of host machine
- Name all the sites ending with `.localhost`. and access it via browser locally. e.g. `http://site1.localhost`
- related issue comment https://github.com/frappe/frappe_docker/issues/448#issuecomment-851723912
