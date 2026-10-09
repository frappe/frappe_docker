---
title: Getting Started
---

# Getting Started with Frappe Docker

_A comprehensive guide for developers getting started with Frappe Docker, with comparisons to Django for teams familiar with that framework_

## Table of Contents

- [How to Use This Guide](#how-to-use-this-guide)
- [Understanding Frappe Docker Architecture](#understanding-frappe-docker-architecture)
- [Repository Structure](#repository-structure)
- [Custom Apps Explained](#custom-apps-explained)
- [Development Workflow](#development-workflow)
- [Platform Notes](#platform-notes)
- [File Locations and Access](#file-locations-and-access)
- [Docker Concepts: Bind Mounts](#docker-concepts-bind-mounts)
- [Fork Management Best Practices](#fork-management-best-practices)
- [Quick Start Examples](#quick-start-examples)
- [Framework Comparisons](#framework-comparisons)
  - [Frappe vs Django](13-explanation/06-framework-comparisons.md#frappe-vs-django-concepts)
- [Resources and References](#resources-and-references)

---

## How to Use This Guide

Walk through the sections sequentially if you're onboarding from scratch, or jump directly using the Table of Contents.

## Understanding Frappe Docker Architecture

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

### 📁 Core Configuration Files

> ⚠️ Before deploying, read
> **[Choosing a Deployment Method](01-getting-started/01-choosing-a-deployment-method.md)**
> to understand the differences between `pwd.yml`, development setup, the Easy Install script and the production setup.

- **compose.yaml** - Main Docker Compose file defining all services
- **example.env** - Environment variables template (copy to `.env`)
- **pwd.yml** - "Play with Docker" - simplified single-file setup for quick testing
- **docker-bake.hcl** - Advanced Docker Buildx configuration for multi-architecture builds
- **docs/container-setup/env-variables.md** - Central reference for environment configuration logic and defaults

### 📁 images/ - Docker Image Definitions

Four predefined Dockerfiles are available, each serving different use cases:

- **images/bench/** - Sets up only the Bench CLI for development or debugging; does not include runtime services
- **images/custom/** - Multi-purpose Python backend built from plain Python base image; installs apps from `apps.json`; suitable for **production** and testing; ideal when you need control over Python/Node versions
- **images/layered/** - Same final contents as `custom` but based on prebuilt images from Docker Hub; faster builds for production when using Frappe-managed dependency versions
- **images/production/** - Installs only Frappe and ERPNext (not customizable with `apps.json`); best for **quick starts or exploration**; for real deployments, use `custom` or `layered`

> **Note:** For detailed build arguments and advanced configuration options, see [docs/02-setup/01-overview.md](02-setup/01-overview.md).

### 📁 overrides/ - Compose File Extensions

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

### 📁 development/ - Dev Environment

- **development/installer.py** - Automated bench/site creation and configuration script
- Contains your local development files (git-ignored to prevent accidental commits)

### 📁 resources/ - Runtime Templates

- **core/nginx/nginx-entrypoint.sh** - Dynamic Nginx configuration generator script
- **core/nginx/nginx-template.conf** - Nginx configuration template with variable substitution

## Custom Apps Explained

### What Are Frappe Custom Apps?

Custom apps are self-contained, modular business applications that extend Frappe's functionality. They follow a convention-over-configuration approach where the framework provides most boilerplate automatically.

### Custom App Structure

```
my_custom_app/
├── hooks.py                    # App configuration and hooks into Frappe lifecycle
├── modules.txt                 # List of business modules in this app
├── my_custom_app/
│   ├── __init__.py
│   ├── config/
│   │   └── desktop.py          # Desktop workspace icons and shortcuts
│   ├── my_module/              # Business domain module (e.g., sales, inventory)
│   │   ├── doctype/           # Document Types (data models)
│   │   │   ├── customer/
│   │   │   │   ├── customer.py      # Python controller (business logic)
│   │   │   │   ├── customer.json    # Model definition (schema, validation)
│   │   │   │   └── customer.js      # Frontend logic (UI interactions)
│   │   └── page/              # Custom pages (dashboards, reports)
│   ├── public/               # Static assets (CSS, JS, images)
│   ├── templates/            # Jinja2 templates for web pages
│   └── www/                  # Web pages accessible via routes
└── requirements.txt          # Python package dependencies
```

### Built-in Features (Auto-generated)

Every Frappe app automatically includes:

- **REST API** - Automatic CRUD endpoints from DocType definitions
- **Permissions system** - Row-level and field-level access control
- **Audit trails** - Automatic version tracking and change history
- **Custom fields** - Runtime field additions without code changes
- **Workflows** - Configurable approval and state management
- **Reports** - Query builder and report designer
- **Print formats** - PDF generation with custom templates
- **Email integration** - Template-based email sending
- **File attachments** - Document attachment management

### Creating Custom Apps

```bash
# Enter the development container
docker exec -it <container_name> bash

# Create new app (interactive prompts will ask for details)
bench new-app my_custom_app

# Install app to a site
bench --site mysite.com install-app my_custom_app

# Create a new DocType (data model)
bench --site mysite.com console
>>> bench.new_doc("DocType", {...})
# Or use the web UI: Setup → Customize → DocType → New
```

## Development Workflow

### Quick Test Setup (pwd.yml)

Perfect for evaluating Frappe Docker without any local setup:

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
docker compose -f pwd.yml up -d

# Monitor site creation (takes ~5 minutes)
docker compose -f pwd.yml logs -f create-site

# Access once "create-site" container exits successfully
# Visit http://localhost:8080
# Login: Administrator / admin
```

### Full Development Setup

For active development with hot-reload and debugging:

1. **Copy devcontainer configuration:**

   ```bash
   cp -R devcontainer-example .devcontainer
   ```

2. **Open in VSCode with Dev Containers extension** (Remote - Containers)

   - VSCode will detect `.devcontainer` and prompt to reopen in container

3. **Run automated installer:**

   ```bash
   cd /workspace/development
   python installer.py
   # Follow interactive prompts for site name, apps to install, etc.
   ```

4. **Access development files:**
   ```
   development/frappe-bench/  # Your live development environment
   ```

### Development File Locations

```
development/
├── frappe-bench/           # Your actual Frappe installation
│   ├── apps/              # All installed Frappe applications
│   │   ├── frappe/        # Core framework (don't modify directly)
│   │   ├── erpnext/       # ERPNext application (if installed)
│   │   └── my_custom_app/ # Your custom apps (edit freely)
│   ├── sites/             # Multi-tenant sites
│   │   ├── development.localhost/     # Default dev site
│   │   │   ├── site_config.json      # Site-specific config
│   │   │   └── private/files/        # Uploaded files
│   │   └── common_site_config.json   # Shared configuration
│   ├── env/               # Python virtual environment
│   ├── logs/              # Application logs
│   └── config/            # Bench-level configuration
└── .vscode/               # VSCode workspace settings
```

### Common Development Commands

```bash
# Inside container
bench start  # Start development server with hot-reload

# Database operations
bench migrate  # Run database migrations
bench --site mysite.com migrate  # Site-specific migration

# Frontend builds
bench build  # Build all app assets
bench build --app my_custom_app  # Build specific app

# Code generation
bench new-app <app_name>  # Create new app
bench new-site <site_name>  # Create new site

# App management
bench get-app <git_url>  # Download app from git
bench install-app <app_name>  # Install app to current site
bench uninstall-app <app_name>  # Remove app from site

# Debugging
bench console  # Python REPL with Frappe context
bench mariadb  # Database console
```

## Platform Notes

### ARM64 and Apple Silicon

- Enable Docker Desktop's Rosetta emulation for initial builds when running on Apple Silicon with x86-only images.
- Prefer published multi-arch images (`frappe/bench`, `frappe/erpnext`) or build locally with `docker buildx bake --set *.platform=linux/amd64,linux/arm64` to cover both architectures in one pass.
- When using `pwd.yml`, export `DOCKER_DEFAULT_PLATFORM=linux/arm64` (or select the provided compose profile) to avoid unexpected emulation.
- Keep bind mounts under your user home directory and apply `:cached` or `:delegated` consistency flags for better performance on macOS.

## File Locations and Access

### Accessing Container Files

```bash
# Enter backend container shell
docker compose -f pwd.yml exec backend bash

# Navigate to bench directory
cd /home/frappe/frappe-bench/

# Key directories:
/home/frappe/frappe-bench/apps/     # All Frappe apps
/home/frappe/frappe-bench/sites/    # Site data and configuration
/home/frappe/frappe-bench/logs/     # Application logs
/home/frappe/frappe-bench/env/      # Python virtual environment
```

### Copying Files from Containers

```bash
# Copy entire app from container to host
docker compose -f pwd.yml cp backend:/home/frappe/frappe-bench/apps/my_app ./local-apps/

# Copy logs
docker compose -f pwd.yml cp backend:/home/frappe/frappe-bench/logs/ ./debug-logs/

# Copy site files
docker compose -f pwd.yml cp backend:/home/frappe/frappe-bench/sites/mysite.com ./backup/
```

### Useful Container Commands

```bash
# List all sites
docker compose -f pwd.yml exec backend bench list-sites

# List installed apps for a site
docker compose -f pwd.yml exec backend bench --site mysite.com list-apps

# View site configuration
docker compose -f pwd.yml exec backend cat /home/frappe/frappe-bench/sites/common_site_config.json

# Check logs in real-time
docker compose -f pwd.yml logs -f backend

# Execute bench command
docker compose -f pwd.yml exec backend bench --site mysite.com console

# Backup site
docker compose -f pwd.yml exec backend bench --site mysite.com backup --with-files
```

## Docker Concepts: Bind Mounts

See [Bind mounts and volumes](13-explanation/02-bind-mounts-and-volumes.md) for the repository's production storage and development source mounts. [Container immutability and persistence](13-explanation/01-container-immutability.md) explains the production boundary between image contents and site data, including [asset handling](13-explanation/03-asset-handling.md).

## Fork Management Best Practices

See [Fork management best practices](11-how-to/08-fork-management.md) for setting up a fork, keeping it updated, and organizing local customizations.

## Quick Start Examples

### 1. Quick Test (5 minutes)

**Goal:** Try Frappe/ERPNext without any local setup

```bash
# Clone and run
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
docker compose -f pwd.yml up -d

# Monitor setup progress (~5 minutes)
docker compose -f pwd.yml logs -f create-site

# When complete, access:
# URL: http://localhost:8080
# Username: Administrator
# Password: admin

# Cleanup when done
docker compose -f pwd.yml down -v
```

### 2. Development Environment (15 minutes)

**Goal:** Set up for daily development with hot-reload

```bash
# Copy devcontainer config
cp -R devcontainer-example .devcontainer

# Open in VSCode
# 1. Install "Dev Containers" extension
# 2. Command Palette (Ctrl+Shift+P) → "Reopen in Container"
# 3. Wait for container build (~5 min first time)

# Inside container terminal:
cd /workspace/development
python installer.py

# Follow prompts:
# - Site name: development.localhost
# - Install ERPNext: Yes
# - Version: version-15

# Start development server
cd frappe-bench
bench start

# Access: http://localhost:8000
# Edit files in: development/frappe-bench/apps/
```

### 3. Custom App Development (30 minutes)

**Goal:** Create and develop a custom Frappe application

```bash
# Prerequisite: Complete Example 2 first

# Inside development container
cd /workspace/development/frappe-bench

# Create new app
bench new-app library_management
# Follow prompts (title, description, publisher, etc.)

# Install to site
bench --site development.localhost install-app library_management

# Create DocTypes via web UI:
# 1. Go to: http://localhost:8000
# 2. Setup → Customize → DocType → New
# 3. Create: Book, Author, Borrower, etc.

# Or create via code:
# Edit: apps/library_management/library_management/library_management/doctype/

# Build and reload
bench build --app library_management
# Server auto-reloads (bench start watches for changes)
```

### 4. Production Deployment (1 hour)

**Goal:** Deploy Frappe in production with SSL

```bash
# Follow detailed guide
# See: docs/single-server-example.md

# Quick overview:
# 1. Setup server with Docker
# 2. Clone frappe_docker
# 3. Configure environment variables
# 4. Use compose.yaml + production overrides
# 5. Setup SSL with Traefik/Let's Encrypt
# 6. Deploy and monitor

# Key files:
# - compose.yaml
# - compose.mariadb.yaml
# - compose.redis.yaml
# - compose.proxy.yaml
# - compose.https.yaml

# Deploy command:
docker compose \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  up -d
```

### 5. Multi-Site Hosting

**Goal:** Host multiple Frappe sites on one server

```bash
# See: docs/11-how-to/05-publish-multiple-sites-on-different-ports.md

# Quick example:
# 1. Create multiple sites in development
bench new-site site1.com
bench new-site site2.com

# 2. Configure Nginx/Traefik for routing
# 3. Each site gets own database
# 4. Shared Redis and application code
```

---

## Framework Comparisons

See [Framework comparisons](13-explanation/06-framework-comparisons.md) for Frappe and Django project structures, conceptual mappings, and code examples.

---

## Resources and References

### Official Documentation

See [Official documentation](12-reference/03-external-links.md#official-documentation) for Frappe, ERPNext, and Docker documentation.

### Key Files in This Repository

- [`docs/05-development/01-development.md`](05-development/01-development.md) - Detailed development setup
- [`docs/02-setup/04-env-variables.md`](02-setup/04-env-variables.md) - Environment variable reference
- [`docs/02-setup/07-single-server-example.md`](02-setup/07-single-server-example.md) - Production deployment guide
- [`docs/04-operations/01-site-operations.md`](04-operations/01-site-operations.md) - Common site management tasks
- `development/installer.py` - Automated setup script
- [`pwd.yml`](https://github.com/frappe/frappe_docker/blob/main/pwd.yml) - Quick test configuration
- [`compose.yaml`](https://github.com/frappe/frappe_docker/blob/main/compose.yaml) - Base Docker Compose configuration

### Community Resources

See [Community resources](12-reference/03-external-links.md#community-resources) for the Frappe forum, school, and framework source.

### Essential Docker Commands Reference

```bash
# Service Management
docker compose up -d              # Start all services in background
docker compose down               # Stop and remove containers
docker compose down -v            # Stop and remove volumes (data loss!)
docker compose restart <service>  # Restart specific service
docker compose ps                 # List running services
docker compose logs -f <service>  # Follow logs for service

# Container Access
docker compose exec <service> bash    # Open shell in running container
docker compose exec <service> <cmd>   # Run command in container
docker compose run <service> <cmd>    # Run one-off command (creates new container)

# Debugging
docker compose logs --tail=100 <service>  # Last 100 log lines
docker compose top                        # Show running processes
docker inspect <container_name>           # Detailed container info

# Cleanup
docker system prune              # Remove unused containers/networks
docker volume prune              # Remove unused volumes (BE CAREFUL!)
docker image prune               # Remove unused images
```

### Essential Bench Commands Reference

```bash
# Site Operations
bench new-site <site_name>                    # Create new site
bench drop-site <site_name>                   # Delete site (asks confirmation)
bench list-sites                              # List all sites
bench use <site_name>                         # Set default site

# App Operations
bench get-app <git_url>                       # Download app from git
bench get-app <app_name>                      # Download from Frappe registry
bench install-app <app_name>                  # Install to default site
bench install-app <app_name> --site <site>   # Install to specific site
bench uninstall-app <app_name>               # Uninstall from default site
bench list-apps                              # List installed apps

# Development
bench start                      # Start development server (hot-reload)
bench build                      # Build frontend assets
bench build --app <app_name>    # Build specific app
bench migrate                    # Run database migrations
bench clear-cache                # Clear Redis cache
bench clear-website-cache        # Clear website route cache

# Database
bench mariadb                    # Open MariaDB console
bench backup                     # Backup default site
bench backup --with-files        # Backup with uploaded files
bench restore <path>             # Restore backup

# Code Generation
bench new-app <app_name>                      # Create new app
bench --site <site> console                   # Python REPL with Frappe context
bench --site <site> execute "<python_code>"   # Execute Python code

# Deployment
bench setup production <user>    # Setup for production (supervisor, nginx)
bench restart                    # Restart bench processes
bench update                     # Update framework and apps
```

### Troubleshooting Quick Reference

| Issue                     | Solution                                              |
| ------------------------- | ----------------------------------------------------- |
| Port 8080 already in use  | Change `PWD_PORT` in `.env` or stop other service     |
| Container won't start     | Check logs: `docker compose logs <service>`           |
| Site creation fails       | Check `create-site` logs, ensure DB is ready          |
| Can't connect to site     | Wait 5 min for initialization, check container health |
| Permission errors         | Check volume permissions, may need `chown`            |
| Out of disk space         | `docker system prune -a --volumes` (CAREFUL!)         |
| Python packages missing   | `bench pip install <package>` inside container        |
| Frontend not building     | `bench build --force`, check Node.js errors           |
| Database connection fails | Check `common_site_config.json`, Redis/MariaDB status |

### Getting Help

1. **Check existing docs** - Most issues covered in [`docs/07-troubleshooting/01-troubleshoot.md](07-troubleshooting/01-troubleshoot.md)
2. **Search Frappe Forum** - [discuss.frappe.io](https://discuss.frappe.io)
3. **GitHub Issues** - Search existing issues first
4. **Discord/Telegram** - Community real-time chat (links in main repo)

### Contributing

Found issues or improvements for this guide?

- Create an issue: [frappe_docker/issues](https://github.com/frappe/frappe_docker/issues)
- Submit focused PRs: keep updates scoped and split large efforts across multiple pull requests.
- Review CONTRIBUTING.md: for coding standards and review expectations.

---

_This guide provides a comprehensive overview of Frappe Docker for developers of all backgrounds. For specific use cases or advanced topics, refer to the linked documentation._

_Last updated: October 2025_
