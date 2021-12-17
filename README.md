[![Build Stable](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml)
[![Build Develop](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml)

Everything about [Frappe](https://github.com/frappe/frappe) and [ERPNext](https://github.com/frappe/erpnext) in containers.

# Getting Started

To get started, you need Docker, docker-compose and git setup on your machine. For Docker basics and best practices. Refer Docker [documentation](http://docs.docker.com).
After that, clone this repo:

```sh
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

# Development

We have baseline for developing in VSCode devcontainer with [frappe/bench](https://github.com/frappe/bench). [Start development](development).

# Production

We provide simple and intuitive production setup with prebuilt Frappe and ERPNext images and compose files. To learn more about those, [read the docs](docs/images-and-compose-files.md).

Also, there's docs to help with deployment:

- [on single server](docs/single-server.md),
- in cluster:
  - [Docker Swarm](docs/docker-swarm.md),
  - [Kubernetes (frappe/helm)](https://helm.erpnext.com),
- [site operations](docs/site-operations.md).

# Custom app

Learn how to containerize your custom Frappe app in [this guide](custom_app/README.md).

# Contributing

If you want to contribute to this repo refer to [CONTRIBUTING.md](CONTRIBUTING.md)

This repository is only for Docker related stuff. You also might want to contribute to:

- [Frappe framework](https://github.com/frappe/frappe#contributing),
- [ERPNext](https://github.com/frappe/erpnext#contributing),
- or [Frappe Bench](https://github.com/frappe/bench).
