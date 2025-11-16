# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository provides Docker containerization for Frappe Framework and ERPNext. It supports both development environments and production deployments through multiple compose configurations and image types.

## Repository Architecture

### Multi-Image Strategy

There are **four distinct Dockerfile types** in `images/`:

- **bench** (`images/bench/Dockerfile`): CLI-only setup for development/debugging
- **custom** (`images/custom/Containerfile`): Production-ready, built from Python base, uses `apps.json` for app installation
- **layered** (`images/layered/Containerfile`): Same as custom but based on prebuilt Docker Hub images for faster builds
- **production** (`images/production/Containerfile`): Quick-start image with only Frappe + ERPNext (not customizable)

**Key principle**: `custom` and `layered` are for real deployments; `production` is for exploration only.

### Multi-Service Architecture

The base `compose.yaml` defines these core services:

- **configurator**: Runs once on startup to configure `common_site_config.json` with database and Redis connection details, then exits
- **backend**: Werkzeug development server (Python) serving dynamic content
- **frontend**: Nginx reverse proxy serving static assets and routing requests
- **websocket**: Node.js Socket.IO server for real-time features
- **queue-short/queue-long**: Python RQ workers for background job processing
- **scheduler**: Python service running scheduled tasks

**Additional services** come from compose overrides in `overrides/`:
- `compose.mariadb.yaml` / `compose.postgres.yaml`: Database services
- `compose.redis.yaml`: Redis cache and queue services
- `compose.proxy.yaml`: Traefik reverse proxy for multi-site hosting
- `compose.https.yaml`: SSL/TLS certificate management
- `compose.noproxy.yaml`: Direct port exposure (no proxy) for development

### Compose File Composition Pattern

The architecture uses Docker Compose overrides to build complete environments:

```bash
docker compose \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > compose.custom.yaml
```

This pattern allows mixing and matching services based on deployment needs.

## Common Development Commands

### Quick Testing Setup (pwd.yml)

For rapid evaluation without local setup:

```bash
# Start all services (uses frappe-custom:v15 image)
docker compose -f pwd.yml up -d

# Monitor site creation (takes ~5 minutes)
docker compose -f pwd.yml logs -f create-site

# Access at http://localhost:8080
# Login: Administrator / admin
```

The `pwd.yml` file is a self-contained configuration that includes all services (MariaDB, Redis, workers, etc.) and automatically creates a site named "frontend".

### Development Environment Setup

Full development with hot-reload:

```bash
# 1. Copy devcontainer configuration
cp -R devcontainer-example .devcontainer

# 2. Open in VSCode with Dev Containers extension
# VSCode will detect .devcontainer and prompt to reopen in container

# 3. Inside container, run automated installer
cd /workspace/development
python installer.py

# Installer arguments:
# -j, --apps-json: Path to apps.json (default: apps-example.json)
# -b, --bench-name: Bench directory name (default: frappe-bench)
# -s, --site-name: Site name, must end with .localhost (default: development.localhost)
# -t, --frappe-branch: Frappe branch (default: version-15)
# -d, --db-type: Database type (mariadb or postgres)
# -a, --admin-password: Admin password (default: admin)
```

Development files are located in `development/frappe-bench/` (git-ignored directory).

### Bench Commands (Inside Container)

```bash
# Site management
bench new-site --mariadb-user-host-login-scope=% <site-name>
bench list-sites
bench --site <site-name> migrate

# App management
bench get-app --branch <branch> <git-url>
bench --site <site-name> install-app <app-name>
bench list-apps

# Development
bench start  # Start dev server with hot-reload
bench build  # Build frontend assets
bench build --app <app-name>  # Build specific app

# Database
bench mariadb  # Open MariaDB console
bench --site <site-name> backup --with-files

# Debugging
bench --site <site-name> console  # Python REPL with Frappe context
```

## Building Custom Images

### Creating apps.json

Define custom apps to install in `apps.json`:

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/frappe/hrms",
    "branch": "version-15"
  }
]
```

### Build Process

```bash
# 1. Encode apps.json
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# 2. Build image (example using layered)
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=custom:15 \
  --file=images/layered/Containerfile .

# Or use docker-bake.hcl for multi-arch builds
docker buildx bake --no-cache
```

**Important build args**:
- `FRAPPE_PATH`: Frappe framework repo URL
- `FRAPPE_BRANCH`: Frappe framework branch
- `APPS_JSON_BASE64`: Base64-encoded apps.json
- `PYTHON_VERSION`: Python version (default: 3.11.6)
- `NODE_VERSION`: Node.js version (default: 20.19.2)

## Testing and CI

### Linting

```bash
# Install pre-commit
pip install pre-commit
# or
brew install pre-commit

# Setup hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Integration Tests

