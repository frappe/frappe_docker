[![Build Stable](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_stable.yml)
[![Build Develop](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml/badge.svg)](https://github.com/frappe/frappe_docker/actions/workflows/build_develop.yml)

# Frappe Docker

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

### Option 2: Local Development Setup

1. **Clone the repository:**

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

2. **Start the containers:**

```bash
docker compose -f pwd.yml up -d
```

3. **Wait for initialization** (approximately 5 minutes)

```bash
# Monitor the setup progress
docker compose -f pwd.yml logs -f create-site
```

4. **Access ERPNext:**

- URL: `http://localhost:8080`
- Username: `Administrator`
- Password: `admin`

### Option 3: Production Setup

1. **Clone and configure:**

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
cp example.env .env
# Edit .env file with your configuration
```

2. **Deploy with production settings:**

```bash
docker compose up -d
```

### ARM64 Architecture Support

For ARM64 systems (Apple Silicon, Raspberry Pi):

```bash
# Build ARM64 images
docker buildx bake --no-cache --set "*.platform=linux/arm64"

# Modify pwd.yml to add platform: linux/arm64 to all services
# Then deploy
docker compose -f pwd.yml up -d
```

## Bench Wrapper Script

To simplify working with bench commands, we provide a convenient wrapper script `bench.sh` that eliminates the need to type `docker compose exec backend bench` repeatedly.

### Setup

```bash
# Make the script executable (one-time setup)
chmod +x bench.sh
```

### Usage

The script automatically detects which compose file you're using and provides a simpler interface:

```bash
# Instead of: docker compose exec backend bench new-site mysite.local
./bench.sh new-site mysite.local

# Instead of: docker compose exec backend bench --site mysite.local migrate
./bench.sh --site mysite.local migrate

# With specific project name
./bench.sh -p erpnext-prod --site production.local backup

# Get help
./bench.sh --help
```

### Features

- **Auto-detection**: Automatically finds and uses the correct compose file (pwd.yml or compose.yaml)
- **Project support**: Use `-p` flag for specific docker-compose projects
- **Full compatibility**: Supports all bench commands and arguments
- **Error handling**: Checks if containers are running before executing commands
- **Help system**: Built-in help with common command examples

## Deployment Options

### Development Environment

Perfect for developers working on Frappe apps:

```bash
# Setup development environment with VSCode integration
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode

# Open in VSCode with Dev Containers extension
code .
# Then: "Reopen in Container"
```

**Features:**

- Hot-reload support
- Debugging capabilities
- Pre-configured VSCode settings
- Multiple Python/Node versions

### Production Environment

For production deployments:

```bash
# Using standard compose file
docker compose up -d

# With external database/Redis
# Configure DB_HOST, REDIS_CACHE, REDIS_QUEUE in .env
docker compose up -d
```

**Features:**

- Auto-restart on failure
- Health checks
- Log rotation
- Backup capabilities

### Single Server Setup

Simplified setup for single server deployments:

```bash
docker compose -f pwd.yml up -d
```

This creates a complete ERPNext instance with all required services.

## Architecture

The Frappe Docker setup consists of multiple interconnected services:

### Core Services

| Service         | Purpose                     | Port |
| --------------- | --------------------------- | ---- |
| **backend**     | Gunicorn application server | 8000 |
| **frontend**    | Nginx reverse proxy         | 8080 |
| **websocket**   | Socket.io real-time server  | 9000 |
| **scheduler**   | Background job scheduler    | -    |
| **queue-short** | Short-running job worker    | -    |
| **queue-long**  | Long-running job worker     | -    |

### Supporting Services

| Service         | Purpose                     | Default      |
| --------------- | --------------------------- | ------------ |
| **db**          | MariaDB/PostgreSQL database | MariaDB 10.6 |
| **redis-cache** | Redis cache server          | Redis 6.2    |
| **redis-queue** | Redis queue server          | Redis 6.2    |

### Service Flow

```
User Request → Nginx (frontend) → Gunicorn (backend) → Database
                ↓                      ↓
            WebSocket              Redis Cache
                                      ↓
                                  Job Queues → Workers
```

## Common Tasks

### Using the Bench Wrapper Script

For convenience, we provide a `bench.sh` wrapper script that simplifies running bench commands from your host machine.

```bash
# Make the script executable (first time only)
chmod +x bench.sh

# Create a new site
./bench.sh new-site mysite.local --admin-password=admin --install-app erpnext

# Run migrations
./bench.sh --site mysite.local migrate

# Backup a site
./bench.sh --site mysite.local backup

# Get help
./bench.sh --help
```

The script automatically detects which compose file you're using and handles the docker compose execution for you.

### Site Management

#### Create a new site

Using wrapper script:

```bash
./bench.sh new-site mysite.local \
  --mariadb-user-host-login-scope=% \
  --db-root-password=admin \
  --admin-password=admin \
  --install-app erpnext
```

Or directly with docker compose:

```bash
docker compose exec backend bench new-site mysite.local \
  --mariadb-user-host-login-scope=% \
  --db-root-password=admin \
  --admin-password=admin \
  --install-app erpnext
```

#### List all sites

Using wrapper script:

```bash
./bench.sh --site all list-apps
```

Or directly:

```bash
docker compose exec backend bench --site all list-apps
```

#### Migrate a site

Using wrapper script:

```bash
./bench.sh --site mysite.local migrate
```

Or directly:

```bash
docker compose exec backend bench --site mysite.local migrate
```

#### Backup a site

Using wrapper script:

```bash
./bench.sh --site mysite.local backup
```

Or directly:

```bash
docker compose exec backend bench --site mysite.local backup
```

### App Management

#### Install an app

Using wrapper script:

```bash
# Get the app
./bench.sh get-app https://github.com/frappe/app_name

# Install on site
./bench.sh --site mysite.local install-app app_name
```

Or directly:

```bash
# Get the app
docker compose exec backend bench get-app https://github.com/frappe/app_name

# Install on site
docker compose exec backend bench --site mysite.local install-app app_name
```

#### Update apps

Using wrapper script:

```bash
./bench.sh update --pull --apps
```

Or directly:

```bash
docker compose exec backend bench update --pull --apps
```

### Database Operations

#### Access MariaDB console

```bash
docker compose exec db mysql -uroot -padmin
```

#### Import database

Using wrapper script:

```bash
./bench.sh --site mysite.local --force restore path/to/backup.sql.gz
```

Or directly:

```bash
docker compose exec backend bench --site mysite.local \
  --force restore path/to/backup.sql.gz
```

### Monitoring & Logs

#### View all logs

```bash
docker compose logs -f
```

#### View specific service logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

#### Check service health

```bash
docker compose ps
docker compose exec backend healthcheck.sh
```

### Security & SSL

#### Setup Let's Encrypt SSL

```bash
# Configure in .env
LETSENCRYPT_EMAIL=your@email.com
SITES=`yourdomain.com`

# Deploy with Traefik
docker compose -f compose.yaml -f overrides/compose.https.yaml up -d
```

## Configuration

### Environment Variables

Create a `.env` file from the example:

```bash
cp example.env .env
```

Key configuration options:

| Variable                  | Description               | Default    |
| ------------------------- | ------------------------- | ---------- |
| `ERPNEXT_VERSION`         | ERPNext version to deploy | `v15.69.2` |
| `DB_PASSWORD`             | Database root password    | `123`      |
| `DB_HOST`                 | External database host    | -          |
| `REDIS_CACHE`             | External Redis cache URL  | -          |
| `REDIS_QUEUE`             | External Redis queue URL  | -          |
| `HTTP_PUBLISH_PORT`       | HTTP port                 | `8080`     |
| `FRAPPE_SITE_NAME_HEADER` | Site resolution header    | `$$host`   |

### Custom Apps Configuration

To include custom apps, create `apps.json`:

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/yourusername/custom-app",
    "branch": "main"
  }
]
```

Build custom image:

```bash
export APPS_JSON_BASE64=$(base64 -i apps.json)
docker buildx bake -f docker-bake.hcl custom
```

### Multi-tenancy Setup

For hosting multiple sites on different ports:

```yaml
# compose.override.yml
services:
  frontend:
    ports:
      - "8081:8080" # Site 1
      - "8082:8080" # Site 2
```

## Advanced Features

### Backup Automation

Setup automated backups to S3:

```bash
# Create backup script
docker compose exec backend push_backup.py \
  --site-name mysite.local \
  --bucket my-bucket \
  --region-name us-east-1 \
  --endpoint-url https://s3.amazonaws.com \
  --aws-access-key-id KEY \
  --aws-secret-access-key SECRET
```

### Custom Build Arguments

Build with specific versions:

```bash
docker buildx bake \
  --set "*.args.FRAPPE_VERSION=v15.0.0" \
  --set "*.args.ERPNEXT_VERSION=v15.0.0" \
  --set "*.args.PYTHON_VERSION=3.11.6" \
  --set "*.args.NODE_VERSION=18.18.2"
```

### Development with Bench

Inside development container:

```bash
# Create new bench
bench init --skip-redis-config-generation frappe-bench
cd frappe-bench

# Start bench
bench start

# Create new app
bench new-app my_custom_app

# Install app
bench --site mysite.local install-app my_custom_app
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs backend

# Verify configuration
docker compose config

# Restart services
docker compose restart
```

### Site not accessible

```bash
# Check site configuration (using wrapper script)
./bench.sh --site mysite.local show-config

# Or directly
docker compose exec backend bench --site mysite.local show-config

# Verify nginx is running
docker compose exec frontend nginx -t
```

### Database connection issues

```bash
# Test database connection (using wrapper script)
./bench.sh --site mysite.local mariadb

# Or directly
docker compose exec backend bench --site mysite.local mariadb

# Check database logs
docker compose logs db
```

### Permission errors

```bash
# Fix permissions
docker compose exec backend chown -R frappe:frappe /home/frappe/frappe-bench
```

### Reset admin password

```bash
# Using wrapper script
./bench.sh --site mysite.local set-admin-password newpassword

# Or directly
docker compose exec backend bench --site mysite.local set-admin-password newpassword
```

## Documentation

### Essential Guides

- [Frequently Asked Questions](https://github.com/frappe/frappe_docker/wiki/Frequently-Asked-Questions)
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
