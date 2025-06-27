# Local Testing Guide for Pre-built Images

This guide explains how to run the Academy LMS stack locally using images from GitHub Container Registry.

## Prerequisites

1. Docker and Docker Compose installed
2. Access to the GitHub Container Registry (for private images)

## Quick Start

### 1. Clone this repository

```bash
git clone https://github.com/ExarLabs/academy_docker.git
cd academy_docker
```

### 2. Set up environment variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your actual values
nano .env
```

**Required variables to update:**
- `MARIADB_ROOT_PASSWORD` - Set a secure password
- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key (optional)
- `LANGCHAIN_DB_PASSWORD` - Password for LangChain database

### 3. Login to GitHub Container Registry (if images are private)

```bash
# Using GitHub Personal Access Token
echo $GITHUB_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Or using GitHub CLI
gh auth token | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 4. Pull and run the services

```bash
# Pull the latest images
docker compose pull

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5. Create your first site (after services are running)

```bash
# Create a new site
docker compose exec backend bench new-site academy.local \
  --admin-password admin \
  --db-root-password $MARIADB_ROOT_PASSWORD

# Install the LMS app
docker compose exec backend bench --site academy.local install-app lms

# Install the AI Tutor Chat app
docker compose exec backend bench --site academy.local install-app academy_ai_tutor_chat

# Set the site as default
docker compose exec backend bench use academy.local
```

### 6. Access the application

1. Add to your hosts file:
   - Windows: `C:\Windows\System32\drivers\etc\hosts`
   - Linux/Mac: `/etc/hosts`
   
   Add this line:
   ```
   127.0.0.1 academy.local
   ```

2. Open in browser: http://academy.local

## What's included?

The `compose.yaml` file includes:
- **Frappe/ERPNext** with Academy LMS and AI Tutor apps (single image: `ghcr.io/exarlabs/ignis-academy-lms`)
- **LangChain service** for AI functionality (image: `ghcr.io/exarlabs/academy-langchain`)
- **MariaDB** for Frappe database
- **PostgreSQL** for LangChain database
- **Redis** for caching and queues
- **Nginx** reverse proxy

## Troubleshooting

### "manifest unknown" error

This means the image hasn't been built yet. Either:
1. Wait for GitHub Actions to build and push the images
2. Build locally (see development guide)

### Environment variable warnings

Ensure your `.env` file exists and contains all required variables. Use `.env.example` as reference.

### Cannot access the site

1. Check if all services are running: `docker compose ps`
2. Ensure you've added the hostname to your hosts file
3. Check nginx logs: `docker compose logs nginx-proxy`

### Database connection errors

1. Ensure MariaDB is fully started before creating sites
2. Check the password in `.env` matches what you use in commands

## Stopping the services

```bash
# Stop all services
docker compose down

# Stop and remove all data (careful!)
docker compose down -v
```

## Next Steps

- For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)
- For development setup, see [README.md](README.md)
- For environment configuration, see [docs/environment-secrets-explained.md](docs/environment-secrets-explained.md)
