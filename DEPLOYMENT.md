# Academy LMS Deployment Guide

This repository is configured to automatically deploy the Academy LMS stack to Hetzner Cloud, including:
- Frappe Framework with custom Academy LMS app
- AI Tutor Chat application
- LangChain service for AI functionality

## Architecture Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   academy-lms       │     │ academy-ai-tutor    │     │ academy-langchain   │
│   (GitHub Repo)     │     │   (GitHub Repo)     │     │   (GitHub Repo)     │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘
           │                           │                           │
           └───────────────────────────┴───────────────────────────┘
                                       │
                              Webhook Triggers
                                       │
                                       ▼
                        ┌─────────────────────────┐
                        │   academy_docker        │
                        │   (This Repository)     │
                        │                         │
                        │  • Builds Docker images │
                        │  • Pushes to GHCR       │
                        │  • Deploys to Hetzner   │
                        └─────────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   Hetzner Server        │
                        │   188.245.211.114       │
                        │                         │
                        │  Running Services:      │
                        │  • Nginx Proxy          │
                        │  • Frappe Backend       │
                        │  • MariaDB              │
                        │  • Redis                │
                        │  • LangChain Service    │
                        └─────────────────────────┘
```

## Setup Instructions

### 1. Prerequisites

- GitHub account with access to all repositories
- Hetzner server with Docker and Docker Compose installed
- SSH access to the Hetzner server

### 2. Repository Secrets

Configure the following secrets in this repository:

- `ACADEMY_DOCKER_PAT`: GitHub Personal Access Token with `repo` and `write:packages` permissions
  - **IMPORTANT**: This PAT must have access to clone the private `academy-LangChain` repository
  - Create at: https://github.com/settings/tokens/new
  - Required scopes: `repo` (full), `write:packages`
- `HETZNER_SSH_KEY`: Private SSH key for accessing the Hetzner server

For environment variables, you can either:
- Use a `.env` file on the server (default approach)
- Use GitHub Secrets for sensitive values (recommended for production)

If using GitHub Secrets, add these:
- `MARIADB_ROOT_PASSWORD`: Strong password for MariaDB root user
- `OPENAI_API_KEY`: Your OpenAI API key for AI features
- `ANTHROPIC_API_KEY`: Your Anthropic API key (optional)
- `LANGCHAIN_DB_PASSWORD`: Password for LangChain PostgreSQL database

### 3. Webhook Setup

Add the webhook workflow files to each watched repository:

1. **For academy-lms repository:**
   - Copy `.github/workflows/webhook-academy-lms.yml` to the academy-lms repo
   - Add secret `ACADEMY_DOCKER_PAT` with the same PAT

2. **For academy-ai-tutor-chat repository:**
   - Copy `.github/workflows/webhook-academy-ai-tutor.yml` to the academy-ai-tutor-chat repo
   - Add secret `ACADEMY_DOCKER_PAT` with the same PAT

3. **For academy-LangChain repository:**
   - Copy `.github/workflows/webhook-academy-langchain.yml` to the academy-LangChain repo
   - Add secret `ACADEMY_DOCKER_PAT` with the same PAT

### 4. Hetzner Server Setup

1. SSH into your Hetzner server:
   ```bash
   ssh ignis_academy_lms@188.245.211.114
   ```

2. Run the automated setup script:
   ```bash
   # Download and run setup script
   curl -O https://raw.githubusercontent.com/ExarLabs/academy_docker/master/scripts/setup-hetzner.sh
   sudo bash setup-hetzner.sh
   ```

   The script will:
   - Install Docker and Docker Compose
   - Create deployment directory
   - Setup Docker networks
   - Configure firewall rules
   - Create backup directory and cron jobs
   - Setup systemd service for auto-start
   - Install monitoring tools

3. Configure environment:
   ```bash
   # Switch to frappe user
   su - frappe
   cd /opt/frappe-deployment
   
   # Copy .env.example to .env and update with your values
   cp .env.example .env
   nano .env
   ```

   Important variables to update:
   - All passwords (MARIADB_ROOT_PASSWORD, ADMIN_PASSWORD, etc.)
   - OPENAI_API_KEY for AI functionality
   - FRAPPE_SITE_NAME_HEADER with your domain
   - Email configuration if needed

### 5. Initial Deployment

Trigger the deployment manually:

1. Go to Actions tab in this repository
2. Select "Deploy Academy LMS to Hetzner"
3. Click "Run workflow"
4. Optionally check "Force rebuild all images"

### 6. Create Your First Site

After deployment is complete, create your first site:

```bash
ssh ignis_academy_lms@188.245.211.114
cd /opt/frappe-deployment
./scripts/create-site.sh academy.example.com
```

The script will:
- Create a new Frappe site
- Install Academy LMS app
- Install AI Tutor Chat app
- Configure the site
- Run migrations

## Deployment Process

### Automatic Deployment

The system automatically deploys when:

1. **Changes to watched repositories**: Any push to main/master branch triggers deployment
2. **Changes to this repository**: Updates to deployment configuration trigger deployment
3. **Manual trigger**: Use GitHub Actions workflow dispatch

### What Happens During Deployment

1. **Build Phase**:
   - Builds custom Frappe image with Academy LMS and AI Tutor apps
   - Tags and pushes to GitHub Container Registry

2. **Deploy Phase**:
   - Copies deployment files to Hetzner server
   - Pulls latest images
   - Stops existing services gracefully
   - Starts new services
   - Runs database migrations on all sites
   - Performs health check

### Migration Process

The `migrate-all-sites.sh` script automatically:
- Detects all Frappe sites
- Runs `bench migrate` on each site
- Clears cache
- Runs system health check

## Monitoring and Troubleshooting

### Check Service Status

```bash
ssh ignis_academy_lms@188.245.211.114
cd /opt/frappe-deployment
docker compose ps
docker compose logs -f
```

### Manual Migration

If needed, run migrations manually:

```bash
ssh ignis_academy_lms@188.245.211.114
cd /opt/frappe-deployment
./scripts/migrate-all-sites.sh
```

### Common Issues

1. **502 Bad Gateway**: Services are still starting. Wait a few minutes.
2. **Migration Failures**: Check logs with `docker compose logs backend`
3. **Network Issues**: Ensure langchain-network exists: `docker network create langchain-network`

## Security Considerations

1. **Secrets Management**:
   - Never commit `.env` file
   - Use strong passwords
   - Rotate credentials regularly
   - Consider using GitHub Secrets for production deployments

2. **Network Security**:
   - Configure firewall rules on Hetzner
   - Use HTTPS in production (see SSL setup below)

3. **Backup Strategy**:
   - Regular database backups
   - Store backups off-site

### Private Registry Setup

By default, images are pushed to GitHub Container Registry (ghcr.io). To use private images:

1. **Make packages private in GitHub**:
   - Go to your repository settings
   - Navigate to "Packages" in the sidebar
   - Find your package (e.g., `ignis-academy-lms`, `academy-langchain`)
   - Click on "Package settings"
   - Change visibility to "Private"

2. **Enable registry authentication in deployment**:
   - The workflow already includes code for private registry login
   - Uncomment the "Login to private registry" section in `.github/workflows/deploy.yml`
   - The `GITHUB_TOKEN` automatically has `packages:read` permission for private packages in the same org

3. **Manual registry login on Hetzner** (if needed):
   ```bash
   # For GitHub Container Registry
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   
   # Or use a Personal Access Token
   echo $PAT | docker login ghcr.io -u USERNAME --password-stdin
   ```

4. **Alternative private registries**:
   - Docker Hub: Update `REGISTRY` to `docker.io`
   - Harbor: Update `REGISTRY` to your Harbor URL
   - GitLab: Update `REGISTRY` to `registry.gitlab.com`

## SSL/TLS Setup (Production)

For production, set up SSL certificates:

1. Install Certbot on Hetzner server
2. Update nginx configuration for SSL
3. Use compose.custom-domain-ssl.yaml override

## Maintenance

### Updating Dependencies

1. Update Frappe version in `images/custom/Containerfile`
2. Update app versions by triggering rebuild
3. Test in staging before production

### Backup and Restore

```bash
# Backup
docker compose exec backend bench --site academy.example.com backup

# Restore
docker compose exec backend bench --site academy.example.com restore [backup-file]
```

## Support

For issues:
1. Check GitHub Actions logs
2. Review server logs
3. Open issue in this repository
