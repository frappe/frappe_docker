# Getting Started

## !! You need to be connected to WSL before proceeding

### Other Pre-requisites

To get started, you must have set up an [IT Workspace environment](https://steed-finance.atlassian.net/wiki/x/CQCQBg).
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
docker build -t rafnav_bench:latest ./images/rafnav_bench
```

> You may change the tag to the relevant naming convention. However, you need to change the image used for development in the correct docker-compose file: ./.devcontainer/docker-compose.yml

## Container Initialization

You have two options to start the docker container for development:

1. Opening the folder in VS as a docker container.
2. Manually starting the container in the terminal.

### Reopen the folder in the dev container

1. Open VsCode in the RAFNAV-Docker folder.
2. Open the command pallet with *ctrl + shift + p*  or  *View->Command Pallet*
3. Run the command ```dev containers: Reopen in container```
4. Wait for the container to warm up...

### Manually start the container

1. Run the following script

```sh
docker-compose -f .devcontainer/docker-compose.yml up -d && docker exec -e \"TERM=xterm-256color\" -w /workspace/development -it devcontainer-frappe-1 bash

```

> Note: Your **terminal** is now open in the development workspace. However, the VsCode **window** is not.

## Starting Development

### GitHub Login (SSH)

> Make sure you're setting it up for Linux

1. [Check for any existing SSH Key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/checking-for-existing-ssh-keys)
2. [Generate an SSH Key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
3. [Add it to your GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
4. [Test your connection](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection)

### RAFNAV Installation

#### Default Install

  ```sh
  frap-install
  ```

#### ERPNext with add-on apps

```sh
  frap-install -j apps-erpnext.json
```

#### Development Branch Apps Install

```sh
  frap-install -j apps-development.json
```

#### Prod Apps Install

 ```sh
  frap-install -j apps-prod.json
  ```


**Note: For additional args and configs run ```frap-install --help``` first.**

2. cd into Rafnav's development bench

```sh
cd rafnav_bench
```

3. Now you are able to start development on RAFNAV with all the dependencies and the correct environment set-up.

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

- [Docker Image Development](docs/Docker-Image-Development.md)
- [Container Aliases for easier development](docs/container-aliases.md)
- [Multi-tenancy Setup in Development (Developing on multiple site)](docs/multi-tenancy.md)
- [Bench Console and VSCode Debugger](docs/bench-console-and-vscode-debugger.md)
- [Connect to localhost services](docs/connect-to-localhost-services-from-containers-for-local-app-development.md)
