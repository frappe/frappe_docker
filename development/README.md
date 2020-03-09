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

VSCode should automatically inquiry you to install the required extensions, that can also be installed manually as follows:

- Install Remote - Containers for VSCode
    - through command line `code --install-extension ms-vscode-remote.remote-containers`
    - clicking on the button at the following link: [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
    - searching for extension `ms-vscode-remote.remote-containers`
- Install Python for VSCode
    - through command line `code --install-extension ms-python.python`
    - clicking on the button at the following link: [install](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
    - searching for extension `ms-python.python`

After the extensions are installed, you can:

- Open frappe_docker folder in VS Code.
    - `code .`
- Launch the command, from Command Palette (Ctrl + Shift + P) `Execute Remote Containers : Reopen in Container`. You can also click in the bottom left corner to access the remote container menu.

Notes:

- The `development` directory is ignored by git. It is mounted and available inside the container. Create all your benches (installations of bench, the tool that manages frappe) inside this directory.
- nvm with node v12 and v10 is installed. Check with `nvm ls`. Node v12 is used by default.

### Setup first bench

Run the following commands in the terminal inside the container. You might need to create a new terminal in VSCode.

```shell
bench init --skip-redis-config-generation --frappe-branch version-12 frappe-bench
cd frappe-bench
```

### Setup hosts

We need to tell bench to use the right containers instead of localhost. Run the following commands inside the container:

```shell
bench set-mariadb-host mariadb
bench set-redis-cache-host redis-cache:6379
bench set-redis-queue-host redis-queue:6379
bench set-redis-socketio-host redis-socketio:6379
```

### Edit Honcho's Procfile

Honcho is the tool used by Bench to manage all the processes Frappe requires. Usually, these all run in localhost, but in this case, we have external containers for Redis. For this reason, we have to stop Honcho from trying to start Redis processes.

Open the Procfile file and remove the three lines containing the configuration from Redis, either by editing manually the file.

```shell
code Procfile
```

or running the following command:
```shell
sed -i '/redis/d' ./Procfile
```

### Create a new site with bench

You can create a new site with the following command:

```shell
bench new-site sitename
```

for example:

```shell
bench new-site localhost
```

The command will ask the MariaDB root password. The default root password is `123`.
This will create a new site and a `localhost` directory under `frappe-bench/sites`.
Your website will now be accessible on [localhost on port 8000](http://locahost:8000)

### Fixing MariaDB issues after rebuilding the container

The `bench new-site` command creates a user in MariaDB with container IP as host, for this reason after rebuilding the container there is a chance that you will not be able to access MariaDB correctly with the previous configuration
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

- Click on the extension icon inside VSCode
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

This command starts all processes with the exception of Redis (which is already running in separate container) and the `web` process. The latter can can finally be started from the debugger tab of VSCode.
