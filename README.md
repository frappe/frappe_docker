# RAFNAV Docker Setup & Usage

## Development

> !! You need to be connected to WSL before proceeding

### Pre-requisites

To get started, you must have set up an [IT Workspace environment](https://steed-finance.atlassian.net/wiki/x/CQCQBg).

### Introduction

You will be working in the ```./development``` folder a.k.a. a dev workspace. Follow the steps below to set up the workspace.

### Workspace Setup

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

> You may change the tag to a more relevant naming convention. However, you need to change the image used for development in the correct docker-compose file: ./.devcontainer/docker-compose.yml

### Container Initialization

We will be attaching a VS Code window to the docker container workspace. This requires the [dev containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

1. Open the RAFNAV-Docker folder with Vs Code.
2. Open the command pallet with *ctrl + shift + p*  or  *View->Command Pallet*
3. Run the command ```dev containers: Reopen in container```
4. Wait for the container to warm up...

### GitHub Login (GitHub CLI)

- Make sure you have git and Github CLI installed on **windows**
- Log in to GitHub from VsCode to sync your github credentials with GitHub

### RAFNAV Installation

#### Development Branch Apps Install

```sh
  frap-install -j apps-development.json -v
```

#### Prod Apps Install

 ```sh
  frap-install -j apps-prod.json -v
  ```

**Note: For additional args and configs run ```frap-install --help``` first.**

2. cd into Rafnav's development bench. An alias has already been assigned. Run the following command:

```sh
go-rafnav_bench
```

1. Now you are able to start development on RAFNAV with all the dependencies and the correct environment set-up.

### Default Credentials

MariaDB Root Password: 123
> Unless changed in the docker or docker-compose file

First site's Administrator password: admin

> Unless changed in the docker or docker-compose file

## Deployment

### Apps List

1. Specify a list of apps in a JSON file called 'apps.json'

```json
[
  {
    "url": "https://{{PAT}}@github.com/cronos-capital/rafnav_core.git",
    "branch": "main"
  },
  {
    "url": "https://{{PAT}}@github.com/cronos-capital/matter_management.git",
    "branch": "main"
  },
  {
    "url": "https://{{PAT}}@github.com/cronos-capital/raf_finance.git",
    "branch": "main"
  },
  {
    "url": "https://{{PAT}}@github.com/cronos-capital/filing.git",
    "branch": "main"
  },
  {
    "url": "https://{{PAT}}@github.com/cronos-capital/documentation.git",
    "branch": "main"
  }
]
```

>Note: {{PAT}} replace with your personal access token from GitHub

2. Generate a Base 64 shell variable of the apps list. This will be passed as a build argument for the docker image later

```sh
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)
```

### Image Build

Build the production version of the image using

```sh
docker build --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 -t rafnav/rafnav_bench:prod --file=images/production/Containerfile .
```

### Publish Image

Publish the newly built docker image to docker hub using your PAT from Docker Hub

1. Log in to Docker if not already

```sh
docker login -u [username]
```

2. At the password prompt, paste your PAT
3. Push the image using the following command:

```sh
docker push rafnav/rafnav_bench:prod
```

## Common Operations

### New Site

```sh
bench new-site [site_name] --mariadb-user-host-login-scope='%' --admin-password [pwd] --verbose
```

### Installing RAFNav

```sh
bench --site [site_name] install-app rafnav_core matter_management filing documentation raf_finance
```

## Resources

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
