[![Build Stable](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml)
[![Build Develop](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml)

Everything about [Frappe](https://github.com/frappe/frappe) and [ERPNext](https://github.com/frappe/erpnext) in containers.

# Getting Started

To get started you need [Docker](https://docs.docker.com/get-docker/), [docker-compose](https://docs.docker.com/compose/), and [git](https://docs.github.com/en/get-started/getting-started-with-git/set-up-git) setup on your machine. For Docker basics and best practices refer to Docker's [documentation](http://docs.docker.com).

Once completed, chose one of the following two sections for next steps.

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

### [Getting Started](#getting-started)

- [Quick Start (Linux/Mac)](docs/01-getting-started/01-quick-start-linux-mac.md)
- [Single Compose Setup](docs/01-getting-started/02-single-compose-setup.md)

### [Setup](#setup)

- [Container Setup Overview](docs/02-setup/01-overview.md)
- [Build Setup](docs/02-setup/02-build-setup.md)
- [Start Setup](docs/02-setup/03-start-setup.md)
- [Environment Variables](docs/02-setup/04-env-variables.md)
- [Compose Overrides](docs/02-setup/05-overrides.md)
- [Setup Examples](docs/02-setup/06-setup-examples.md)
- [Single Server Example](docs/02-setup/07-single-server-example.md)

### [Production](#production)

- [TLS/SSL Setup](docs/03-production/01-tls-ssl-setup.md)
- [Backup Strategy](docs/03-production/02-backup-strategy.md)
- [Multi-Tenancy](docs/03-production/03-multi-tenancy.md)

### [Operations](#operations)

- [Site Operations](docs/04-operations/01-site-operations.md)

### [Development](#development)

- [Development Guide](docs/05-development/01-development.md)
- [Debugging](docs/05-development/02-debugging.md)
- [Local Services Connection](docs/05-development/03-local-services-connection.md)

### [Migration](#migration)

- [Migrate from Multi-Image Setup](docs/06-migration/01-migrate-from-multi-image-setup.md)

### [Troubleshooting](#troubleshooting)

- [Troubleshoot Guide](docs/07-troubleshooting/01-troubleshoot.md)
- [Windows Nginx Entrypoint Error](docs/07-troubleshooting/02-windows-nginx-entrypoint-error.md)

### [Reference](#reference)

- [Build Version 10 Images](docs/08-reference/01-build-version-10-images.md)

# Contributing

If you want to contribute to this repo refer to [CONTRIBUTING.md](CONTRIBUTING.md)

This repository is only for container related stuff. You also might want to contribute to:

- [Frappe framework](https://github.com/frappe/frappe#contributing),
- [ERPNext](https://github.com/frappe/erpnext#contributing),
- [Frappe Bench](https://github.com/frappe/bench).
