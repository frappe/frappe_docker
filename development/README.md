# Getting Started

## Prerequisites

- Docker
- docker-compose
- user added to docker group

## Bootstrap Containers for development

Clone and change directory to frappe_docker directory

```shell
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

## Use VSCode Remote Containers extension

For most people getting started with Frappe development, the best solution is to use [ VSCode Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

- Install Remote - Containers for VSCode
    - through command line `code --install-extension ms-vscode-remote.remote-containers`
    - clicking on the following link: [install](vscode:extension/ms-vscode-remote.remote-containers)
- Install Python for VSCode
    - through command line `code --install-extension ms-python.python`
    - clicking on the following link: [install](vscode:extension/ms-python.python)
- Open frappe_docker folder in VS Code.
    - `code .`
- From Command Palette (Ctrl + Shift + P) Execute Remote Containers : Reopen in Container. You can also click in the bottom left corner to access the remote container menu.

Notes:

- The `development` directory is ignored by git. It is mounted and available inside the container. Create all your benches (installations of bench, the tool that manages frappe) inside this directory.
- nvm with node v12 and v10 is installed. Check with `nvm ls`. Node v12 is default.

### Setup first bench

Run the following commands in the terminal inside the container. You might need to create a new terminal in VSCode.

```shell
bench init --skip-redis-config-generation --frappe-branch version-12 frappe-bench
cd frappe-bench
```

### Setup hosts

We need to tell bench to use the right containers instead of localhosts. Run the following commands inside the container:

```shell
bench set-mariadb-host mariadb
bench set-redis-cache-host redis-cache:6379
bench set-redis-queue-host redis-queue:6379
bench set-redis-socketio-host redis-socketio:6379
```

### Edit Honcho's Procfile

Honcho is the tool used by Bench to manage all the processes Frappe requires. Usually, these all run in localhost, but in this case we have external containers for Redis. For this reason, we have to stop Honcho from trying to start Redis processes.

Open the Procfile file and remove the three lines containing the configuration from Redis, either by editing manually the file

```shell
code Procfile
```

or running the following command:
```shell
sed -i '/redis/d' ./Procfile
```

### Create a new site with bench

You can create a new site with the following command

```shell
bench new-site sitename
```

for example:

```shell
bench new-site localhost
```

The command will ask the MariaDB root password. The default root password is `123`
Your website will now be accessible on [localhost on port 8000](http://locahost:8000)

### Fixing MariaDB issues after rebuilding the container

The `bench new-site` command creates a user in MariaDB with container IP as host, for this reason after rebuilding the container there is a chance that you will not be able to access MariaDB correctly with the previous configuration
The parameter `'db_name'@'%'` needs to be set in MariaDB and permission to the site database properly assigned to the user.

Open sites/common_site_config.json:


```shell
code sites/common_site_config.json
```

and take note of the parameters `db_name` and `db_password`.

Enter MariaDB Interactive shell:

```shell
mysql -uroot -p123 -hmariadb
```

Execute following queries replacing db_name` and `db_password` with the values found in common_site_config.json.

```sql
UPDATE mysql.user SET Host = '%' where User = 'db_name'; FLUSH PRIVILEGES;
SET PASSWORD FOR 'db_name'@'%' = PASSWORD('db_password'); FLUSH PRIVILEGES;
GRANT ALL PRIVILEGES ON `db_name`.* TO 'db_name'@'%'; FLUSH PRIVILEGES;
EXIT;
```

## Manually start containers

In case you don't use VSCode, you may start the containers manually with the following command:

```shell
docker-compose -f .devcontainer/docker-compose.yml up -d
```

And enter the interactive shell for the development container with the following command:

```shell
docker exec -e "TERM=xterm-256color" -w /workspace/development -it devcontainer_frappe_1 bash
```

### Visual Studio Code Python Debugging

To enable Python debugging inside Visual Studio Code, you must first install the `ms-python.python` extension inside the container.

- Click on the extensions icon of VSCode
- Search `ms-python.python`
- Click on `Install on Dev Container: Frappe Bench`
- Click on 'Reload'

We need to start bench separately through the VSCode debugger. For this reason, **instead** of running `bench start` you should run the following command inside the frappe-bench directory:

```shell
honcho start \
    socketio \
    watch \
    schedule \
    worker_short \
    worker_long \
    worker_default
```

This command starts all processes but Redis (which is already running in separate container) and the `web` process, which we can finally start from the debugger tab of VSCode.
