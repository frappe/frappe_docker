[![Build Stable](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml)
[![Build Develop](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml)

# Frappe Docker

Everything about [Frappe](https://github.com/frappe/frappe) and [ERPNext](https://github.com/frappe/erpnext) in containers.

Production-ready containerized setup for [Frappe](https://github.com/frappe/frappe) and [ERPNext](https://github.com/frappe/erpnext) applications. This repository provides Docker images and deployment configurations for running Frappe/ERPNext in both development and production environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Architecture](#architecture)
- [Common Tasks](#common-tasks)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

Frappe Docker provides a complete containerized solution for deploying the Frappe framework and ERPNext ERP system. It includes:

- **Pre-built Docker images** for Frappe and ERPNext (versions 13, 14, and 15)
- **Multiple deployment configurations** (development, production, single-server)
- **Docker Compose setups** for easy orchestration
- **Support for custom apps** and extensions
- **Built-in backup and restore capabilities**
- **TLS/SSL support** via Traefik reverse proxy
- **Multi-tenancy support** with port-based routing
- **Development containers** with VSCode integration

## Prerequisites

Before you begin, ensure you have:

- **Docker** (v20.10+) - [Installation Guide](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+) - [Installation Guide](https://docs.docker.com/compose/install/)
- **Git** - [Installation Guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- **System Requirements:**
  - Minimum 4GB RAM (8GB recommended for production)
  - 20GB free disk space
  - Linux, macOS, or Windows with WSL2

## Quick Start

Choose one of the following options to get started quickly:

### Option 1: Try in Browser (Play With Docker)

Click below to instantly spin up a Frappe/ERPNext instance in your browser:

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

### [Production](#production)

- [List of containers](docs/list-of-containers.md)
- [Single Compose Setup](docs/single-compose-setup.md)
- [Environment Variables](docs/environment-variables.md)
- [Site Operations](docs/site-operations.md)
- [Custom Apps](docs/custom-apps.md)
- [Development Guide](docs/development.md)
- [Troubleshooting](docs/troubleshoot.md)

### Production Deployment

- [Single Server Example](docs/single-server-example.md)
- [Setup Options](docs/setup-options.md)
- [Backup and Push Cron Job](docs/backup-and-push-cronjob.md)
- [Port Based Multi Tenancy](docs/port-based-multi-tenancy.md)
- [TLS for local deployment](docs/tls-for-local-deployment.md)
- [Migrate from multi-image setup](docs/migrate-from-multi-image-setup.md)

### Development

- [Development using containers](docs/development.md)
- [Bench Console and VSCode Debugger](docs/bench-console-and-vscode-debugger.md)
- [Connect to localhost services](docs/connect-to-localhost-services-from-containers-for-local-app-development.md)

### Customization

- [Custom Apps](docs/custom-apps.md)
- [Custom Apps with Podman](docs/custom-apps-podman.md)
- [Build Version 10 Images](docs/build-version-10-images.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Related Projects

- [Frappe Framework](https://github.com/frappe/frappe) - Full-stack web framework
- [ERPNext](https://github.com/frappe/erpnext) - Open source ERP
- [Frappe Bench](https://github.com/frappe/bench) - CLI tool for Frappe deployments

## Support

- [Official Documentation](https://frappeframework.com/docs)
- [Community Forum](https://discuss.frappe.io/)
- [Report Issues](https://github.com/frappe/frappe_docker/issues)
- [Commercial Support](https://frappe.io/support)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
