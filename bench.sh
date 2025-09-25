#!/bin/bash

# Bench wrapper script for Frappe Docker
# This script simplifies running bench commands in the Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PROJECT_NAME=""
COMPOSE_FILE=""
SHOW_HELP=0

# Function to show help
show_help() {
    cat << EOF
Frappe Docker Bench Wrapper Script
===================================

This script simplifies running bench commands in the Frappe Docker container.

Usage:
    ./bench.sh [OPTIONS] [BENCH_COMMAND] [ARGS...]

Options:
    -p, --project NAME      Docker Compose project name
    -f, --file FILE        Docker Compose file to use (default: auto-detect)
    -h, --help             Show this help message

Examples:
    # Create a new site
    ./bench.sh new-site mysite.local --admin-password=admin --install-app erpnext

    # Run bench command on specific site
    ./bench.sh --site mysite.local migrate

    # Use with specific project
    ./bench.sh -p erpnext-prod --site production.local backup

    # List all sites
    ./bench.sh --site all list-apps

    # Get a new app
    ./bench.sh get-app https://github.com/frappe/app_name

    # Install app on site
    ./bench.sh --site mysite.local install-app app_name

    # Update bench
    ./bench.sh update --pull --apps

    # Set admin password
    ./bench.sh --site mysite.local set-admin-password newpassword

Common Commands:
    new-site        Create a new site
    backup          Backup a site
    restore         Restore a site from backup
    migrate         Run migrations
    list-apps       List installed apps
    install-app     Install an app on a site
    uninstall-app   Uninstall an app from a site
    get-app         Download an app
    update          Update bench and apps
    console         Open Python console
    mariadb         Open MariaDB console
    redis-cache     Open Redis cache console
    redis-queue     Open Redis queue console

Note: For new-site with MariaDB, you may need to add:
      --mariadb-user-host-login-scope=% --db-root-password=<password>

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            SHOW_HELP=1
            shift
            ;;
        *)
            # Stop parsing options when we hit bench commands
            break
            ;;
    esac
done

# Show help if requested
if [ $SHOW_HELP -eq 1 ] || [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# Auto-detect compose file if not specified
if [ -z "$COMPOSE_FILE" ]; then
    if [ -f "pwd.yml" ] && docker compose -f pwd.yml ps --quiet backend 2>/dev/null | grep -q .; then
        COMPOSE_FILE="pwd.yml"
        echo -e "${GREEN}Using pwd.yml (detected running containers)${NC}"
    elif [ -f "compose.yaml" ] && docker compose -f compose.yaml ps --quiet backend 2>/dev/null | grep -q .; then
        COMPOSE_FILE="compose.yaml"
        echo -e "${GREEN}Using compose.yaml (detected running containers)${NC}"
    elif [ -f "docker-compose.yml" ] && docker compose -f docker-compose.yml ps --quiet backend 2>/dev/null | grep -q .; then
        COMPOSE_FILE="docker-compose.yml"
        echo -e "${GREEN}Using docker-compose.yml (detected running containers)${NC}"
    elif [ -f "pwd.yml" ]; then
        COMPOSE_FILE="pwd.yml"
        echo -e "${YELLOW}Using pwd.yml (default, no running containers detected)${NC}"
    elif [ -f "compose.yaml" ]; then
        COMPOSE_FILE="compose.yaml"
        echo -e "${YELLOW}Using compose.yaml (default, no running containers detected)${NC}"
    else
        echo -e "${RED}Error: No docker-compose file found (pwd.yml or compose.yaml)${NC}"
        exit 1
    fi
fi

# Build the docker compose command
DOCKER_CMD="docker compose"
if [ -n "$COMPOSE_FILE" ]; then
    DOCKER_CMD="$DOCKER_CMD -f $COMPOSE_FILE"
fi
if [ -n "$PROJECT_NAME" ]; then
    DOCKER_CMD="$DOCKER_CMD -p $PROJECT_NAME"
fi

# Check if backend container is running
if ! $DOCKER_CMD ps --quiet backend 2>/dev/null | grep -q .; then
    echo -e "${RED}Error: Backend container is not running${NC}"
    echo -e "${YELLOW}Start containers with: docker compose -f $COMPOSE_FILE up -d${NC}"
    exit 1
fi

# Execute the bench command
echo -e "${GREEN}Executing: bench $@${NC}"
$DOCKER_CMD exec backend bench "$@"