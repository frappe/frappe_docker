| Develop | [![Build Status](https://travis-ci.com/frappe/frappe_docker.svg?branch=develop)](https://travis-ci.com/frappe/frappe_docker)  |
|---------|-----------------------------------------------------------------------------------------------------------------------------|
| Master  | [![Build Status](https://travis-ci.com/frappe/frappe_docker.svg?branch=master)](https://travis-ci.com/frappe/frappe_docker) |

## Table of Contents

- [Try in Play With Docker](#try-in-play-with-docker)
- [Installation](#installation)
   - [Docker Installation](#docker-installation)
      - [Setting up Pre-requisites](#setting-up-pre-requisites)
      - [Development Setup](#development-setup)
      - [Production Setup](#production-setup)
   - [Easy Install Script](#easy-install-script)
   - [Manual Installation](#manual-installation)
- [Contribution](#contributing)

## Try in Play With Docker

<a href="https://labs.play-with-docker.com/?stack=https://raw.githubusercontent.com/frappe/frappe_docker/develop/tests/pwd.yml">
  <img src="https://raw.githubusercontent.com/play-with-docker/stacks/master/assets/images/button.png" alt="Try in PWD"/>
</a>

Wait for 5 minutes for ERPNext site to be created or check `site-creator` container logs before opening browser on port 80. (username: `Administrator`, password: `admin`)

## Installation

A typical bench setup provides two types of environments &mdash; Development and Production.

The setup for each of these installations can be achieved in multiple ways:

- [Docker Installation](#docker-installation)
- [Easy Install Script](#easy-install-script)
- [Manual Installation](#manual-installation)

We recommend using either the Docker Installation or the Easy Install Script to setup a Production Environment. For Development, you may choose either of the three methods to setup an instance.

Otherwise, if you are looking to evaluate ERPNext, you can also download the [Virtual Machine Image](https://erpnext.com/download) or register for [a free trial on erpnext.com](https://erpnext.com/pricing).


### Docker Installation

A Frappe/ERPNext instance can be setup and replicated easily using [Docker](https://docker.com). The officially supported Docker installation can be used to setup either of both Development and Production environments.

To setup either of the environments, you will need to clone the official docker repository:

```sh
$ git clone https://github.com/frappe/frappe_docker.git
$ cd frappe_docker
```

#### Setting up Pre-requisites

This repository requires Docker, docker-compose and Git to be setup on the instance to be used.

For Docker basics and best practices. Refer Docker [documentation](http://docs.docker.com).

#### Production Setup

It takes care of the following:

* Setting up the desired version of Frappe/ERPNext.
* Setting up all the system requirements: eg. MariaDB, Node, Redis.
* Configure networking for remote access and setting up LetsEncrypt.

It doesn't take care of the following:

* Cron Job to backup sites is not created by default.
* Use `CronJob` on k8s or refer wiki for alternatives.

1. Single Server Installs
    1. [Single bench](docs/single-bench.md). Easiest Install!
    2. [Multi bench](docs/multi-bench.md)
2. Multi Server Installs
    1. [Docker Swarm](docs/docker-swarm.md)
    2. [Kubernetes](https://helm.erpnext.com)
3. [Site Operations](docs/site-operations.md)
4. [Environment Variables](docs/environment-variables.md)
5. [Custom apps for production](docs/custom-apps-for-production.md)
6. [Tips for moving deployments](docs/tips-for-moving-deployments.md)
7. [Wiki for optional recipes](https://github.com/frappe/frappe_docker/wiki)

Copy the `env-example` file to `.env`

```sh
$ cp env-example .env
```

Optionally, you may also setup an [NGINX Proxy for SSL Certificates](https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion) with auto-renewal for your Production instance. We recommend this for instances being accessed over the internet. For this to work, the DNS needs to be configured correctly so that [LetsEncrypt](https://letsencrypt.org) can verify the domain. To setup the proxy, run the following commands:

```sh
$ git clone https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion.git
$ cd docker-compose-letsencrypt-nginx-proxy-companion
$ cp .env.sample .env
$ ./start.sh
```

To get the Production instance running, run the following command:

```sh
$ docker-compose \
    --project-name <project-name> \
    -f installation/docker-compose-common.yml \
    -f installation/docker-compose-erpnext.yml \
    -f installation/docker-compose-networks.yml \
    --project-directory installation up -d
```

Make sure to replace `<project-name>` with whatever you wish to call it. This should get the instance running through docker. Now, to create a new site on the instance you may run:

```sh
docker exec -it \
    -e "SITE_NAME=$SITE_NAME" \
    -e "DB_ROOT_USER=$DB_ROOT_USER" \
    -e "MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD" \
    -e "ADMIN_PASSWORD=$ADMIN_PASSWORD" \
    -e "INSTALL_APPS=erpnext" \ # optional, if you want to install any other apps
    <project-name>_erpnext-python_1 docker-entrypoint.sh new
```

Once this is done, you may access the instance at `$SITE_NAME`.

**Note:** The Production setup does not contain, require, or use bench. For a list of substitute commands, check out the [Frappe/ERPNext Docker Site Operations](https://github.com/frappe/frappe_docker/#site-operations).

#### Development Setup

To setup a development environment for Docker, follow the [Frappe/ERPNext Docker for Development Guide](https://github.com/frappe/frappe_docker/blob/develop/development/README.md).

It takes care of complete setup to develop with Frappe/ERPNext and Bench, Including the following features:

- VSCode containers integration
- VSCode Python debugger
- Pre-configured Docker containers for an easy start

[Start development](development).

### Easy Install Script

The Easy Install script should get you going with a Frappe/ERPNext setup with minimal manual intervention and effort. Since there are a lot of configurations being automatically setup, we recommend executing this script on a fresh server.

**Note:** This script works only on GNU/Linux based server distributions, and has been designed and tested to work on Ubuntu 16.04+, CentOS 7+, and Debian-based systems.

#### Prerequisites

You need to install the following packages for the script to run:

- ##### Ubuntu and Debian-based Distributions:

  ```sh
  $ apt install python3-minimal build-essential python3-setuptools
  ```

- ##### CentOS and other RPM Distributions:

  ```sh
  $ dnf groupinstall "Development Tools"
  $ dnf install python3
  ```

#### Setup

Download the Easy Install script and execute it:

```sh
$ wget https://raw.githubusercontent.com/frappe/bench/develop/install.py
$ python3 install.py --production
```

The script should then prompt you for the MySQL root password and an Administrator password for the Frappe/ERPNext instance, which will then be saved under `$HOME/passwords.txt` of the user used to setup the instance. This script will then install the required stack, setup bench and a default ERPNext instance.

When the setup is complete, you will be able to access the system at `http://<your-server-ip>`, wherein you can use the administrator password to login.

#### Troubleshooting

In case the setup fails, the log file is saved under `/tmp/logs/install_bench.log`. You may then:

- Create an Issue in this repository with the log file attached.
- Search for an existing issue or post the log file on the [Frappe/ERPNext Discuss Forum](https://discuss.erpnext.com/c/bench) with the tag `installation_problem` under "Install/Update" category.

For more information and advanced setup instructions, check out the [Easy Install Documentation](https://github.com/frappe/bench/blob/develop/docs/easy_install.md).


### Manual Installation

Some might want to manually setup a bench instance locally for development. To quickly get started on installing bench the hard way, you can follow the guide on [Installing Bench and the Frappe Framework](https://frappe.io/docs/user/en/installation).

You'll have to set up the system dependencies required for setting up a Frappe Environment. Checkout [docs/installation](https://github.com/frappe/bench/blob/develop/docs/installation.md) for more information on this. If you've already set up, install bench via pip:


```sh
$ pip install frappe-bench
```

For more extensive distribution-dependent documentation, check out the following guides:

- [Hitchhiker's Guide to Installing Frappe on Linux](https://github.com/frappe/frappe/wiki/The-Hitchhiker%27s-Guide-to-Installing-Frappe-on-Linux)
- [Hitchhiker's Guide to Installing Frappe on MacOS](https://github.com/frappe/bench/wiki/Setting-up-a-Mac-for-Frappe-ERPNext-Development)

## Contributing

- [Frappe Docker Images](CONTRIBUTING.md)
- [Frappe Framework](https://github.com/frappe/frappe#contributing)
- [ERPNext](https://github.com/frappe/erpnext#contributing)
- [frappe/bench](https://github.com/frappe/bench)
