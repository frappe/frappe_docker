# Getting Started

## !! You need to be connected to WSL before proceeding

### Other Pre-requisites

To get started you need [Docker](https://docs.docker.com/get-docker/), [docker-compose](https://docs.docker.com/compose/), and [git](https://docs.github.com/en/get-started/getting-started-with-git/set-up-git) setup in WSL. For Docker basics and best practices refer to Docker's [documentation](http://docs.docker.com).
After that, clone this repo:

## Introduction

You will be working in the ```./development``` folder a.k.a. a dev workspace. Follow the steps below to set up the workspace.

## Workspace Setup

1. Clone the Repo into your working directory

```sh
git clone https://github.com/cronos-capital/RAFNAV-Docker.git
cd RAFNAV-Docker
```

2. Create the devcontainer and VsCode configuration from the templates provided

```sh
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode
```

## Build the Docker Image

Run the following command in your working directory

```sh
docker build -t rafnav_bench:latest ./images/bench
```

> You may change the tag to the relevant naming convention.

## Container Initialization

You have two option for starting the docker container for development:

1. Opening the folder in VS as a docker container.
2. Manually starting the container in the terminal.

### Reopen folder in dev container

1. Open the command pallet with *ctrl + shift + p*  or  *View->Command Pallet*

2. Run the command ```dev containers: rebuild and reopen in container```
3. Wait for the container to warm up...

### Manually start the container

1. Run the following script

```sh
sudo ./run-container.sh
```

> Note: Your **terminal** is now open in the development workspace. However, the VsCode **window** is not.

## Starting Development

1. Run the installer

  ```sh
  frap-install
  ```

**Note: For additional args and configs run ```frap-install --help``` first.**

2. cd into rafnav's development bench

```sh
cd rafnav_bench
```

3. Now you are able to start development on RAFNAV with all the dependencies and correct environment set up.

## Documentation

### Default Credentials
MariaDB Root Password: 123
> Unless changed in the docker or docker-compose file

First site's Administrator password: admin

> Unless changed in the docker or docker-compose file

### [Production](#production)

- [List of containers](docs/list-of-containers.md)
- [Single Compose Setup](docs/single-compose-setup.md)
- [Environment Variables](docs/environment-variables.md)
- [Single Server Example](docs/single-server-example.md)
- [Setup Options](docs/setup-options.md)
- [Site Operations](docs/site-operations.md)
- [Backup and Push Cron Job](docs/backup-and-push-cronjob.md)
- [Port Based Multi Tenancy](docs/port-based-multi-tenancy.md)
- [Migrate from multi-image setup](docs/migrate-from-multi-image-setup.md)
- [running on linux/mac](docs/setup_for_linux_mac.md)

### [Development](#development)

- [Container Aliases for easier development](docs/container-aliases.md)
- [Bench Console and VSCode Debugger](docs/bench-console-and-vscode-debugger.md)
- [Connect to localhost services](docs/connect-to-localhost-services-from-containers-for-local-app-development.md)
