---
title: Introduction
---

# Introduction to Frappe Docker

This is the documentation for the Frappe Docker repository, which contains all the information on how to develop, deploy and share Frappe app, using Docker containers.

## Repository Architecture

Frappe Docker provides a comprehensive containerized environment for developing and deploying Frappe/ERPNext applications. It uses a **multi-service architecture** that handles everything from web serving to background job processing.

### Core Services

The base compose file includes these essential services:

- **configurator** - Initialization service that configures database and Redis connections; runs on startup and exits
- **backend** - Werkzeug development server for dynamic content processing
- **frontend** - Nginx reverse proxy that serves static assets and routes requests
- **websocket** - Node.js server running Socket.IO for real-time communications
- **queue-short/long** - Python workers using RQ (Redis Queue) for asynchronous background job processing
- **scheduler** - Python service that runs scheduled tasks using the schedule library

Additional services are added through compose overrides:

- **db** - MariaDB or PostgreSQL database server (via `compose.mariadb.yaml` or `compose.postgres.yaml`)
- **redis-cache/queue** - Redis instances for caching and job queues (via `compose.redis.yaml`)

### How Services Work Together

```
User Request
    ↓
[frontend (Nginx)] → Static files served directly
    ↓
[backend (Werkzeug)] → Dynamic content processing
    ↓                    ↓
[db (MariaDB)]      [redis-cache]

Background Tasks:
[scheduler] → [redis-queue] → [queue-short/long workers]

Real-time:
[websocket (Socket.IO)] ←→ [redis-cache]
```

## Repository Structure

### `/` Root: Core Configuration Files

- **compose.yaml** - Main Docker Compose file defining all services
- **example.env** - Environment variables template (copy to `.env`)
- **pwd.yml** - "Play with Docker" - simplified single-file setup for quick testing
- **docker-bake.hcl** - Advanced Docker Buildx configuration for multi-architecture builds
- **docs/container-setup/env-variables.md** - Central reference for environment configuration logic and defaults

### `images/`: Docker Image Definitions

Four predefined Dockerfiles are available, each serving different use cases:

- **images/bench/** - Sets up only the Bench CLI for development or debugging; does not include runtime services
- **images/custom/** - Multi-purpose Python backend built from plain Python base image; installs apps from `apps.json`; suitable for **production** and testing; ideal when you need control over Python/Node versions
- **images/layered/** - Same final contents as `custom` but based on prebuilt images from Docker Hub; faster builds for production when using Frappe-managed dependency versions
- **images/production/** - Installs only Frappe and ERPNext (not customizable with `apps.json`); best for **quick starts or exploration**; for real deployments, use `custom` or `layered`

> **Note:** For detailed build arguments and advanced configuration options, see [Setup Overview](../02-setup/01-overview.md).

### `overrides/`: Compose File Extensions

Docker Compose "overrides" that extend the base compose.yaml for different scenarios:

- **compose.mariadb.yaml** - Adds MariaDB database service
- **compose.redis.yaml** - Adds Redis caching service
- **compose.proxy.yaml** - Adds Traefik reverse proxy for multi-site hosting (label-based routing)
- **compose.https.yaml** - Adds Traefik HTTPS + automatic certs (uses `SITES_RULE`)
- **compose.nginxproxy.yaml** - Adds nginx-proxy reverse proxy (HTTP, env-based `VIRTUAL_HOST`)
- **compose.nginxproxy-ssl.yaml** - Adds nginx-proxy + acme-companion (HTTPS, env-based `LETSENCRYPT_HOST`)

**Proxy choice:**

- Traefik is more flexible for advanced routing and multi-bench setups
- nginx-proxy is simpler for a single bench with host-based routing.

### `development/`: Dev Environment

- **development/installer.py** - Automated bench/site creation and configuration script
- Contains your local development files (git-ignored to prevent accidental commits)

### `resources/`: Runtime Templates

- **core/nginx/nginx-entrypoint.sh** - Dynamic Nginx configuration generator script
- **core/nginx/nginx-template.conf** - Nginx configuration template with variable substitution
