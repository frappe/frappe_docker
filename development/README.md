# Getting Started

## Prerequisites

- Docker
- docker-compose
- user added to docker group

### Bootstrap Containers for development

Clone and change working directory to frappe_docker directory

```shell
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

#### Manually start containers

```shell
docker-compose -f .devcontainer/docker-compose.yml up -d
```

Enter the bench container

```shell
docker exec -e "TERM=xterm-256color" -w /workspace/development -it frappe bash
```

#### Use VSCode Remote Containers extension

- Install Remote Development Pack / Remote Containers extension
- Install VSCode Python extension
- Open frappe_docker in VSCode
- From Command Palette (Ctrl + Shift + P) Execute Remote Containers : Reopen in Container

### Setup Docker specific bench environment

Notes:

- `development` directory is ignored by it. It is mounted and available in container. Create all your benches inside this directory
- Execute these commands from container
- nvm with node v12 and v10 is installed. Check with `nvm ls`. Node v12 is default

#### Setup first bench

```shell
bench init --skip-redis-config-generation --frappe-branch version-12 frappe-bench
cd frappe-bench
```

#### Set hosts

```shell
bench set-mariadb-host mariadb
bench set-redis-cache-host redis-cache:6379
bench set-redis-queue-host redis-queue:6379
bench set-redis-socketio-host redis-socketio:6379
```

#### Changes related to bench start / honcho / Procfile

- honcho/Procfile starts processes required for development.
- By default Procfile has 3 redis processes that it starts. Comment (`#`) or remove these lines and then run `bench start`.
- Another option is to run following command

```shell
honcho start \
    web \
    socketio \
    watch \
    schedule \
    worker_short \
    worker_long \
    worker_default
```

#### Changes related to MariaDB

Notes:

- `bench new-site` command creates a user in mariadb with container IP as host
- After rebuilding container there is a chance that new bench container will not be able to access mariadb
- `'db_name'@'%'` needs to be set in mariadb and permission to the site database be given to the user
- Replace `db_name` and `db_password` from site's `site_config.json`
- MariaDB root password is 123

Enter mariadb shell

```shell
mysql -uroot -p123 -hmariadb
```

Execute following queries

```sql
UPDATE mysql.user SET Host = '%' where User = 'db_name'; FLUSH PRIVILEGES;
SET PASSWORD FOR 'db_name'@'%' = PASSWORD('db_password'); FLUSH PRIVILEGES;
GRANT ALL PRIVILEGES ON `db_name`.* TO 'db_name'@'%'; FLUSH PRIVILEGES;
```

### Visual Studio Code Python Debugging

- Install VSCode Python Extension once in remote container
- Reload VSCode
- Do not start `web` process with honcho

```shell
honcho start \
    socketio \
    watch \
    schedule \
    worker_short \
    worker_long \
    worker_default
```

- On debugger tab, Connect debugger. This will start the web process with debugger connected
