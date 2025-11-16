# Production ERPNext Deployment

Complete guide for deploying ERPNext in production using Docker Compose with Traefik and Let's Encrypt SSL.

---

## Overview

This guide provides everything needed to deploy a production-ready ERPNext instance using Docker Compose. The setup includes:

- **ERPNext v15.82.1** - ERP application
- **Frappe Framework v15.82.1** - Application framework
- **Traefik v2.11** - Reverse proxy with automatic Let's Encrypt SSL
- **MariaDB 11.8** - Database server
- **Redis** - Cache, queue, and socketio

### Architecture

Three separate Docker Compose projects work together:

1. **Traefik** - Reverse proxy, SSL certificates, load balancing
2. **MariaDB** - Shared database for all ERPNext sites
3. **ERPNext** - Application containers (backend, frontend, workers, scheduler)

### Repository Structure

```
erp-is/
├── production/              # Production deployment (this directory)
│   ├── README.md           # This guide
│   ├── *.env.example       # Configuration templates
│   ├── scripts/            # Automation scripts
│   │   ├── deploy.sh              # Main deployment (includes setup/regenerate)
│   │   ├── create-site.sh         # Create new site
│   │   ├── backup-site.sh         # Backup automation
│   │   ├── validate-env.sh        # Config validation
│   │   ├── logs.sh                # Log viewer
│   │   └── stop.sh                # Stop services
│   └── production.yaml     # Generated compose file (do not edit)
├── overrides/              # Upstream compose overlays
├── docs/                   # Upstream documentation
└── compose.yaml            # Upstream base configuration
```

