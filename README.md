# Getting Started

**!! You need to be connected to WSL before proceeding**

To get started you need [Docker](https://docs.docker.com/get-docker/), [docker-compose](https://docs.docker.com/compose/), and [git](https://docs.github.com/en/get-started/getting-started-with-git/set-up-git) setup in WSL. For Docker basics and best practices refer to Docker's [documentation](http://docs.docker.com).
After that, clone this repo:

## Introduction
You will be working in the ```./development``` folder a.k.a. workspace. Follow the steps below to set up the workspace.

## Workspace Setup

1. Clone Repo into your working directory
```sh
git clone https://github.com/cronos-capital/RAFNAV-Docker.git
cd RAFNAV-Docker
```
2. Create the devcontainer and VsCode configuration from the templates provided
```sh
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode
```

## Build the Image

Run the following command in your working directory
```sh
docker build -t rafnav_bench:latest ./images/bench
```

## Container Initialization
1. Open the command pallet with *ctrl + shift + p*  or  *View->Command Pallet*

2. Run the command ```dev containers: rebuild and reopen in container```
3. Wait for the container to warm up...

# Starting Development

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

# Documentation

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

- [Bench Console and VSCode Debugger](docs/bench-console-and-vscode-debugger.md)
- [Connect to localhost services](docs/connect-to-localhost-services-from-containers-for-local-app-development.md)
