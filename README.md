# Frappe Docker

[![Build Stable](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml)
[![Build Develop](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml)

Docker images and orchestration for Frappe applications.

## What is this?

This repository handles the containerization of the Frappe stack, including the application server, database, Redis, and supporting services. It provides quick disposable demo setups, a development environment, production-ready Docker images and compose configurations for deploying Frappe applications including ERPNext.

## Repository Structure

```
frappe_docker/
├── docs/                 # Complete documentation
├── overrides/            # Docker Compose configurations for different scenarios
├── compose.yaml          # Base Compose File for production setups
├── pwd.yml               # Single Compose File for quick disposable demo
├── images/               # Dockerfiles for building Frappe images
├── development/          # Development environment configurations
├── devcontainer-example/ # VS Code devcontainer setup
└── resources/            # Helper scripts and configuration templates
```

> This section describes the structure of **this repository**, not the Frappe framework itself.

### Key Components

- `docs/` - Canonical documentation for all deployment and operational workflows
- `overrides/` - Opinionated Compose overrides for common deployment patterns
- `compose.yaml` - Base compose file for production setups (production)
- `pwd.yml` - Disposable demo environment (non-production)

## Documentation

**The official documentation for `frappe_docker` is maintained in the `docs/` folder in this repository.**

**New to Frappe Docker?** Read the [Getting Started Guide](docs/getting-started.md) for a comprehensive overview of repository structure, development workflow, custom apps, Docker concepts, and quick start examples.

If you are already familiar with Frappe, you can jump right into the [different deployment methods](docs/01-getting-started/01-choosing-a-deployment-method.md) and select the one best suited to your use case.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose v2](https://docs.docker.com/compose/)
- [git](https://docs.github.com/en/get-started/getting-started-with-git/set-up-git)

> For Docker basics and best practices refer to Docker's [documentation](http://docs.docker.com)

## Demo setup

The fastest way to try Frappe is to play in an already set up sandbox, in your browser, click the button below:

<a href="https://labs.play-with-docker.com/?stack=https://raw.githubusercontent.com/frappe/frappe_docker/main/pwd.yml">
  <img src="https://raw.githubusercontent.com/play-with-docker/stacks/master/assets/images/button.png" alt="Try in PWD"/>
</a>

### Try on your environment

> **⚠️ Disposable demo only**
>
> **This setup is intended for quick evaluation. Expect to throw the environment away.** You will not be able to install custom apps to this setup. For production deployments, custom configurations, and detailed explanations, see the full documentation.

First clone the repo:

```sh
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

Then run:

```sh
docker compose -f pwd.yml up -d
```

Wait for a couple of minutes for ERPNext site to be created or check `create-site` container logs before opening browser on port `8080`. (username: `Administrator`, password: `admin`)

## Documentation Links

### [Getting Started Guide](docs/getting-started.md)

### [Frequently Asked Questions](https://github.com/frappe/frappe_docker/wiki/Frequently-Asked-Questions)

### [Getting Started](#getting-started)

### [Deployment Methods](docs/01-getting-started/01-choosing-a-deployment-method.md)

### [ARM64](docs/01-getting-started/03-arm64.md)

### [Container Setup Overview](docs/02-setup/01-overview.md)

### [Development](docs/05-development/01-development.md)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

This repository is only for container related stuff. You also might want to contribute to:

## Resources

- [Frappe framework](https://github.com/frappe/frappe),
- [ERPNext](https://github.com/frappe/erpnext),
- [Frappe Bench](https://github.com/frappe/bench).

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE) for details.