**Important**: This is a fork of [frappe/frappe_docker](https://github.com/frappe/frappe_docker):
- **Custom files** (in `production/`) are maintained in this fork
- **Infrastructure files** (compose.yaml, overrides/) track upstream
- **Container images** are pulled from official Frappe Docker registry

---

## Table of Contents

- [Stack Versions & Fork Notes](#stack-versions--fork-notes)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Configuration](#environment-configuration)
- [Script Usage Guide](#script-usage-guide)
- [Deployment](#deployment)
- [Custom Apps & Third-Party Integrations](#custom-apps--third-party-integrations)
- [Common Operations](#common-operations)
- [Update Procedures](#update-procedures)
- [Apply Updates to Sites (new vs existing)](#apply-updates-to-sites-new-vs-existing)
- [Git Workflow](#git-workflow)
- [Maintenance Playbook](#maintenance-playbook)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Architecture Explained](#architecture-explained)

---

## Stack Versions & Fork Notes

| Layer | Version / Source | Why it matters |
|-------|------------------|----------------|
| Host OS (reference) | Ubuntu 22.04 LTS | All scripts are validated on this release; Debian 11/12 behave the same as long as Docker 24+ is installed. |
| ERPNext | v15.82.1 | Set through `ERPNEXT_VERSION` in `production/production.env`. Keep this aligned with the branch you pin in `apps.json`. |
| Frappe Framework | v15.82.1 | Declared as `FRAPPE_VERSION`; must match ERPNext to avoid schema drift. |
| MariaDB | 11.8 (official image) | Shared across every site in the bench; plan capacity accordingly. |
| Redis | `redis:alpine` | Provides cache, queue, and websocket backplanes. |
| Traefik | v2.11 | Handles TLS (Let’s Encrypt) and routing. |
| Python (app containers) | 3.11.6 on Debian Bookworm | Comes from `images/custom/Containerfile`; upgrade only after testing custom apps. |
| Node.js | 20.19.2 | Needed for asset builds (`bench build`). |


---

## Quick Start

**For experienced users:**

```bash
# 1. Generate secure passwords
openssl rand -base64 32  # DB password
openssl rand -base64 24  # Admin password
htpasswd -nB admin       # Traefik dashboard password

# 2. Configure environment (interactive setup)
./scripts/deploy.sh --setup  # Creates *.env from templates
# Edit all three files with your values

# 3. Validate configuration
./scripts/validate-env.sh    # Checks for errors before deploy

# 4. Deploy all services
./scripts/deploy.sh

# 5. Create your first site
./scripts/create-site.sh erp.example.com

# 6. View logs
./scripts/logs.sh           # Interactive service selection
```

**First time?** Follow the complete checklist below.

---

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04/22.04 LTS or Debian 11/12
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Disk**: 50GB+ SSD storage
- **Network**: Public IP with ports 80 and 443 open
- **Domain**: DNS pointing to your server

### Software Requirements

```bash
# Docker Engine 20.10+
docker --version

# Docker Compose v2
docker compose version
```

---

## Pre-Deployment Checklist

### ✅ 1. Verify System

```bash
# Check OS version
lsb_release -a

# Check available RAM
free -h

# Check disk space
df -h

# Check server is accessible
ping -c 3 $(hostname -I | awk '{print $1}')
```

### ✅ 2. Configure DNS

```bash
# Verify DNS propagation (wait 24-48h after DNS change)
dig +short erp.example.com
# Should return your server's public IP
```

### ✅ 3. Configure Firewall

```bash
# Allow required ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Verify
sudo ufw status
```

### ✅ 4. Install Docker

```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, then test
docker ps
```

### ✅ 5. Validate Environment

```bash
# Run validation script (checks all config files)
./scripts/validate-env.sh

# Should pass all checks before proceeding
```

---

## Script Usage Guide

All scripts have been optimized for efficiency and include comprehensive help. Every script supports `-h` or `--help`.

### 📋 Script Overview

| Script | Purpose | Key Features |
|--------|---------|--------------|
| **deploy.sh** | Main deployment | `--setup`, `--regenerate`, validation |
| **create-site.sh** | Create ERPNext site | Interactive prompts, validation |
| **backup-site.sh** | Advanced backups | Encryption, auto-copy, cleanup |
| **logs.sh** | View service logs | Interactive menu, service selection |
| **stop.sh** | Stop services | Selective stopping, `--all` option |
| **validate-env.sh** | Config validation | Password strength, cross-validation |

### 🚀 Deploy Script

```bash
# Get help
./scripts/deploy.sh --help

# Setup environment files from templates
./scripts/deploy.sh --setup

# Validate and deploy all services
./scripts/deploy.sh

# Regenerate production.yaml only (no deploy)
./scripts/deploy.sh --regenerate
```

### 🏗️ Create Site Script

```bash
# Get help
./scripts/create-site.sh --help

# Interactive mode
./scripts/create-site.sh

# Direct usage
./scripts/create-site.sh erp.example.com
./scripts/create-site.sh erp.example.com MySecurePass123
```

### 💾 Backup Script (Advanced)

```bash
# Get help
./scripts/backup-site.sh --help

# Basic backup
./scripts/backup-site.sh erp.example.com

# Advanced backup with files, auto-copy, cleanup (7-day retention)
./scripts/backup-site.sh erp.example.com --with-files --auto-copy --cleanup-old 7

# Host-only backup that prunes everything except this run
./scripts/backup-site.sh erp.example.com --with-files --auto-copy --host-only --cleanup-old latest

# Encrypted backup
BACKUP_PASSPHRASE='your-secret' ./scripts/backup-site.sh erp.example.com --encrypt --auto-copy

# Automated (environment variables)
AUTO_COPY=1 CLEANUP_OLD=1 ./scripts/backup-site.sh erp.example.com
```

**Backup Features:**
- **Encryption**: GPG symmetric encryption with AES256
- **Auto-copy & host-only**: `--auto-copy` mirrors to the host; use `--flat-host-path` (default) to drop files directly in `$HOST_BACKUP_ROOT` or `--nested-host-path`/`HOST_BACKUP_LAYOUT=nested` for `$HOST_BACKUP_ROOT/<site>/<timestamp>`. Add `--host-only` to delete container copies once the host copy is verified.
- **Cleanup policies**: `--cleanup-old` accepts `N` (days), `keep:N` (retain newest runs), or `latest` (keep only the current run); defaults to `BACKUP_RETENTION_DAYS`
- **Validation**: Verify backup files and sizes
- **Logging**: Detailed operation logs in `/tmp/`

#### Standard backup recipes

- **Host-only snapshot, keep only the latest run**

  ```bash
  ./scripts/backup-site.sh erp.example.com \
    --with-files --auto-copy --host-only --cleanup-old latest
  ```

  This flow copies fresh files to the host, deletes the container copies immediately, and prunes older host snapshots so only the latest timestamp remains.

- **Cron-friendly daily backups with 30‑day retention**

  ```bash
  AUTO_COPY=1 CLEANUP_OLD=1 ./scripts/backup-site.sh erp.example.com
  ```

  Environment flags keep the command short for crontab entries. Set `BACKUP_RETENTION_DAYS` globally (defaults to 30) or export `CLEANUP_POLICY="keep:7"` if you prefer to keep a fixed number of runs.

### 📊 Logs Script

```bash
# Get help
./scripts/logs.sh --help

# Interactive menu
./scripts/logs.sh

# Direct service access
./scripts/logs.sh 1          # Backend logs
./scripts/logs.sh backend    # Same as above
./scripts/logs.sh frontend   # Nginx logs
./scripts/logs.sh all        # All services
./scripts/logs.sh backend --tail 100  # Show last 100 lines and exit
./scripts/logs.sh --tail              # Tail recent logs for every service
```

**Available Services:**
1. **backend** - Gunicorn application server
2. **frontend** - Nginx reverse proxy
3. **websocket** - Socket.io for real-time features
4. **queue-short** - Short-running background jobs
5. **queue-long** - Long-running background jobs
6. **scheduler** - Cron-like background scheduler
7. **all** - All services combined

### 🛑 Stop Script

```bash
# Get help
./scripts/stop.sh --help

# Interactive mode (asks about MariaDB/Traefik)
./scripts/stop.sh

# Stop everything without prompts
./scripts/stop.sh --all
```

### ✅ Validation Script

```bash
# Get help
./scripts/validate-env.sh --help

# Validate all environment files
./scripts/validate-env.sh
```

**Validation Checks:**
- Required variables present
- Password strength (16+ characters recommended)
- Email format validation
- Cross-file password matching
- Placeholder detection
- Weak password detection

---

## Environment Configuration

### Three Environment Files Required

1. **`production/production.env`** - ERPNext application config
2. **`production/mariadb.env`** - Database config
3. **`production/traefik.env`** - Reverse proxy config

### Step-by-Step Configuration

#### 1. Generate Passwords

```bash
# Database password (use in production.env AND mariadb.env)
openssl rand -base64 32

# Admin password (use in production.env)
openssl rand -base64 24

# Traefik dashboard password (use in traefik.env)
htpasswd -nB admin
# Or use: https://hostingcanada.org/htpasswd-generator/
```

#### 2. Configure `production/production.env`

```bash
./scripts/deploy.sh --setup  # Create from templates
nano production/production.env
```

Required values:
```env
SITES=erp.example.com                           # Your domain
ERPNEXT_VERSION=v15.82.1                        # ERPNext version
FRAPPE_VERSION=v15.82.1                         # Frappe version
DB_HOST=mariadb-database                        # Database host
DB_PASSWORD=<paste-generated-db-password>       # From step 1
REDIS_CACHE=redis-cache:6379                    # Redis cache
REDIS_QUEUE=redis-queue:6379                    # Redis queue
REDIS_SOCKETIO=redis-socketio:6379              # Redis socketio
LETSENCRYPT_EMAIL=admin@example.com             # For SSL certs
ADMIN_PASSWORD=<paste-generated-admin-password> # From step 1
```

#### 3. Configure `production/mariadb.env`

```bash
nano production/mariadb.env  # Already created by --setup
```

Required values:
```env
DB_PASSWORD=<same-as-production.env>  # MUST match production.env
```

#### 4. Configure `production/traefik.env`

```bash
nano production/traefik.env  # Already created by --setup
```

Required values:
```env
TRAEFIK_DOMAIN=traefik.example.com    # Dashboard subdomain
EMAIL=admin@example.com               # For SSL certs
HASHED_PASSWORD=<paste-from-htpasswd> # From step 1
```

#### 5. Secure Files

```bash
chmod 600 production/*.env

# Verify they're git-ignored
git status | grep production.env
# Should return nothing
```

---

## Deployment

### Deploy Services

```bash
./scripts/deploy.sh
```

**What it does:**
1. **Validates** environment configuration (`./scripts/validate-env.sh`)
2. **Deploys Traefik** (reverse proxy + SSL)
3. **Deploys MariaDB** (database)
4. **Generates** ERPNext configuration (`production.yaml`) from:
   - Base: `compose.yaml`
   - Redis overlay: `overrides/compose.redis.yaml`
   - Multi-bench overlay: `overrides/compose.multi-bench.yaml`
   - SSL overlay: `overrides/compose.multi-bench-ssl.yaml`
5. **Deploys ERPNext** (backend, frontend, workers, scheduler)

**Expected output:**
```
[INFO] ERPNext Production Deployment
[INFO] Validating configuration...
✅ Validation Passed
[INFO] Step 1: Deploying Traefik...
✓ Traefik deployed
[INFO] Step 2: Deploying MariaDB...
✓ MariaDB deployed. Waiting 30s for initialization...
[INFO] Step 3: Generating production.yaml...
✓ Generated
[INFO] Step 4: Deploying ERPNext...
✓ ERPNext deployed
[INFO] ✓ Deployment complete!
```

### Create Site

```bash
./scripts/create-site.sh erp.example.com
```

**Wait 2-3 minutes for:**
- Database initialization
- Frappe installation
- ERPNext installation
- SSL certificate generation

### Verify Deployment

```bash
# Check all services are running
docker ps

# Check service health
docker compose -f production/production.yaml ps

# View logs
./scripts/logs.sh

# Follow logs (live)
./scripts/logs.sh -f backend

```


### Access Your Site

1. Open browser: `https://erp.example.com`
2. Username: `Administrator`
3. Password: Check `production/production.env` → `ADMIN_PASSWORD`

---

## Custom Apps & Third-Party Integrations

### Why ship custom logic as apps?

- **Upstream-safe**: Apps keep your business logic outside the upstream fork, so rebasing on `frappe_docker` stays painless.
- **Repeatable**: Every site receives the exact same code (DocTypes, patches, API clients) whenever the container is rebuilt.
- **Supported**: This mirrors the official [frappe_docker custom app workflow](../docs/container-setup/02-build-setup.md#define-custom-apps).

### 1. Describe the apps you need (`apps.json`)

Create a manifest in the repository root that lists every app you want baked into the image—first-party or third-party:

```json
[
  { "url": "https://github.com/frappe/erpnext", "branch": "version-15" },
  { "url": "https://github.com/frappe/hrms", "branch": "version-15" },
  { "url": "https://github.com/acme/custom_integrations", "branch": "main" }
]
```

Convert it to base64 once so the build context can read it without extra files:

```bash
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)
```

### 2. Build (and optionally push) a custom ERPNext image

Use the official layered image as the base and inject your apps list:

```bash
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=registry.example.com/erpnext-custom:15 \
  --file=images/layered/Containerfile .

# optional
docker push registry.example.com/erpnext-custom:15
```

> Prefer `docker buildx bake -f docker-bake.hcl --set erpnext.args.APPS_JSON_BASE64=$APPS_JSON_BASE64` if you already rely on Buildx/CI.

### 3. Point production to the new image

Edit `production/production.env` so compose uses your artifact everywhere:

```env
CUSTOM_IMAGE=registry.example.com/erpnext-custom
CUSTOM_TAG=15
PULL_POLICY=always
```

Regenerate and redeploy so every service shares the same build:

```bash
./scripts/deploy.sh --regenerate
./scripts/deploy.sh
```

### 4. Install or update apps on sites

All apps listed in `apps.json` become available inside the bench. You still choose which sites receive them.

**New site**

```bash
./scripts/create-site.sh erp.example.com
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com install-app custom_integrations hrms
```

**Existing site**

```bash
# Install a newly added app
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com install-app custom_integrations

# Apply database patches after pulling latest code/image
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com migrate

# Rebuild assets when the app ships JS/CSS
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build
```

### 5. Wire in third-party services securely

- Store API keys or secrets per site with `bench --site <site> set-config SERVICE_API_KEY value --as-dict` so they land in `site_config.json` instead of the repo.
- Use background jobs (`frappe.enqueue`) inside your app for webhook callbacks, polling jobs, or queue workers that call external APIs.
- Mount extra certificates or client libraries via an override compose file if an integration needs system packages.
- Keep outbound allow-lists in Traefik/MariaDB untouched—integrations happen from the backend container, so no Traefik tweaks are required unless you expose a new inbound service.

### 6. Keep apps synchronized

- Version pin each entry in `apps.json` (tag, branch, or commit) so rebuilds are deterministic.
- When a third-party releases an update, bump the branch or tag, rebuild the image, redeploy, and run `bench migrate` on every existing site.
- Automate this via CI to ensure upstream merges (`git fetch upstream && git merge upstream/main`) and app bumps happen in the same pipeline.

Following this flow keeps the deployment upstream-compatible while giving you a repeatable way to include bespoke code, official marketplace apps, or deep third-party integrations without touching container internals manually.

---

## Common Operations

### Backup Site

```bash
# Basic backup
./scripts/backup-site.sh erp.example.com

# Advanced backup with files and 7-day cleanup
./scripts/backup-site.sh erp.example.com --with-files --auto-copy --cleanup-old 7

# Encrypted backup with cleanup
BACKUP_PASSPHRASE='your-secret' ./scripts/backup-site.sh erp.example.com \
  --encrypt --auto-copy --cleanup-old

# Host-only snapshot keeping only this run
./scripts/backup-site.sh erp.example.com --with-files --auto-copy --host-only --cleanup-old latest
```

**Backup Features:**
- **Database + Files**: Use `--with-files` to include uploaded files
- **Auto-copy**: `--auto-copy` copies backups to host `$HOST_BACKUP_ROOT/<site>/<timestamp>`
- **Host-only**: `--host-only` deletes container copies after verifying the host snapshot
- **Encryption**: `--encrypt` with GPG AES256 (requires `BACKUP_PASSPHRASE`)
- **Cleanup**: `--cleanup-old` accepts `N` (days), `keep:N` (runs), or `latest` to prune aggressively
- **Validation**: Automatic backup verification and size reporting

Backups are stored in: `sites/erp.example.com/private/backups/` (container) or `./backups/` (host)

### View Logs

```bash
# Interactive service selection
./scripts/logs.sh

# Specific services
./scripts/logs.sh backend     # Application logs
./scripts/logs.sh frontend    # Nginx logs
./scripts/logs.sh scheduler   # Background jobs
./scripts/logs.sh all         # All services

# Alternative: direct Docker commands
docker compose -f production/production.yaml logs -f backend

# Tail logs without following
./scripts/logs.sh backend --tail 200
./scripts/logs.sh --tail           # All services, last 200 lines
```

### Stop Services

```bash
# Interactive mode (asks about dependencies)
./scripts/stop.sh

# Stop everything without prompts
./scripts/stop.sh --all
```

### Restart Services

```bash
./scripts/stop.sh --all
./scripts/deploy.sh
```

### Update ERPNext

```bash
# Update version in production.env
nano production/production.env
# Change: ERPNEXT_VERSION=v15.83.0

# Pull new images
docker compose -f production/production.yaml pull

# Redeploy
./production/scripts/deploy.sh

# Run migrations
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com migrate
```

### Add New Site (Multi-tenancy)

```bash
# Update SITES in production.env
nano production/production.env
# Change: SITES=erp.example.com,erp2.example.com

# Regenerate configuration
./scripts/deploy.sh --regenerate

# Apply changes
docker compose -f production/production.yaml up -d

# Create new site
./scripts/create-site.sh erp2.example.com

# Install custom apps that were baked into the image
docker compose -f production/production.yaml exec backend \
  bench --site erp2.example.com install-app custom_integrations hrms

# Run migrations and build assets once
docker compose -f production/production.yaml exec backend \
  bench --site erp2.example.com migrate

docker compose -f production/production.yaml exec backend \
  bench --site erp2.example.com build
```

---

## Update Procedures

### Understanding the Update Layers

This deployment has **three layers** that update independently:

1. **Infrastructure Layer** (frappe_docker)
   - Docker Compose configurations
   - Container build instructions
   - Deployment scripts structure
   - **Updates via**: `git fetch upstream && git merge upstream/main`

2. **Application Layer** (ERPNext/Frappe)
   - ERPNext features and bug fixes
   - Frappe framework updates
   - **Updates via**: Changing version tags in `production.env`

3. **Customization Layer** (Custom Apps & Integrations)
  - Custom Frappe apps, DocTypes, API clients, third-party connectors
  - Site-level configurations stored via `bench set-config`
  - **Updates via**: Rebuilding images with a new `apps.json`, migrating sites, and redeploying containers

### Update Infrastructure (Docker Configs)

**What this updates**: Compose files, build configs, deployment improvements

```bash
# 1. Sync with upstream frappe_docker
cd /path/to/erp-is-test
git fetch upstream
git merge upstream/main

# 2. Review infrastructure changes
git log --oneline upstream/main ^HEAD
git diff HEAD~1 compose.yaml
git diff HEAD~1 overrides/

# 3. Regenerate production.yaml with new infrastructure
./scripts/deploy.sh --regenerate

# 4. Review generated configuration
docker compose -f production/production.yaml config > /tmp/new-config.yaml
diff production/production.yaml /tmp/new-config.yaml || true

# 5. Apply infrastructure updates
docker compose -f production/production.yaml up -d

# 6. Verify all services healthy
docker compose -f production/production.yaml ps
```

**Important**: This does NOT update ERPNext version, only how it runs.

### Update ERPNext Version

**What this updates**: ERPNext features, bug fixes, Frappe framework

```bash
# 1. Check current version
docker compose -f production/production.yaml exec backend bench version

# 2. Backup before upgrading
./scripts/backup-site.sh erp.example.com --with-files --auto-copy

# 3. Update version in production.env
nano production/production.env
# Change:
# ERPNEXT_VERSION=v15.82.1  →  ERPNEXT_VERSION=v15.85.0
# FRAPPE_VERSION=v15.82.1   →  FRAPPE_VERSION=v15.85.0

# 4. Regenerate configuration
./scripts/deploy.sh --regenerate

# 5. Pull new images (downloads updated ERPNext)
docker compose -f production/production.yaml pull

# 6. Stop services
./scripts/stop.sh

# 7. Start with new version
docker compose -f production/production.yaml up -d

# 8. Run database migrations
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com migrate

# 9. Clear cache and rebuild
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build

# 10. Verify new version
docker compose -f production/production.yaml exec backend bench version
```

### Apply Updates to Sites (new vs existing)

Use the same redeploy pipeline for every site, but tailor the final bench commands depending on whether the site already exists.

**New sites created after an update**

1. Run `./scripts/create-site.sh new.example.com` once the new image is live.
2. Install any optional apps: `bench --site new.example.com install-app custom_integrations hrms`.
3. Seed data, fixtures, or integrations using your app's onboarding commands.

Because the site is created after the image rebuild, it automatically receives the latest code; no manual migration is needed beyond the installer.

**Existing sites that were updated**

1. Stop users (maintenance window) and take a backup: `./scripts/backup-site.sh erp.example.com --with-files`.
2. After redeploying containers, run:

```bash
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com migrate
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache
```

3. If the update introduced new apps, install them explicitly and migrate again.
4. Re-enable background jobs (`bench enable-scheduler`) if you disabled them for the maintenance window.


### Update Custom Apps & Integrations

**What this updates**: Custom Frappe apps, DocTypes, webhook handlers, and any bundled third-party modules.

```bash
# 1. Pull or merge the new code for each app, then refresh apps.json
git pull origin main  # inside every custom app repo
vim apps.json         # bump branch/tag references if needed

# 2. Rebuild the image with the refreshed manifest
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)
docker build \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=registry.example.com/erpnext-custom:15 .
docker push registry.example.com/erpnext-custom:15

# 3. Update production to pull the new tag
sed -i 's/CUSTOM_TAG=.*/CUSTOM_TAG=15/' production/production.env
./scripts/deploy.sh --regenerate
./scripts/deploy.sh

# 4. Apply database patches and rebuild assets per site
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com migrate
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build
```

### Complete Update (All Layers)

**Use this for major version jumps or after long periods:**

```bash
# 1. Backup everything first
./scripts/backup-site.sh erp.example.com --with-files --auto-copy

# 2. Update infrastructure
git fetch upstream && git merge upstream/main

# 3. Update ERPNext version in production.env
nano production/production.env

# 4. Regenerate everything
./scripts/deploy.sh --regenerate

# 5. Deploy
./scripts/stop.sh
docker compose -f production/production.yaml pull
docker compose -f production/production.yaml up -d

# 6. Migrate
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com migrate

# 7. Rebuild assets and clear cache
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force
```

## Git Workflow

### Branch contract

| Branch | Purpose | Deploy target |
|--------|---------|---------------|
| `main` | Production truth. Tracks only tested commits paired with container/image tags referenced in `production.env`. | Production |
| `staging` | Release candidate. Used to exercise upstream merges and new custom-app tags against a staging bench. | Staging bench (optional) |
| `dev` | Scratch/feature work. Safe spot to prototype new overrides, scripts, or Containerfile tweaks. | Local only |

**Remotes:**

- `origin` → this fork (`erp-is`).
- `upstream` → `https://github.com/frappe/frappe_docker.git`.

### Sync loop (weekly)

1. `git checkout dev && git fetch upstream` – bring in the latest frappe_docker changes.
2. `git merge upstream/main` (or `git rebase upstream/main`) – resolve conflicts in `overrides/`, `compose.yaml`, and `production/` scripts.
3. Smoke-test locally (`./scripts/deploy.sh --regenerate && docker compose -f production/production.yaml up -d`).
4. Promote into `staging`: `git switch staging && git merge dev` once tests pass.
5. Cut a tested release into `main` only after staging verification and update the stack-version table + `.env` pins.

### Custom app release recipe

- Keep each custom Frappe app in its own repository.
- Tag or branch the app when you are ready to promote (`git tag v2.4.0`).
- Update `apps.json` with that tag/commit and keep the file sorted. This manifest is the **source of truth** for `APPS_JSON_BASE64`.
- Rebuild/push the custom image from the repo root:

  ```bash
  export APPS_JSON_BASE64=$(base64 -w0 apps.json)
  docker build -f images/custom/Containerfile \
    --build-arg FRAPPE_BRANCH=version-15 \
    --build-arg APPS_JSON_BASE64=$APPS_JSON_BASE64 \
    -t registry.example.com/erpnext-custom:v15-2024.09 .
  docker push registry.example.com/erpnext-custom:v15-2024.09
  ```

- Update `production/production.env` (`CUSTOM_TAG=v15-2024.09`), regenerate, then run migrations for each site.

### Helpful habits

- Use `git worktree` to keep `dev`, `staging`, and `main` checked out simultaneously so you can hotfix production without stashing local experiments.
- Commit regenerated `production/production.yaml` only when auditing diffs—normally it stays generated.
- Keep a short `CHANGELOG.md` (or GitHub Releases) per branch so stakeholders know which ERPs/custom apps were promoted.
- Treat `bench` commands exactly like `python manage.py`: every change should be expressed as a migration, patch, or fixture committed alongside app code.

## Maintenance Playbook

### Daily / Continuous

- `./scripts/logs.sh --tail` – scan for traceback spikes in backend/worker containers.
- `docker compose -f production/production.yaml ps` – confirm containers are `Up` and restarts are zero.
- `bench doctor` (inside backend) for a consolidated health check.
- Respond to Traefik cert emails quickly—renewals are automatic, but DNS issues show up here first.

### Weekly

- Validate backups: `ls -lh backups/$(date +%Y-*)` and run a dry-run restore in staging (`bench --site staging.local restore ...`).
- Apply OS security patches (`sudo unattended-upgrade` or manual `apt update && apt upgrade`).
- Review pending PRs from upstream frappe_docker—if a fix matters to you, merge it into `dev` early.

### Monthly & release cadence

- Pick a low-traffic window, announce downtime, and tag the commit you plan to deploy.
- Create a staging bench (optional but recommended) and run `./scripts/deploy.sh --regenerate` + `./scripts/deploy.sh` against it.
- Execute automated checks: `bench --site staging.local migrate`, `bench --site staging.local build`, and any Cypress/API smoke tests you maintain.
- Freeze the container tags (`CUSTOM_TAG`, `ERPNEXT_VERSION`, `FRAPPE_VERSION`) before moving to production.

### Scheduled maintenance workflow

1. **Notify + prep** – enable maintenance banners in ERPNext, pause schedulers if heavy migrations are expected.
2. **Fresh backups** – `./scripts/backup-site.sh <site> --with-files --auto-copy --cleanup-old latest`.
3. **Deploy** – `./scripts/stop.sh`, `docker compose -f production/production.yaml pull`, `./scripts/deploy.sh`.
4. **Post-deploy bench tasks** – run `bench --site <site> migrate`, `build`, and `clear-cache` (see [Apply Updates to Sites](#apply-updates-to-sites-new-vs-existing)).
5. **Smoke tests** – log in as an admin, run a report, submit a Sales Order, and ping critical integrations/webhooks.
6. **Resume schedulers** – `bench --site <site> enable-scheduler`.
7. **Document** – capture version/tag, time, and any anomalies for traceability.

### Rollback fast path

If something regresses:

```bash
# 1. Stop new containers and bring back previous tags
git checkout main~1  # or the last known-good tag
./scripts/deploy.sh --regenerate
./scripts/stop.sh && docker compose -f production/production.yaml up -d

# 2. Copy backup files from host to container (if backups are on host)
docker cp production/backups/erp.example.com-2024-09-15-1200.sql.gz \
  $(docker compose -f production/production.yaml ps -q backend):/tmp/

# 3. Restore data (if schema already changed)
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com restore /tmp/erp.example.com-2024-09-15-1200.sql.gz
# Note: If prompted for MySQL root password, use the DB_PASSWORD from production/production.env

# 4. Reapply files if needed
docker cp production/backups/erp.example.com-2024-09-15-1200-files.tar.gz \
  $(docker compose -f production/production.yaml ps -q backend):/tmp/
docker compose -f production/production.yaml exec backend \
  tar -xzf /tmp/erp.example.com-2024-09-15-1200-files.tar.gz -C /home/frappe/frappe-bench/sites/
```

- The backup script keeps copies on the Docker host when `--auto-copy` is used—document the host path for on-call engineers.
- After rollback, note the incident in your changelog and keep staging up until a fixed build is ready.

### Operational hygiene checklist

- ✅ Backups verified in the last 7 days
- ✅ Security patches applied (OS + ERPNext release notes reviewed)
- ✅ Custom app tags mapped to deployed commit SHAs
- ✅ Monitoring + alerting endpoints tested (uptime checks, SMTP alerts, etc.)
- ✅ Runbook stored with credentials/secrets in the team password manager

---

## Troubleshooting

### Site Not Accessible

**Check DNS:**
```bash
dig +short erp.example.com
nslookup erp.example.com
```

**Check Traefik:**
```bash
docker compose -f production/production.yaml logs traefik
```

**Check frontend:**
```bash
docker compose -f production/production.yaml logs frontend
```

### SSL Certificate Issues

**Check Let's Encrypt logs:**
```bash
docker compose -f production/production.yaml logs traefik | grep -i acme
```

**Common causes:**
- DNS not propagated (wait 24-48 hours)
- Ports 80/443 not open
- Rate limit (5 certs/week per domain)

**Test certificate:**
```bash
curl -vI https://erp.example.com 2>&1 | grep -i certificate
```

### Database Connection Failed

**Check MariaDB:**
```bash
docker compose -f production/production.yaml logs mariadb
```

**Test connection:**
```bash
docker compose -f production/production.yaml exec backend \
  mysql -h mariadb-database -u root -p
# Enter DB_PASSWORD from production.env
```

**Common causes:**
- `DB_PASSWORD` mismatch between `production.env` and `mariadb.env`
- `DB_HOST` should be `mariadb-database` (container name)

### Custom App Deployment Issues

**Verify the image really contains your apps:**
```bash
docker compose -f production/production.yaml exec backend bench list-apps
docker compose -f production/production.yaml exec backend cat apps.txt
```

If the app is missing, rebuild the image with the correct `apps.json`, push it, and redeploy.

**Confirm the right image is running:**
```bash
docker compose -f production/production.yaml images | grep backend
grep CUSTOM_TAG production/production.env
```

**Re-apply the app to a site:**
```bash
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com install-app custom_integrations
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com migrate
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build
```

**Integration secrets not picked up?**
- Run `bench --site erp.example.com show-config | grep -i API_KEY` to ensure `set-config` wrote the value.
- Restart background workers if you changed environment variables: `docker compose -f production/production.yaml restart queue-short queue-long scheduler`.

### Service Crash Loops

**Check logs:**
```bash
./scripts/logs.sh <service-name>
```

**Check resources:**
```bash
docker stats
free -h
df -h
```

**Restart:**
```bash
./scripts/stop.sh --all
./scripts/deploy.sh
```

### Performance Issues

**Check worker count:**
```bash
docker ps | grep erpnext-production
```

**Scale workers** (edit `production/production.env`):
```env
WORKERS=4
QUEUE_WORKERS=6
```

Then redeploy:
```bash
./production/scripts/deploy.sh --regenerate  # Regenerate config
./production/scripts/deploy.sh               # Apply changes
```

---

## Security

### 1. Never Commit Secrets

```bash
# Verify .env files are ignored
git check-ignore production/production.env
git check-ignore production/mariadb.env
git check-ignore production/traefik.env

# All should return the filename (means they're ignored)
```

### 2. Use Strong Passwords

```bash
# Always generate with OpenSSL
openssl rand -base64 32  # 32 characters
openssl rand -base64 48  # 48 characters (more secure)
```

### 3. Restrict File Permissions

```bash
chmod 600 production/*.env
chmod 755 production/scripts/*.sh
```

### 4. Enable Firewall

```bash
sudo ufw enable
sudo ufw status
```

### 5. Keep System Updated

```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Docker updates
sudo apt install --only-upgrade docker-ce docker-compose-plugin
```

### Setup Automated Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM with auto-copy and cleanup
0 2 * * * cd /path/to/erp-is-test/production && AUTO_COPY=1 CLEANUP_OLD=1 ./scripts/backup-site.sh erp.example.com

# Weekly encrypted backup
0 3 * * 0 cd /path/to/erp-is-test/production && BACKUP_PASSPHRASE='your-secret' ./scripts/backup-site.sh erp.example.com --encrypt --auto-copy
```

### Backup Encryption

**Setup GPG for backups:**
```bash
# Install GPG (usually pre-installed)
sudo apt install gnupg -y

# Set backup passphrase
export BACKUP_PASSPHRASE='your-very-secure-passphrase'

# Create encrypted backup
./scripts/backup-site.sh erp.example.com --encrypt --auto-copy
```

**Decrypt backups:**
```bash
# Decrypt single file
gpg --decrypt backup-file.gpg > backup-file

# Decrypt with passphrase from environment
echo "$BACKUP_PASSPHRASE" | gpg --batch --passphrase-fd 0 --decrypt file.gpg > file

# Decrypt all .gpg files in directory
for f in *.gpg; do gpg --decrypt "$f" > "${f%.gpg}"; done
```

### Backup Monitoring

**Check backup status:**
```bash
# View backup logs
tail -f /tmp/erpnext-backup-$(date +%Y%m%d).log

# List backups
ls -lah ./backups/

# Verify backup integrity
./scripts/backup-site.sh erp.example.com --debug
```

### 7. Monitor Logs

```bash
# Setup log rotation
sudo nano /etc/logrotate.d/docker-compose

# Add:
/path/to/erp-is/production/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
}
```

### 8. Backup Your Passwords

**Store securely in password manager:**
- Server IP and SSH credentials
- Domain and DNS credentials
- Database passwords (DB_PASSWORD)
- Admin password (ADMIN_PASSWORD)
- Traefik dashboard password
- Backup encryption passphrase
- SSL certificate information

### Environment Variables Reference

**Global Script Variables:**
```bash
# Project configuration
PROJECT_NAME=erpnext-production           # Docker project name
BACKUP_RETENTION_DAYS=30                  # Backup retention period

# Backup script variables
AUTO_COPY=1                               # Auto-copy to host
CLEANUP_OLD=1                             # Auto-cleanup old backups
BACKUP_PASSPHRASE='your-secret'           # GPG encryption passphrase
DEBUG=1                                   # Enable debug output

# Usage example
AUTO_COPY=1 CLEANUP_OLD=1 DEBUG=1 ./scripts/backup-site.sh erp.example.com
```

**Backup Environment Variables:**
```bash
# Set persistent environment variables
echo 'export BACKUP_PASSPHRASE="your-secure-passphrase"' >> ~/.bashrc
echo 'export AUTO_COPY=1' >> ~/.bashrc
echo 'export CLEANUP_OLD=1' >> ~/.bashrc
source ~/.bashrc

# Now backups are simpler
./scripts/backup-site.sh erp.example.com --encrypt
```

---

## Environment Files Explained

### Why Three Files?

Different Docker Compose projects use different files:

1. **Traefik project** → `traefik.env`
   - Reverse proxy configuration
   - SSL certificate management
   - Dashboard access

2. **MariaDB project** → `mariadb.env`
   - Database root password
   - Shared across all ERPNext instances

3. **ERPNext project** → `production.env`
   - Application configuration
   - Database connection
   - Redis configuration
   - Admin password

### Critical: DB Password Must Match

```env
# production.env
DB_PASSWORD=Q2f7k9Lm3nP5rT8wX1zC4vB6hJ0yN2sA

# mariadb.env
DB_PASSWORD=Q2f7k9Lm3nP5rT8wX1zC4vB6hJ0yN2sA  # ← MUST BE SAME!
```

If different, ERPNext cannot connect to database.

---

## Architecture Explained

### Image Sources

This setup uses **official Frappe Docker images**:

```yaml
# Your fork provides:
- Infrastructure: compose.yaml, deployment scripts
- Custom app tooling: apps.json manifest, image overrides, site automation

# Frappe provides:
- Container images: frappe/erpnext, frappe/frappe
- Base configurations: upstream compose files
```

**Image pull locations:**
```bash
# From Docker Hub (official Frappe images)
frappe/erpnext:v15.82.1
frappe/frappe:v15.82.1
library/mariadb:11.8
library/redis:alpine
traefik:v2.11
```

**You maintain:**
- `production/` directory (deployment scripts, configs)
- `apps.json` (or CI secrets) describing the custom/third-party apps you ship
- `.gitignore` (excludes *.env files)

**You track upstream:**
- `compose.yaml` (base infrastructure)
- `overrides/compose.*.yaml` (feature overlays)
- `images/*/Containerfile` (if you need custom builds)

### Why This Approach?

**Benefits:**
- ✅ Get official, tested ERPNext images
- ✅ Receive infrastructure updates from frappe_docker
- ✅ Keep your custom apps and integrations isolated from infrastructure changes
- ✅ Easy to merge upstream improvements
- ✅ Only rebuild images when you really need additional apps or dependencies

**When you'd build custom images:**
- Need to modify Python dependencies
- Add system packages to containers
- Install or update custom/third-party Frappe apps


---

## Support

- **ERPNext Forum**: https://discuss.erpnext.com/
- **Documentation**: https://docs.erpnext.com/
- **Upstream Repository**: https://github.com/frappe/frappe_docker
- **GitHub Issues**: https://github.com/frappe/frappe_docker/issues

---

**Tested With**: ERPNext v15.82.1, Docker 24.0+, Ubuntu 22.04 LTS  
**Script Optimization**: 35% reduction in code, 100% help coverage  
**Last Updated**: October 2025