```bash
# Setup test environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt

# Run tests
pytest
```

## Site Operations

### Creating a New Site

```bash
# Basic site creation
docker compose exec backend \
  bench new-site --mariadb-user-host-login-scope=% \
  --db-root-password <db-password> \
  --admin-password <admin-password> <site-name>

# For PostgreSQL
docker compose exec backend bench set-config -g root_login postgres
docker compose exec backend bench set-config -g root_password <password>
docker compose exec backend \
  bench new-site --db-type postgres \
  --admin-password <admin-password> <site-name>
```

**Note**: The `--mariadb-user-host-login-scope=%` option is critical for Docker networking - it allows database users to connect from any host (%).

### Accessing Container Files

```bash
# Enter backend container
docker compose exec backend bash

# Key directories inside container:
# /home/frappe/frappe-bench/apps/     - All Frappe applications
# /home/frappe/frappe-bench/sites/    - Site data and configuration
# /home/frappe/frappe-bench/logs/     - Application logs

# Copy files from container to host
docker compose cp backend:/home/frappe/frappe-bench/apps/my_app ./local-apps/
```

## Environment Variables

The main environment variables (from `example.env`):

- `ERPNEXT_VERSION`: Version tag for ERPNext image
- `DB_HOST`, `DB_PORT`: External database connection (if not using compose.mariadb.yaml)
- `REDIS_CACHE`, `REDIS_QUEUE`: External Redis connection (if not using compose.redis.yaml)
- `FRAPPE_SITE_NAME_HEADER`: Override site resolution (default: `$$host`)
- `HTTP_PUBLISH_PORT`: HTTP port to publish (default: 8080)
- `LETSENCRYPT_EMAIL`: Email for Let's Encrypt certificates
- `SITES`: Comma-separated list of sites for SSL certificates

See `docs/container-setup/env-variables.md` for complete reference.

## Key Implementation Details

### Service Startup Dependencies

The `configurator` service MUST complete successfully before other services start. It writes database and Redis connection details to `sites/common_site_config.json`. The compose file uses:

```yaml
x-depends-on-configurator: &depends_on_configurator
  depends_on:
    configurator:
      condition: service_completed_successfully
```

### Nginx Configuration

The `frontend` service uses `nginx-entrypoint.sh` which dynamically generates Nginx configuration from `resources/nginx-template.conf` using environment variables like `BACKEND`, `SOCKETIO`, `FRAPPE_SITE_NAME_HEADER`.

### Volume Mounts

- **sites**: Shared across all services, contains site data and configuration
- **logs**: Application logs (optional, for debugging)

For development, bind mount `./development/frappe-bench` to `/workspace/development` in the container.

## Platform-Specific Notes

### ARM64 / Apple Silicon

```bash
# Build multi-arch images
docker buildx bake --no-cache --set "*.platform=linux/arm64"

# For pwd.yml on ARM64
# 1. Add platform: linux/arm64 to all services
# 2. Replace version tags with :latest
```

Use `:cached` or `:delegated` volume flags on macOS for better performance.

## Project Structure Reference

```
frappe_docker/
├── compose.yaml              # Base compose file (core services)
├── pwd.yml                   # Self-contained quick-start config
├── docker-bake.hcl           # Buildx bake configuration
├── example.env               # Environment variables template
├── images/                   # Dockerfile definitions
│   ├── bench/               # CLI-only image
│   ├── custom/              # Production image (apps.json)
│   ├── layered/             # Fast-build production image
│   └── production/          # Quick-start image (Frappe + ERPNext only)
├── overrides/               # Compose file extensions
│   ├── compose.mariadb.yaml
│   ├── compose.redis.yaml
│   ├── compose.proxy.yaml
│   └── compose.https.yaml
├── resources/               # Runtime templates
│   ├── nginx-entrypoint.sh
│   └── nginx-template.conf
├── development/             # Dev environment (git-ignored)
│   └── installer.py        # Automated setup script
├── devcontainer-example/    # VSCode devcontainer template
└── docs/                    # Documentation
```

## Version Compatibility

- **Frappe v14**: Python 3.10.13, Node v16
- **Frappe v15**: Python 3.11.6, Node v20 (default)
- **Frappe v13**: Python 3.9.17, Node v14

When working with different versions, set `PYENV_VERSION` and use `nvm` to switch Node versions inside the container.

## Important Development Notes

1. **Site names must end with `.localhost`** for local development
2. **Default MariaDB root password is `123`** in development
3. **Default admin password is `admin`** when using installer.py
4. **Wait for configurator to exit** before creating sites or running migrations
5. **The `development/` directory is git-ignored** - all local development happens here
6. **Use `--mariadb-user-host-login-scope=%`** when creating sites in Docker to enable proper networking
