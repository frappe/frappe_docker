# Frappe Docker Development Guide for Django Developers

*A comprehensive guide for Django developers getting started with Frappe Docker*

## Table of Contents
- [Understanding Frappe Docker Architecture](#understanding-frappe-docker-architecture)
- [Frappe vs Django Concepts](#frappe-vs-django-concepts)
- [Repository Structure](#repository-structure)
- [Custom Apps Explained](#custom-apps-explained)
- [Development Workflow](#development-workflow)
- [File Locations and Access](#file-locations-and-access)
- [Docker Concepts: Bind Mounts](#docker-concepts-bind-mounts)
- [Fork Management Best Practices](#fork-management-best-practices)
- [Quick Start Examples](#quick-start-examples)

---

## Understanding Frappe Docker Architecture

Frappe Docker provides a comprehensive containerized environment for developing and deploying Frappe/ERPNext applications. Unlike typical Django setups, Frappe uses a **multi-service architecture**.

### Core Services
- **backend** - Gunicorn server (like your Django app server)
- **frontend** - Nginx static file server + reverse proxy
- **queue-short/long** - Background job workers (like Celery)
- **scheduler** - Cron-like task scheduler
- **websocket** - Real-time Socket.IO server
- **db** - MariaDB/PostgreSQL database
- **redis-cache/queue** - Caching and job queues

## Frappe vs Django Concepts

### Project Structure Comparison

**Django Project:**
```python
myproject/
├── myproject/          # Project settings
├── blog/              # Django app
├── shop/              # Django app
└── users/             # Django app
```

**Frappe Bench:**
```
bench/
├── apps/
│   ├── frappe/        # Core framework (like Django itself)
│   ├── erpnext/       # Business app (complete ERP solution)
│   ├── hrms/          # HR Management app
│   └── my_custom_app/ # YOUR custom app
└── sites/
    └── mysite.com/    # Site using the apps above
```

### Key Differences from Django

1. **Multi-tenancy**: One installation can serve multiple sites
2. **Built-in job queues**: No need for separate Celery setup
3. **Real-time features**: WebSocket support built-in
4. **Bench management**: Tool for managing multiple apps/sites
5. **Database per site**: Each site gets its own database

## Repository Structure

### 📁 Core Configuration Files
- **compose.yaml** - Main Docker Compose file defining all services
- **example.env** - Environment variables template
- **pwd.yml** - "Play with Docker" - simplified single-file setup for quick testing
- **docker-bake.hcl** - Advanced Docker Buildx configuration

### 📁 images/ - Docker Image Definitions
- **images/bench/** - Development container with full Frappe tooling
- **images/production/** - Production-ready containers
- **images/custom/** - Build custom apps using apps.json
- **images/layered/** - Optimized layered builds

### 📁 overrides/ - Compose File Extensions
Docker Compose "overrides" that extend the base compose.yaml:
- **compose.mariadb.yaml** - Adds MariaDB service
- **compose.redis.yaml** - Adds Redis service  
- **compose.proxy.yaml** - Adds Traefik reverse proxy
- **compose.https.yaml** - Adds SSL/TLS support

### 📁 development/ - Dev Environment
- **development/installer.py** - Automated bench/site creation script
- Contains your local development files (git-ignored)

### 📁 resources/ - Runtime Templates
- **nginx-entrypoint.sh** - Dynamic configuration generator script
- **nginx-template.conf** - Nginx configuration template with variable substitution

## Custom Apps Explained

### What Are Frappe Custom Apps?
Custom apps are self-contained business applications that extend Frappe's functionality. Unlike Django apps that you build piece by piece, Frappe apps are complete business solutions.

### Custom App Structure
```
my_custom_app/
├── hooks.py                    # App configuration (like Django's apps.py)
├── modules.txt                 # List of modules in this app
├── my_custom_app/
│   ├── __init__.py
│   ├── config/
│   │   └── desktop.py          # Desktop icons/shortcuts
│   ├── my_module/              # Business module
│   │   ├── doctype/           # Models (like Django models)
│   │   │   ├── customer/
│   │   │   │   ├── customer.py      # Python controller
│   │   │   │   ├── customer.json    # Model definition
│   │   │   │   └── customer.js      # Frontend logic
│   │   └── page/              # Custom pages
│   ├── public/               # Static files
│   ├── templates/            # Jinja2 templates
│   └── www/                  # Web pages
└── requirements.txt          # Python dependencies
```

### Built-in Features (Auto-generated)
Every Frappe app automatically gets:
- **REST API** (automatic from DocType definitions)
- **Permissions system** (row-level security built-in)
- **Audit trails** (automatic change tracking)
- **Custom fields** (users can add fields without code changes)
- **Workflows** (approval processes)
- **Reports** (built-in report builder)

### Creating Custom Apps
```bash
# Enter the development container
docker exec -it <container_name> bash

# Create new app
bench new-app my_custom_app

# Install app to a site
bench --site mysite.com install-app my_custom_app
```

## Development Workflow

### Quick Test Setup (pwd.yml)
```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker  
docker compose -f pwd.yml up -d
# Visit http://localhost:8080 (user: Administrator, pass: admin)
```

### Full Development Setup
1. Copy devcontainer example: `cp -R devcontainer-example .devcontainer`
2. Use VSCode Dev Containers extension
3. Run installer: `cd /workspace/development && python installer.py`
4. Your development files appear in `development/frappe-bench/`

### Development File Locations
```
development/
├── frappe-bench/           # Your actual Frappe installation
│   ├── apps/              # Frappe apps (frappe, erpnext, custom apps)
│   │   ├── frappe/        # Core framework
│   │   ├── erpnext/       # ERPNext application  
│   │   └── my_custom_app/ # Your custom apps
│   ├── sites/             # Your sites
│   │   ├── development.localhost/ # Main dev site
│   │   └── common_site_config.json # Shared config
│   └── env/               # Python virtual environment
└── .vscode/               # VSCode settings
```

## File Locations and Access

### Accessing Container Files
```bash
# Enter backend container
docker compose -f pwd.yml exec backend bash

# Navigate to bench directory
cd /home/frappe/frappe-bench/

# Key directories:
/home/frappe/frappe-bench/apps/     # All Frappe apps
/home/frappe/frappe-bench/sites/    # Site data and configuration
```

### Copying Files from Containers
```bash
# Copy files from container to host
docker compose -f pwd.yml cp backend:/home/frappe/frappe-bench/apps/ ./local-apps/
```

### Useful Container Commands
```bash
# List sites
docker compose -f pwd.yml exec backend bench list-sites

# List installed apps  
docker compose -f pwd.yml exec backend bench list-apps

# View site configuration
docker compose -f pwd.yml exec backend cat /home/frappe/frappe-bench/sites/common_site_config.json
```

## Docker Concepts: Bind Mounts

### What Are Bind Mounts?
Bind mounts directly connect a file/directory on your host machine to a file/directory inside a container, creating real-time synchronization.

### Bind Mount Types
```yaml
# Bind Mounts (Direct host path mapping)
volumes:
  - /home/user/myproject:/app          # Host path : Container path
  - ./development:/home/frappe/frappe-bench/sites  # Relative path

# Named Volumes (Docker-managed storage)  
volumes:
  - db_data:/var/lib/mysql             # Volume name : Container path

# Anonymous Volumes (Temporary)
volumes:
  - /tmp                               # Just container path
```

### Development Use Cases
```yaml
# Development code editing
volumes:
  - ./my_custom_app:/home/frappe/frappe-bench/apps/my_custom_app

# Configuration files
volumes:
  - ./config/my-site.conf:/etc/nginx/sites-enabled/my-site.conf:ro

# Database data (persistent)
volumes:
  - ./data/mysql:/var/lib/mysql

# Logs and debugging
volumes:
  - ./logs:/home/frappe/frappe-bench/logs
```

### Performance Options
```yaml
# For macOS/Windows
volumes:
  - ./development:/home/frappe/frappe-bench:cached    # Better performance
  - ./development:/home/frappe/frappe-bench:delegated # Best for writes
```

## Fork Management Best Practices

### Setting Up Your Fork
```bash
# Add upstream remote (one time)
git remote add upstream https://github.com/frappe/frappe_docker.git

# Create development branch
git checkout -b my-development
```

### Safe Areas for Customizations
**✅ Safe (Won't conflict with upstream):**
- `development/` directory contents
- New compose override files (`compose.my-*.yaml`)
- New scripts in `scripts/` directory
- New documentation files in `docs/`
- `.env.local` files

**⚠️ Risky (May conflict):**
- `compose.yaml` - Core compose file
- `docker-bake.hcl` - Build configuration
- Existing scripts

**❌ Avoid modifying:**
- Core Dockerfiles in `images/`
- Main configuration files

### Sync Strategy
```bash
# Sync with upstream
git checkout main
git pull upstream main
git checkout my-development  
git rebase main
```

### Custom Environment Setup
```yaml
# compose.my-env.yaml
version: "3.7"

services:
  backend:
    environment:
      - MY_CUSTOM_VAR=value
    volumes:
      - ./development/my_custom_scripts:/home/frappe/my_scripts
  
  my-custom-service:
    image: redis:alpine
```

### .gitignore Strategy
```gitignore
# Add to existing .gitignore
.env.local
development/sites/*
development/apps/*
!development/apps.json
development/logs/
my-local-configs/
compose.my-env.yaml.local
```

## Quick Start Examples

### 1. Quick Test (pwd.yml)
```bash
# Clone and test
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
docker compose -f pwd.yml up -d

# Follow site creation
docker compose -f pwd.yml logs -f create-site

# Access: http://localhost:8080
# Login: Administrator / admin
```

### 2. Development Setup
```bash
# Copy devcontainer config
cp -R devcontainer-example .devcontainer

# Open in VSCode with Dev Containers extension
# Run installer inside container
cd /workspace/development
python installer.py --site-name mysite.localhost

# Access development files in development/frappe-bench/
```

### 3. Custom App Development
```bash
# Inside development container
bench new-app my_erp_customization
bench --site mysite.localhost install-app my_erp_customization

# Edit files in development/frappe-bench/apps/my_erp_customization/
```

### 4. Production Deployment
```bash
# Use single-server example
# Follow docs/single-server-example.md
# Customize with compose overrides as needed
```

## Resources and References

### Documentation
- [Frappe Framework Docs](https://frappeframework.com/docs)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Docker Documentation](https://docs.docker.com)

### Key Files in This Repository
- [`docs/development.md`](docs/development.md) - Development setup guide
- [`docs/single-server-example.md`](docs/single-server-example.md) - Production deployment
- [`development/installer.py`](development/installer.py) - Automated setup script
- [`pwd.yml`](pwd.yml) - Quick test configuration

### Useful Commands
```bash
# Container management
docker compose logs -f <service_name>
docker compose exec <service_name> bash
docker compose ps
docker compose down

# Bench commands (inside container)
bench list-sites
bench list-apps
bench new-site <site_name>
bench install-app <app_name>
bench migrate
bench build
```

---

*This guide covers the essentials for Django developers transitioning to Frappe Docker development. For specific use cases or advanced topics, refer to the official documentation or create additional guides in this docs/ directory.*

*Last updated: October 2025*
*Author: Development Team*