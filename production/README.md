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
│   ├── customizations/     # Brand customizations (CSS, favicon, logo)
│   │   ├── custom.css
│   │   ├── favicon.ico
│   │   └── logo.png
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

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
- [Script Usage Guide](#script-usage-guide)
- [Branding Customization](#branding-customization)
- [Common Operations](#common-operations)
- [Update Procedures](#update-procedures)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Architecture Explained](#architecture-explained)
- [Script Optimizations](#script-optimizations)

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

# Advanced backup with files, auto-copy, cleanup
./scripts/backup-site.sh erp.example.com --with-files --auto-copy --cleanup-old

# Encrypted backup
BACKUP_PASSPHRASE='your-secret' ./scripts/backup-site.sh erp.example.com --encrypt --auto-copy

# Automated (environment variables)
AUTO_COPY=1 CLEANUP_OLD=1 ./scripts/backup-site.sh erp.example.com
```

**Backup Features:**
- **Encryption**: GPG symmetric encryption with AES256
- **Auto-copy**: Copy backups from container to host `./backups/`
- **Cleanup**: Remove old backups (configurable retention)
- **Validation**: Verify backup files and sizes
- **Logging**: Detailed operation logs in `/tmp/`

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
```

### Access Your Site

1. Open browser: `https://erp.example.com`
2. Username: `Administrator`
3. Password: Check `production/production.env` → `ADMIN_PASSWORD`

---

## Branding Customization

### Overview

Customize your ERPNext instance with your company's brand identity including favicon, logo, colors, and styling. This section provides **manual procedures** for applying branding changes.

### Step 1: Prepare Customization Assets

#### Create Directory Structure

```bash
mkdir -p production/customizations
cd production/customizations
```

#### Prepare Your Files

You'll need:
- **favicon.ico** - Browser tab icon (16x16, 32x32, 48x48 px)
- **favicon.png** - Modern browser icon (192x192 px recommended)
- **logo.png** - Company logo (any size, PNG with transparency recommended)
- **custom.css** - Brand colors and styling overrides

#### Generate Favicon from Logo (Optional)

If you have a logo and need to create favicons:

```bash
# Install ImageMagick
sudo apt install imagemagick -y

# Generate multiple sizes
convert your-logo.png -resize 16x16 favicon-16.ico
convert your-logo.png -resize 32x32 favicon-32.ico
convert your-logo.png -resize 48x48 favicon.ico
convert your-logo.png -resize 192x192 favicon.png

# Or use online tool: https://realfavicongenerator.net/
```

### Step 2: Create Custom CSS

Create `production/customizations/custom.css`:

```css
/* Brand Color Scheme */
:root {
    --primary: #1a365d;        /* Primary brand color (navbar, buttons) */
    --secondary: #2c5282;      /* Secondary brand color */
    --accent: #3182ce;         /* Accent color (links, hover states) */
    --text-on-primary: #ffffff; /* Text color on primary background */
}

/* Apply primary color to navbar */
.navbar {
    background-color: var(--primary) !important;
}

.navbar .navbar-brand,
.navbar .nav-link {
    color: var(--text-on-primary) !important;
}

/* Primary buttons */
.btn-primary {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
}

.btn-primary:hover {
    background-color: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* Links */
a {
    color: var(--accent) !important;
}

a:hover {
    color: var(--primary) !important;
}

/* Hide "Powered by ERPNext" footer */
.footer-powered {
    display: none !important;
}

/* Login page branding */
.login-content {
    background-color: #f7fafc;
}

.login-content .card {
    border: 1px solid var(--primary);
}
```

**Customize the colors:**
- Replace `#1a365d`, `#2c5282`, `#3182ce` with your brand colors
- Use a color picker to get hex codes from your logo

### Step 3: Configure Docker Volume Mounts

Add volume mounts to `production/production.yaml` to inject your customizations.

**Option A: Edit production.yaml directly** (regenerate will overwrite)

```bash
nano production/production.yaml
```

Find the `backend` service and add under `volumes:`:

```yaml
services:
  backend:
    volumes:
      # ... existing volumes ...
      - ./customizations/custom.css:/home/frappe/frappe-bench/sites/assets/custom.css:ro
      - ./customizations/favicon.ico:/home/frappe/frappe-bench/sites/assets/favicon.ico:ro
      - ./customizations/favicon.png:/home/frappe/frappe-bench/sites/assets/favicon.png:ro
      - ./customizations/logo.png:/home/frappe/frappe-bench/sites/assets/logo.png:ro
```

Also add to `frontend` service:

```yaml
  frontend:
    volumes:
      # ... existing volumes ...
      - ./customizations/custom.css:/usr/share/nginx/html/assets/custom.css:ro
      - ./customizations/favicon.ico:/usr/share/nginx/html/assets/favicon.ico:ro
      - ./customizations/favicon.png:/usr/share/nginx/html/assets/favicon.png:ro
      - ./customizations/logo.png:/usr/share/nginx/html/assets/logo.png:ro
```

**Option B: Create compose.custom.yaml overlay** (recommended, survives regeneration)

Create `production/compose.custom.yaml`:

```yaml
services:
  backend:
    volumes:
      - ./customizations/custom.css:/home/frappe/frappe-bench/sites/assets/custom.css:ro
      - ./customizations/favicon.ico:/home/frappe/frappe-bench/sites/assets/favicon.ico:ro
      - ./customizations/favicon.png:/home/frappe/frappe-bench/sites/assets/favicon.png:ro
      - ./customizations/logo.png:/home/frappe/frappe-bench/sites/assets/logo.png:ro

  frontend:
    volumes:
      - ./customizations/custom.css:/usr/share/nginx/html/assets/custom.css:ro
      - ./customizations/favicon.ico:/usr/share/nginx/html/assets/favicon.ico:ro
      - ./customizations/favicon.png:/usr/share/nginx/html/assets/favicon.png:ro
      - ./customizations/logo.png:/usr/share/nginx/html/assets/logo.png:ro
```

Then modify `scripts/deploy.sh` to include this overlay during generation (search for the `docker compose` command that generates production.yaml).

### Step 4: Apply Volume Mounts

```bash
# Restart services to mount new files
docker compose -f production/production.yaml restart backend frontend

# Verify files are mounted
docker compose -f production/production.yaml exec backend \
  ls -la /home/frappe/frappe-bench/sites/assets/

# Should show: custom.css, favicon.ico, favicon.png, logo.png
```

### Step 5: Configure Site to Use Custom Assets

**Method 1: Via Website Settings (Recommended)**

1. Login to ERPNext: `https://erp.example.com`
2. Go to: **Setup → Website Settings**
3. Set the following:
   - **Favicon**: Upload or set path to `/assets/favicon.ico`
   - **Brand HTML**: Add custom logo if needed
   - **Website Theme**: Create custom theme with your colors
   - **Custom HTML**: Add CSS reference if needed

4. Go to: **Setup → System Settings**
   - Upload app icon if needed

**Method 2: Via Bench Commands**

```bash
# Set site config to use custom CSS
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com set-config app_include_css '["/assets/custom.css"]'

# Set favicon
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com set-config app_logo_url '/assets/favicon.png'

# Clear cache and rebuild
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force
```

**Method 3: Via site_config.json**

```bash
# Edit site config directly
docker compose -f production/production.yaml exec backend bash

# Inside container:
cd sites/erp.example.com
nano site_config.json

# Add these lines:
{
  "app_include_css": ["/assets/custom.css"],
  "app_logo_url": "/assets/favicon.png",
  # ... other config ...
}

# Exit and rebuild
exit

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force
```

### Step 6: Verify Branding

```bash
# Clear cache
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

# Rebuild assets
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force

# Restart services
docker compose -f production/production.yaml restart backend frontend
```

**In Browser:**
1. Open `https://erp.example.com`
2. Hard refresh: `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac)
3. Check browser tab for your favicon
4. Verify colors match your brand
5. Check that "Powered by ERPNext" is hidden

### Updating Branding

When you need to update your branding:

```bash
# 1. Edit customization files
nano production/customizations/custom.css
# or replace files:
cp ~/new-logo.png production/customizations/logo.png

# 2. Restart services (mounts are read-only, no rebuild needed)
docker compose -f production/production.yaml restart backend frontend

# 3. Clear cache and rebuild
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force

# 4. Hard refresh browser (Ctrl+Shift+R)
```

### What Gets Customized

✅ **Via File Mounts + CSS:**
- Favicon (browser tab icon)
- Brand colors (navbar, buttons, links)
- Login page styling
- Hide "Powered by ERPNext" footer
- Custom CSS overrides

✅ **Via ERPNext Settings:**
- Website logo (Setup → Website Settings)
- App name (Setup → System Settings)
- Website theme colors
- Custom HTML/CSS includes

### Troubleshooting Branding

**Branding not showing:**

```bash
# 1. Check files exist
ls -la production/customizations/

# 2. Check files are mounted
docker compose -f production/production.yaml exec backend \
  ls -la /home/frappe/frappe-bench/sites/assets/

# 3. Check site config
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com show-config | grep -i css

# 4. Force rebuild
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force

# 5. Restart services
docker compose -f production/production.yaml restart backend frontend
```

**CSS not applied:**

```bash
# Verify CSS is loaded (check browser console)
# Should see: /assets/custom.css

# If not, set in site_config.json:
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com set-config app_include_css '["/assets/custom.css"]'
```

**Favicon not showing:**

```bash
# Set favicon URL
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com set-config app_logo_url '/assets/favicon.png'

# Or via Website Settings in UI
```

### Advanced: Custom Frappe App for Branding

For complex branding needs, create a custom Frappe app:

```bash
# Inside backend container
docker compose -f production/production.yaml exec backend bash

# Create custom app
cd /home/frappe/frappe-bench
bench new-app custom_theme

# Add your customizations to:
# apps/custom_theme/custom_theme/public/css/
# apps/custom_theme/custom_theme/public/js/

# Install app to site
bench --site erp.example.com install-app custom_theme

# Exit container
exit
```

This approach is recommended for:
- Complex UI changes
- Multiple sites with different branding
- Custom JavaScript functionality
- Version-controlled branding

---

## Common Operations

### Backup Site

```bash
# Basic backup
./scripts/backup-site.sh erp.example.com

# Advanced backup with files and auto-copy
./scripts/backup-site.sh erp.example.com --with-files --auto-copy

# Encrypted backup with cleanup
BACKUP_PASSPHRASE='your-secret' ./scripts/backup-site.sh erp.example.com \
  --encrypt --auto-copy --cleanup-old
```

**Backup Features:**
- **Database + Files**: Use `--with-files` to include uploaded files
- **Auto-copy**: `--auto-copy` copies backups to host `./backups/` directory
- **Encryption**: `--encrypt` with GPG AES256 (requires `BACKUP_PASSPHRASE`)
- **Cleanup**: `--cleanup-old` removes backups older than `BACKUP_RETENTION_DAYS`
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
```

# Follow logs (live)
./production/scripts/logs.sh -f backend
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

# Apply branding to new site (manual steps)
# 1. Set CSS include
docker compose -f production/production.yaml exec backend \
  bench --site erp2.example.com set-config app_include_css '["/assets/custom.css"]'

# 2. Set logo/favicon
docker compose -f production/production.yaml exec backend \
  bench --site erp2.example.com set-config app_logo_url '/assets/favicon.png'

# 3. Build and clear cache
docker compose -f production/production.yaml exec backend \
  bench --site erp2.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp2.example.com build --force
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

3. **Customization Layer** (Your Branding)
   - Custom CSS, logos, favicon
   - Your deployment scripts
   - **Updates via**: Editing files in `production/customizations/`

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

### Update Branding

**What this updates**: Your custom CSS, logos, favicon

```bash
# 1. Edit customization files
nano production/customizations/custom.css
# or replace:
cp ~/new-logo.png production/customizations/logo.png

# 2. Restart services to mount new files
docker compose -f production/production.yaml restart backend frontend

# 3. Clear cache and rebuild
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force

# 4. Clear browser cache (Ctrl+Shift+R)
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

# 7. Rebuild branding and cache
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force
```

### Scheduled Maintenance Window

**Recommended schedule:**

```bash
# Monthly: Infrastructure updates
# - Review frappe_docker upstream changes
# - Merge if stability improvements available
# - Test in staging first

# Quarterly: ERPNext version updates
# - Check release notes: https://erpnext.com/version-15
# - Backup before upgrading
# - Update during low-traffic period

# As needed: Branding updates
# - No downtime required
# - Can be done anytime
```

### Rollback Procedures

**If update fails:**

```bash
# 1. Restore from backup
# (Backup is in sites/SITENAME/private/backups/ or ./backups/)

# 2. Revert version in production.env
nano production/production.env
# Change back to previous version

# 3. Regenerate and redeploy
./scripts/deploy.sh --regenerate
./scripts/stop.sh
docker compose -f production/production.yaml up -d

# 4. Restore database backup
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com restore /path/to/backup/database.sql.gz
```

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

### Branding Not Applied

**Check files exist:**
```bash
ls -la production/customizations/
# Should show: custom.css, favicon.ico, favicon.png, logo.png
```

**Check mounts:**
```bash
docker compose -f production/production.yaml exec backend \
  ls -la /home/frappe/frappe-bench/sites/assets/
```

**Reapply branding manually:**
```bash
# 1. Verify volume mounts in production.yaml
grep -A5 "customizations" production/production.yaml

# 2. Restart services
docker compose -f production/production.yaml restart backend frontend

# 3. Set CSS and favicon in site config
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com set-config app_include_css '["/assets/custom.css"]'

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com set-config app_logo_url '/assets/favicon.png'

# 4. Clear cache and rebuild
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache

docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com build --force
```

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
- Customizations: production/customizations/, branding

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
- `production/customizations/` (branding files)
- `.gitignore` (excludes *.env files)

**You track upstream:**
- `compose.yaml` (base infrastructure)
- `overrides/compose.*.yaml` (feature overlays)
- `images/*/Containerfile` (if you need custom builds)

### Why This Approach?

**Benefits:**
- ✅ Get official, tested ERPNext images
- ✅ Receive infrastructure updates from frappe_docker
- ✅ Keep your customizations separate
- ✅ Easy to merge upstream improvements
- ✅ No need to rebuild images for simple branding

**When you'd build custom images:**
- Need to modify Python dependencies
- Add system packages to containers
- Install custom Frappe apps (beyond branding)

---

## Script Optimizations

All automation scripts have been significantly optimized for better performance, maintainability, and user experience.

### 📊 Optimization Results

| Script | Before | After | Reduction | Features Added |
|--------|--------|-------|-----------|----------------|
| **backup-site.sh** | 469 lines | 224 lines | **52%** | Help, encryption, validation |
| **create-site.sh** | 118 lines | 96 lines | **19%** | Help, better prompts |
| **deploy.sh** | 287 lines | 156 lines | **46%** | Help, cleaner output |
| **logs.sh** | 106 lines | 65 lines | **39%** | Help, menu interface |
| **stop.sh** | 85 lines | 68 lines | **20%** | Help, --all option |
| **validate-env.sh** | 238 lines | 241 lines | **+1%** | Help (already optimal) |
| **TOTAL** | **1,303** | **850** | **35%** | **100% help coverage** |

### 🚀 Key Improvements

**1. Comprehensive Help System**
```bash
# Every script now has detailed help
./scripts/deploy.sh --help
./scripts/backup-site.sh -h
./scripts/logs.sh --help
```

**2. Condensed Code Structure**
- One-liner helper functions
- Compact conditional statements
- DRY (Don't Repeat Yourself) principles
- Smart use of bash shortcuts

**3. Enhanced Backup Features**
- **GPG Encryption**: AES256 symmetric encryption
- **Auto-copy**: Container → host backup transfer
- **Cleanup**: Automated old backup removal
- **Validation**: File verification and size reporting
- **Logging**: Detailed operation logs

**4. Interactive Log Viewer**
- Menu-driven service selection
- Support for both numbers (1-7) and names
- Real-time log following
- Clear service descriptions

**5. Smart Deployment**
- Built-in validation before deployment
- Cleaner progress output
- Helper functions for repetitive tasks
- Better error handling

**6. Improved Stop Script**
- Selective service stopping
- `--all` flag for automation
- Interactive confirmation for dependencies

### 📝 Technical Details

**Before (verbose):**
```bash
echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

if [ -z "$SITE_NAME" ]; then
    echo_error "Site name cannot be empty"
    exit 1
fi
```

**After (lean):**
```bash
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

[[ -z "$SITE_NAME" ]] && { echo_error "Site name cannot be empty"; exit 1; }
```

**Result:** 60% fewer lines with identical functionality.

### 🛡️ Maintained Compatibility

✅ **All original functionality preserved**  
✅ **Same command-line interfaces**  
✅ **No breaking changes**  
✅ **Enhanced error handling**  
✅ **Better user experience**

For detailed optimization information, see: `scripts/OPTIMIZATION_SUMMARY.md`

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