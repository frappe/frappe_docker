[![Build Stable](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml)
[![Build Develop](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml)
[![Build Dokploy](https://github.com/ubden/frappe_docker/actions/workflows/build-dokploy.yml/badge.svg)](https://github.com/ubden/frappe_docker/actions/workflows/build-dokploy.yml)
[![GitHub release](https://img.shields.io/github/v/release/ubden/frappe_docker?label=dokploy)](https://github.com/ubden/frappe_docker/releases)
[![Docker Image](https://img.shields.io/badge/docker-erpnext--complete-blue)](https://github.com/ubden/frappe_docker/pkgs/container/frappe_docker%2Ferpnext-complete)

Everything about [Frappe](https://github.com/frappe/frappe) and [ERPNext](https://github.com/frappe/erpnext) in containers.

# Getting Started

To get started you need [Docker](https://docs.docker.com/get-docker/), [docker-compose](https://docs.docker.com/compose/), and [git](https://docs.github.com/en/get-started/getting-started-with-git/set-up-git) setup on your machine. For Docker basics and best practices refer to Docker's [documentation](http://docs.docker.com).

Once completed, chose one of the following two sections for next steps.

### 🚀 Deploy to Dokploy (Production Ready)

**NEW!** Deploy ERPNext with 9 pre-installed apps (CRM, LMS, Builder, Print Designer, Payments, Wiki, Twilio Integration, and ERPNext Shipping) to Dokploy in minutes!

```bash
Repository: https://github.com/ubden/frappe_docker
Branch: main
Compose Path: dokploy/docker-compose.yml
```

📚 **Quick Start Guide**: [dokploy/QUICKSTART.md](dokploy/QUICKSTART.md)  
📖 **Full Documentation**: [dokploy/README.md](dokploy/README.md)

**Features:**
- ✅ One-click deployment with all apps pre-installed
- ✅ Production-optimized configuration
- ✅ Automatic SSL/TLS with Let's Encrypt
- ✅ Built-in health checks and monitoring
- ✅ Easy backup and restore
- ✅ Horizontal scaling ready

### Try in Play With Docker

To play in an already set up sandbox, in your browser, click the button below:

<a href="https://labs.play-with-docker.com/?stack=https://raw.githubusercontent.com/frappe/frappe_docker/main/pwd.yml">
  <img src="https://raw.githubusercontent.com/play-with-docker/stacks/master/assets/images/button.png" alt="Try in PWD"/>
</a>

### Try on your Dev environment

First clone the repo:

```sh
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

Then run: `docker compose -f pwd.yml up -d`

### To run on ARM64 architecture follow this instructions

After you clone the repo and `cd frappe_docker`, run this command to build multi-architecture images specifically for ARM64.

`docker buildx bake --no-cache --set "*.platform=linux/arm64"`

and then

- add `platform: linux/arm64` to all services in the `pwd.yml`
- replace the current specified versions of erpnext image on `pwd.yml` with `:latest`

Then run: `docker compose -f pwd.yml up -d`

## Final steps

Wait for 5 minutes for ERPNext site to be created or check `create-site` container logs before opening browser on port 8080. (username: `Administrator`, password: `admin`)

If you ran in a Dev Docker environment, to view container logs: `docker compose -f pwd.yml logs -f create-site`. Don't worry about some of the initial error messages, some services take a while to become ready, and then they go away.

# Documentation

### [Frequently Asked Questions](https://github.com/frappe/frappe_docker/wiki/Frequently-Asked-Questions)

### [Dokploy Deployment](#dokploy) 🚀

Complete ERPNext solution with 9 pre-installed apps, optimized for Dokploy:

- [Quick Start (5 minutes)](dokploy/QUICKSTART.md) ⚡
- [Deployment Guide](dokploy/DEPLOYMENT.md) 📖
- [Package Summary](dokploy/SUMMARY.md) 📋
- [Changelog](dokploy/CHANGELOG.md) 📝

**Included Apps**: ERPNext, CRM, LMS, Builder, Print Designer, Payments, Wiki, Twilio Integration, ERPNext Shipping

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
- [TLS for local deployment](docs/tls-for-local-deployment.md)

### [Custom Images](#custom-images)

- [Custom Apps](docs/custom-apps.md)
- [Custom Apps with podman](docs/custom-apps-podman.md)
- [Build Version 10 Images](docs/build-version-10-images.md)

### [Development](#development)

- [Development using containers](docs/development.md)
- [Bench Console and VSCode Debugger](docs/bench-console-and-vscode-debugger.md)
- [Connect to localhost services](docs/connect-to-localhost-services-from-containers-for-local-app-development.md)

### [Troubleshoot](docs/troubleshoot.md)

# Contributing

If you want to contribute to this repo refer to [CONTRIBUTING.md](CONTRIBUTING.md)

This repository is only for container related stuff. You also might want to contribute to:

- [Frappe framework](https://github.com/frappe/frappe#contributing),
- [ERPNext](https://github.com/frappe/erpnext#contributing),
- [Frappe Bench](https://github.com/frappe/bench).
