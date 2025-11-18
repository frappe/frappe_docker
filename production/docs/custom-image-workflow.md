# Building Custom ERPNext Images for Production

**Production-Grade Workflow for Third-Party and Custom Apps**

This guide covers the **Pattern 2 (Gold Standard)** approach: building immutable Docker images with custom apps and pre-compiled assets. This is the recommended method for production deployments.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Real-World Example: India Compliance](#real-world-example-india-compliance)
6. [Adding Custom Apps](#adding-custom-apps)
7. [Updating Apps](#updating-apps)
8. [Uninstall Apps](#uninstall-apps)
9. [Deployment Workflow](#deployment-workflow)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

### What This Achieves

- ✅ **True Immutability**: Apps frozen at specific versions (tags/commits)
- ✅ **Zero Runtime Builds**: No `bench build` needed in production
- ✅ **No Asset Sync**: All containers have identical `/apps/` trees
- ✅ **Fast Deployments**: Pull image → deploy → activate on sites
- ✅ **Reliable Rollbacks**: Switch image tags instantly
- ✅ **Audit Trail**: Image tag = exact code deployed

### When to Use This Method

- ✅ Production environments
- ✅ Need reproducible deployments
- ✅ Regulatory compliance required
- ✅ Apps change weekly/monthly (not daily)
- ✅ Want reliable rollbacks

### Key Difference from Runtime Install (Pattern 3)

| Aspect | Pattern 3 (Runtime) | Pattern 2 (This Guide) |
|--------|---------------------|------------------------|
| Apps installed | At runtime with `bench get-app` | Baked into image at build time |
| Assets compiled | `bench build` in production | Pre-compiled during image build |
| Asset sync | Manual `tar` pipeline required | Not needed - assets in image |
| Immutability | Partial (apps can drift) | Complete (frozen versions) |
| Rollback | Complex | Change image tag |

---

## Prerequisites

### Required Tools

```bash
# Verify Docker is installed
docker --version  # Need 20.10+

# Verify git is available
git --version

# Verify you have base64
base64 --version
```

### GitHub Container Registry Access

1. Create Personal Access Token:
   - Go to: https://github.com/settings/tokens/new
   - Select scope: `write:packages`
   - Generate token and save it securely

2. Login to GitHub Container Registry:
   ```bash
   export GITHUB_TOKEN=your_token_here
   echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   ```

3. Verify login:
   ```bash
   docker pull ghcr.io/YOUR_USERNAME/test || echo "Ready to push"
   ```

---

## Quick Start

**5-minute walkthrough** for experienced users:

```bash
# 1. Define apps with pinned versions (custom apps only)
cat > production/apps.json <<EOF
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "v15.88.1"
  },
  {
    "url": "https://github.com/resilient-tech/india-compliance",
    "branch": "v15.23.2"
  }
]
EOF

# 2. Build immutable image
export APPS_JSON_BASE64=$(base64 -w0 production/apps.json)
BUILD_TAG="ghcr.io/YOUR_USERNAME/erpnext-custom:$(date +%Y%m%d)-$(git rev-parse --short HEAD)"

docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=v15.88.1 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=$BUILD_TAG \
  --tag=ghcr.io/YOUR_USERNAME/erpnext-custom:production-latest \
  --file=images/layered/Containerfile .

# 3. Push to registry
docker push $BUILD_TAG
docker push ghcr.io/YOUR_USERNAME/erpnext-custom:production-latest

# 4. Update production config
nano production/production.env
# Set: CUSTOM_TAG=20251118-4c860c6

# 5. Deploy
./scripts/deploy.sh --regenerate
./scripts/deploy.sh

# 6. Activate apps on sites
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost install-app india_compliance

docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost migrate
```

---

## Step-by-Step Guide

### Step 1: Find App Versions

**Goal**: Pin exact versions for immutability

#### For Third-Party Apps (GitHub)

```bash
# Find latest stable tags
curl -s https://api.github.com/repos/frappe/erpnext/tags | grep '"name"' | head -5
curl -s https://api.github.com/repos/resilient-tech/india-compliance/tags | grep '"name"' | head -5

# For Frappe Framework (use as FRAPPE_BRANCH build arg)
curl -s https://api.github.com/repos/frappe/frappe/tags | grep '"name"' | head -5

# Or browse tags on GitHub:
# https://github.com/frappe/frappe/tags
# https://github.com/frappe/erpnext/tags
# https://github.com/resilient-tech/india-compliance/tags
```

**Example output**:
```json
"name": "v15.88.1",  ← Use this specific tag
"name": "v15.88.0",
"name": "v15.87.2",
```

#### For Custom Apps (Your Repository)

```bash
# Tag your custom app first
cd /path/to/your/custom-app
git tag v1.0.0
git push origin v1.0.0

# Or use specific commit
git log --oneline -5
# abc1234 Fix invoice bug  ← Use this commit hash
```

### Step 2: Create apps.json with Pinned Versions

**Location**: `production/apps.json`

**Bad Example** (not immutable):
```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"  ← WRONG: Moving target!
  }
]
```

**Good Example** (immutable):
```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "v15.88.1"  ← CORRECT: Frozen version
  },
  {
    "url": "https://github.com/resilient-tech/india-compliance",
    "branch": "v15.23.2"  ← Specific tag
  },
  {
    "url": "https://github.com/YOUR_ORG/custom-hrms-integration",
    "branch": "v2.1.0"  ← Your custom app
  }
]
```

**Using Commit Hashes** (even more precise):
```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15",
    "commit": "a1b2c3d4e5f6"  ← Exact commit
  }
]
```

**Edit the file**:
```bash
nano production/apps.json
```

**Important**: \n- **Do NOT include Frappe Framework in apps.json** - it's controlled via `FRAPPE_BRANCH` build arg\n- The upstream Containerfile expects Frappe via build args, not in apps.json\n- Only include custom/third-party apps (ERPNext, india_compliance, HRMS, etc.)\n- Use specific tags for immutability\n\n### Step 3: Build the Immutable Image

**Generate unique image tag**:
```bash
# Components of the tag
BUILD_DATE=$(date +%Y%m%d)           # 20251118
GIT_SHA=$(git rev-parse --short HEAD) # 4c860c6
USERNAME="duthink"  # Your GitHub username

# Full image tags
IMAGE_TAG="ghcr.io/${USERNAME}/erpnext-custom:${BUILD_DATE}-${GIT_SHA}"
IMAGE_LATEST="ghcr.io/${USERNAME}/erpnext-custom:production-latest"

echo "Will create tags:"
echo "  Specific: $IMAGE_TAG"
echo "  Latest:   $IMAGE_LATEST"
```

**Encode apps.json**:
```bash
export APPS_JSON_BASE64=$(base64 -w0 production/apps.json)

# Verify it worked
echo "Base64 encoded (first 50 chars): ${APPS_JSON_BASE64:0:50}..."
```

**Build the image**:
```bash
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=v15.88.1 \
  --build-arg=PYTHON_VERSION=3.11.6 \
  --build-arg=NODE_VERSION=18.18.2 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=$IMAGE_TAG \
  --tag=$IMAGE_LATEST \
  --file=images/layered/Containerfile \
  .
```

**What happens during build** (10-15 minutes):
1. Installs Frappe Framework v15.88.1 (from FRAPPE_BRANCH arg)
2. Installs all custom apps from `apps.json`
3. Installs Python dependencies
4. Installs Node.js dependencies
5. **Runs `bench build`** (compiles all assets!)
6. Creates final image with everything baked in

**Verify build success**:
```bash
# Check images exist
docker images | grep erpnext-custom

# Expected output:
# ghcr.io/duthink/erpnext-custom  20251118-4c860c6    e3768a4d428a  1.5GB
# ghcr.io/duthink/erpnext-custom  production-latest   e3768a4d428a  1.5GB
```

### Step 4: Push to Registry

**Push both tags**:
```bash
# Push specific version (immutable)
docker push ghcr.io/${USERNAME}/erpnext-custom:${BUILD_DATE}-${GIT_SHA}

# Push latest (convenience pointer)
docker push ghcr.io/${USERNAME}/erpnext-custom:production-latest
```

**Note**: The second push is instant (just updates the tag pointer, no re-upload).

**Verify on GitHub**:
1. Go to: https://github.com/YOUR_USERNAME?tab=packages
2. Find `erpnext-custom`
3. Check both tags exist

### Step 5: Update Production Configuration

**Edit production environment**:
```bash
nano production/production.env
```

**Update these lines**:
```env
# Custom Image Configuration
CUSTOM_IMAGE=ghcr.io/duthink/erpnext-custom
CUSTOM_TAG=20251118-4c860c6  # Use your BUILD_DATE-GIT_SHA
PULL_POLICY=always
```

**Why not use `production-latest`?**
- Production needs **specific, immutable tags**
- `production-latest` moves when you push new images
- Specific tags enable reliable rollbacks

### Step 6: Deploy the New Image

**Regenerate production.yaml**:
```bash
./scripts/deploy.sh --regenerate
```

**What this does**:
- Merges base `compose.yaml` with overlays
- Injects your `CUSTOM_IMAGE` and `CUSTOM_TAG`
- Generates `production/production.yaml`

**Deploy to production**:
```bash
./scripts/deploy.sh
```

**What this does**:
1. Validates configuration
2. Deploys Traefik (if not running)
3. Deploys MariaDB (if not running)
4. **Pulls new image** from registry
5. Recreates containers with new image
6. Starts all services

**Verify deployment**:
```bash
# Check all containers use new image
docker compose -f production/production.yaml images

# Expected output:
# CONTAINER        IMAGE                                             
# backend          ghcr.io/duthink/erpnext-custom:20251118-4c860c6
# frontend         ghcr.io/duthink/erpnext-custom:20251118-4c860c6
# queue-short      ghcr.io/duthink/erpnext-custom:20251118-4c860c6
# ...
```

### Step 7: Activate Apps on Sites

**Important**: Apps are in the image, but not yet active on your sites.

**Install app on existing site**:
```bash
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost install-app india_compliance
```

**Run migrations**:
```bash
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost migrate
```

**That's it!** No `bench build` or asset sync needed. Assets are already compiled and present in all containers.

**Verify it works**:
```bash
# Check app is installed
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost list-apps

# Expected output:
# frappe 15.88.2
# erpnext 15.88.1
# india_compliance 15.23.2

# Test the site
curl -k -I https://erp.localhost/app/home
# Should return: HTTP/2 200
```

---

## Real-World Example: India Compliance

### Complete Workflow from Scratch

```bash
# 1. Check current stable version
curl -s https://api.github.com/repos/resilient-tech/india-compliance/tags | grep '"name"' | head -3
# Output: "name": "v15.23.2"

# 2. Create apps.json (custom apps only - NOT Frappe)
cat > production/apps.json <<EOF
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "v15.88.1"
  },
  {
    "url": "https://github.com/resilient-tech/india-compliance",
    "branch": "v15.23.2"
  }
]
EOF

# 3. Build image
export APPS_JSON_BASE64=$(base64 -w0 production/apps.json)
BUILD_DATE=$(date +%Y%m%d)
GIT_SHA=$(git rev-parse --short HEAD)

docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=v15.88.1 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/duthink/erpnext-custom:${BUILD_DATE}-${GIT_SHA} \
  --tag=ghcr.io/duthink/erpnext-custom:production-latest \
  --file=images/layered/Containerfile .

# Takes 10-15 minutes...

# 4. Push to registry
docker push ghcr.io/duthink/erpnext-custom:${BUILD_DATE}-${GIT_SHA}
docker push ghcr.io/duthink/erpnext-custom:production-latest

# 5. Update production config
echo "CUSTOM_TAG=${BUILD_DATE}-${GIT_SHA}" >> production/production.env

# 6. Deploy
./scripts/deploy.sh --regenerate
./scripts/deploy.sh

# 7. Activate on site
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost install-app india_compliance

docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost migrate

# 8. Verify
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost list-apps
```

### What You Get

- ✅ India Compliance v15.23.2 installed
- ✅ All GST, TDS, and compliance features available
- ✅ Assets pre-compiled (no 404 errors)
- ✅ Can rollback to previous image anytime
- ✅ Image SHA = exact deployed code

---

## Adding Custom Apps

### Scenario: Add Your Own Frappe App

**1. Prepare your custom app**:
```bash
cd /path/to/your/custom_integrations

# Tag a release
git tag v1.0.0
git push origin v1.0.0

# Or note the commit hash
git log --oneline -1
# abc1234 Add webhook integration
```

**2. Add to apps.json**:
```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "v15.88.1"
  },
  {
    "url": "https://github.com/resilient-tech/india-compliance",
    "branch": "v15.23.2"
  },
  {
    "url": "https://github.com/YOUR_ORG/custom_integrations",
    "branch": "v1.0.0"
  }
]
```

**3. Rebuild image** (same process as above):
```bash
# New image tag reflects new date
BUILD_DATE=$(date +%Y%m%d)  # 20251119
GIT_SHA=$(git rev-parse --short HEAD)

export APPS_JSON_BASE64=$(base64 -w0 production/apps.json)

docker build \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/duthink/erpnext-custom:${BUILD_DATE}-${GIT_SHA} \
  --tag=ghcr.io/duthink/erpnext-custom:production-latest \
  --file=images/layered/Containerfile .

docker push ghcr.io/duthink/erpnext-custom:${BUILD_DATE}-${GIT_SHA}
docker push ghcr.io/duthink/erpnext-custom:production-latest
```

**4. Deploy new image**:
```bash
# Update production config
nano production/production.env
# CUSTOM_TAG=20251119-def5678

./scripts/deploy.sh --regenerate
./scripts/deploy.sh
```

**5. Install on sites**:
```bash
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost install-app custom_integrations

docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost migrate
```

### Private Repositories

**For private GitHub repos**:

```json
[
  {
    "url": "https://YOUR_TOKEN@github.com/YOUR_ORG/private_app",
    "branch": "v1.0.0"
  }
]
```

**Security Note**: Never commit tokens to git! Use environment variables:

```bash
# In CI/CD or local build
export GITHUB_TOKEN=your_token
export APPS_JSON_BASE64=$(cat production/apps.json | sed "s/YOUR_TOKEN/$GITHUB_TOKEN/g" | base64 -w0)
```

---

## Updating Apps

### Scenario: India Compliance Releases v15.24.0

**1. Check for new version**:
```bash
curl -s https://api.github.com/repos/resilient-tech/india-compliance/tags | grep '"name"' | head -3
# New output: "name": "v15.24.0"
```

**2. Update apps.json**:
```bash
nano production/apps.json

# Change:
# "branch": "v15.23.2"  → "branch": "v15.24.0"
```

**3. Rebuild with new tag**:
```bash
export APPS_JSON_BASE64=$(base64 -w0 production/apps.json)
BUILD_DATE=$(date +%Y%m%d)
GIT_SHA=$(git rev-parse --short HEAD)

docker build \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/duthink/erpnext-custom:${BUILD_DATE}-${GIT_SHA} \
  --tag=ghcr.io/duthink/erpnext-custom:production-latest \
  --file=images/layered/Containerfile .

docker push ghcr.io/duthink/erpnext-custom:${BUILD_DATE}-${GIT_SHA}
docker push ghcr.io/duthink/erpnext-custom:production-latest
```

**4. Test in staging first** (recommended):
```bash
# Use production-latest for staging
nano staging/staging.env
# CUSTOM_TAG=production-latest

./scripts/deploy-staging.sh
# Test thoroughly...
```

**5. Deploy to production**:
```bash
nano production/production.env
# CUSTOM_TAG=20251125-xyz9999  # New specific tag

./scripts/deploy.sh --regenerate
./scripts/deploy.sh
```

**6. Migrate sites**:
```bash
docker compose -f production/production.yaml exec backend \
  bench --site erp.localhost migrate
```

**7. Rollback if issues**:
```bash
# Just change to old tag
nano production/production.env
# CUSTOM_TAG=20251118-4c860c6  # Previous working version

./scripts/deploy.sh
# Old image still exists in registry!
```

---

## Deployment Workflow

### Standard Deployment Process

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Update apps.json with pinned versions                   │
│    └─ Commit to git                                         │
│                                                              │
│ 2. Build image                                              │
│    └─ Tag with BUILD_DATE-GIT_SHA                           │
│    └─ Also tag as production-latest                         │
│                                                              │
│ 3. Push to registry                                         │
│    └─ Both tags pushed                                      │
│                                                              │
│ 4. Test (optional but recommended)                          │
│    └─ Pull production-latest in staging                     │
│    └─ Run smoke tests                                       │
│                                                              │
│ 5. Deploy to production                                     │
│    └─ Update CUSTOM_TAG with specific tag                   │
│    └─ Regenerate production.yaml                            │
│    └─ Deploy (pulls new image)                              │
│                                                              │
│ 6. Migrate sites                                            │
│    └─ bench migrate on each site                            │
│                                                              │
│ 7. Monitor                                                  │
│    └─ Check logs                                            │
│    └─ Verify assets load                                    │
│    └─ Test critical features                                │
└─────────────────────────────────────────────────────────────┘
```

### CI/CD Integration (GitHub Actions Example)

```yaml
# .github/workflows/build-image.yml
name: Build ERPNext Custom Image

on:
  push:
    paths:
      - 'production/apps.json'
      - 'images/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to GitHub Container Registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      
      - name: Build image
        run: |
          export APPS_JSON_BASE64=$(base64 -w0 production/apps.json)
          BUILD_DATE=$(date +%Y%m%d)
          GIT_SHA=$(git rev-parse --short HEAD)
          
          docker build \
            --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
            --tag=ghcr.io/${{ github.repository_owner }}/erpnext-custom:${BUILD_DATE}-${GIT_SHA} \
            --tag=ghcr.io/${{ github.repository_owner }}/erpnext-custom:production-latest \
            --file=images/layered/Containerfile .
      
      - name: Push image
        run: |
          BUILD_DATE=$(date +%Y%m%d)
          GIT_SHA=$(git rev-parse --short HEAD)
          
          docker push ghcr.io/${{ github.repository_owner }}/erpnext-custom:${BUILD_DATE}-${GIT_SHA}
          docker push ghcr.io/${{ github.repository_owner }}/erpnext-custom:production-latest
```

---

## Uninstall Apps

When you need to remove an app from a site:

```bash
# 1. Backup first (uninstall deletes DocTypes and data!)
./scripts/backup-site.sh erp.example.com --with-files --auto-copy

# 2. Uninstall from site
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com uninstall-app india_compliance

# 3. Clear cache and restart
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com clear-cache
docker compose -f production/production.yaml restart frontend
```

**Important Notes:**
- The app remains in the image's `/apps/` directory but is deactivated on the site
- No `bench build` or asset sync needed—assets are pre-compiled in the image
- Uninstall permanently deletes all app DocTypes and database records
- Always backup before uninstalling
- To completely remove an app from future deployments: rebuild image without it in `apps.json`

**Complete Removal Workflow:**

If you want to stop deploying an app entirely:

```bash
# 1. Uninstall from all sites first
docker compose -f production/production.yaml exec backend \
  bench --site site1.example.com uninstall-app india_compliance
docker compose -f production/production.yaml exec backend \
  bench --site site2.example.com uninstall-app india_compliance

# 2. Remove from apps.json
nano production/apps.json
# Delete the india_compliance entry

# 3. Rebuild image without the app
export APPS_JSON_BASE64=$(base64 -w0 production/apps.json)
NEW_TAG="ghcr.io/YOUR_USERNAME/erpnext-custom:$(date +%Y%m%d)-$(git rev-parse --short HEAD)"

docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=v15.88.1 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=$NEW_TAG \
  --file=images/layered/Containerfile .

docker push $NEW_TAG

# 4. Update production.env and deploy
nano production/production.env
# CUSTOM_TAG=20251119-newsha

./scripts/deploy.sh --regenerate
./scripts/deploy.sh
```

**Verify Clean State:**
```bash
# Check app is not in image
docker compose -f production/production.yaml exec backend bench list-apps

# Check app is not active on sites
docker compose -f production/production.yaml exec backend \
  bench --site erp.example.com list-apps
```

---

## Troubleshooting

### Issue: Build Fails with "App not found"

**Symptom**:
```
ERROR: Could not find app: india_compliance
```

**Causes**:
- Typo in repository URL
- Branch/tag doesn't exist
- Private repo without authentication

**Solution**:
```bash
# Verify URL and branch exist
curl -I https://github.com/resilient-tech/india-compliance
curl -I https://github.com/resilient-tech/india-compliance/tree/v15.23.2

# Check apps.json syntax
cat production/apps.json | python3 -m json.tool
```

### Issue: Build Fails with "Node modules not found"

**Symptom**:
```
ERROR: Cannot find module 'xyz'
```

**Cause**: Upstream dependency issue in one of the apps

**Solution**:
```bash
# Try building with specific Node version
docker build \
  --build-arg=NODE_VERSION=18.18.2 \
  ...

# Or check app's package.json for required Node version
```

### Issue: Assets Return 404 After Deployment

**Symptom**: CSS/JS files show 404 in browser

**This should NOT happen with Pattern 2**, but if it does:

**Diagnosis**:
```bash
# Verify all containers use same image
docker compose -f production/production.yaml images

# Check if assets exist in image
docker compose -f production/production.yaml exec backend \
  ls /home/frappe/frappe-bench/apps/india_compliance/india_compliance/public/dist

# Check frontend can access them
docker compose -f production/production.yaml exec frontend \
  ls /home/frappe/frappe-bench/apps/india_compliance/india_compliance/public/dist
```

**Solution**: Rebuild image, ensure `bench build` completed during build.

### Issue: Image Size Too Large

**Symptom**: Image is 3+ GB

**Cause**: Includes development dependencies or build cache

**Solution**:
```dockerfile
# Multi-stage builds help (already in images/layered/Containerfile)
# Ensure .dockerignore is present:
cat > .dockerignore <<EOF
.git
.github
node_modules
*.log
development/
docs/
tests/
EOF
```

### Issue: Cannot Push to Registry

**Symptom**:
```
denied: permission_denied
```

**Solutions**:
```bash
# 1. Verify login
docker login ghcr.io -u YOUR_USERNAME

# 2. Check token has write:packages scope
# Go to: https://github.com/settings/tokens

# 3. Ensure repository exists or image name matches your username
# Image must be: ghcr.io/YOUR_USERNAME/image-name
```

---

## Best Practices

### 1. Version Pinning

**Always use specific tags or commits**:
```json
// ✅ GOOD
{"url": "...", "branch": "v15.23.2"}
{"url": "...", "branch": "main", "commit": "abc1234"}

// ❌ BAD
{"url": "...", "branch": "version-15"}
{"url": "...", "branch": "main"}
```

### 2. Image Tagging Strategy

**Use semantic, traceable tags**:
```bash
# Format: YYYYMMDD-GITSHA
20251118-4c860c6  # Date + git commit

# Why?
✅ Chronological ordering
✅ Git traceability
✅ Unique identifier
✅ Easy to find in registry
```

### 3. Keep Old Images

**Don't delete old images immediately**:
```bash
# Keep last 5-10 production images
# Allows rollback window of several months
```

**Cleanup script**:
```bash
# Keep only last 10 tags (manual cleanup)
# Use GitHub Packages retention policies
```

### 4. Document Image Contents

**Tag your git commits when building images**:
```bash
git tag release-20251118-india-compliance-v15.23.2
git push origin release-20251118-india-compliance-v15.23.2
```

**Maintain a changelog**:
```markdown
## 20251118-4c860c6
- Added india_compliance v15.23.2
- Updated erpnext to v15.88.1

## 20251117-abc1234
- Initial production image
- erpnext v15.88.1
```

### 5. Test Before Production

**Always test new images**:
```bash
# Pull latest in staging
docker pull ghcr.io/duthink/erpnext-custom:production-latest

# Run tests
# - Create test site
# - Install apps
# - Run migrations
# - Test critical workflows

# Only promote to production after validation
```

### 6. Automate Builds

**Use CI/CD for consistency**:
- Automatic builds on `apps.json` changes
- Automatic tagging with git SHA
- Automatic push to registry
- Manual approval for production deployment

### 7. Monitor Image Registry

**Set up alerts**:
- Failed builds
- Image size growing unexpectedly
- Old images not being cleaned up

### 8. Security Scanning

**Scan images before production**:
```bash
# Using Trivy (example)
trivy image ghcr.io/duthink/erpnext-custom:20251118-4c860c6

# Fix critical vulnerabilities before deploying
```

---

## Summary

### Key Takeaways

1. **Pin versions** in `apps.json` for true immutability
2. **Build once, deploy many** - assets pre-compiled
3. **Tag with date+sha** for traceability
4. **Push to registry** for reliable distribution
5. **Use specific tags** in production (not `latest`)
6. **Keep old images** for rollback capability
7. **Test in staging** before production
8. **Automate via CI/CD** for consistency

### Workflow Checklist

- [ ] Update `apps.json` with pinned versions
- [ ] Build image with unique tag
- [ ] Push both specific and latest tags
- [ ] Test in staging environment
- [ ] Update `CUSTOM_TAG` in production.env
- [ ] Regenerate production.yaml
- [ ] Deploy to production
- [ ] Migrate sites
- [ ] Monitor and verify
- [ ] Document in changelog

### Next Steps

- Set up CI/CD pipeline for automated builds
- Implement staging environment for testing
- Configure monitoring and alerts
- Document rollback procedures
- Train team on workflow

---

## Additional Resources

- [Main Production README](../README.md)
- [Asset Management Patterns](asset-management-frappe.md)
- [Frappe Docker Documentation](https://github.com/frappe/frappe_docker)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Last Updated**: November 2025  
**Maintainer**: This repository  
**Pattern**: Pattern 2 (Gold Standard - Immutable Images)
