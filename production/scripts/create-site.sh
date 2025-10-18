#!/bin/bash

# Create ERPNext Site Script
# Usage: ./create-site.sh <site-name> [admin-password]

set -e

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Helper functions
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Navigate to production directory
cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" || exit 1

PROJECT_NAME="erpnext-production"

# Get site name
if [[ -z "$1" ]]; then
    echo_warn "Usage: $0 <site-name> [admin-password]"
    read -p "Enter site name (e.g., erp.example.com): " SITE_NAME
elif [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    cat << EOF
Usage: $0 <site-name> [admin-password]

Arguments:
  site-name         Site domain (e.g., erp.example.com)
  admin-password    Optional admin password (default: 'admin')

Examples:
  $0 erp.example.com
  $0 erp.example.com MySecurePass123

Notes:
  - Requires backend container to be running
  - DNS should point to your server IP
  - Change admin password after first login
  - SSL certificate may take a few minutes
EOF
    exit 0
else
    SITE_NAME=$1
fi

[[ -z "$SITE_NAME" ]] && { echo_error "Site name cannot be empty"; exit 1; }

# Get admin password
if [[ -z "$2" ]]; then
    read -sp "Enter admin password (Enter for 'admin'): " ADMIN_PASSWORD
    echo
    if [[ -z "$ADMIN_PASSWORD" ]]; then
        ADMIN_PASSWORD="admin"
        echo_warn "Using default password 'admin' - Change after login!"
    fi
else
    ADMIN_PASSWORD=$2
fi

# Get DB password from mariadb.env
[[ ! -f "mariadb.env" ]] && { echo_error "mariadb.env not found!"; exit 1; }
DB_ROOT_PASSWORD=$(grep "^DB_PASSWORD=" mariadb.env | cut -d'=' -f2)
[[ -z "$DB_ROOT_PASSWORD" ]] && { echo_error "DB_PASSWORD not found in mariadb.env"; exit 1; }

# Check if backend is running
docker ps | grep -q "$PROJECT_NAME-backend" || {
    echo_error "Backend not running! Run: ./scripts/deploy.sh"
    exit 1
}

# Create the site
echo_info "Creating site: $SITE_NAME"
docker compose --project-name "$PROJECT_NAME" exec backend \
  bench new-site \
    --mariadb-user-host-login-scope='%' \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --install-app erpnext \
    --admin-password "$ADMIN_PASSWORD" \
    "$SITE_NAME"

# Success message
echo ""
echo_info "✓ Site created successfully!"
echo_info "URL: https://$SITE_NAME"
echo_info "Username: Administrator"
echo_info "Password: $ADMIN_PASSWORD"
echo ""
echo_warn "Next steps:"
echo_warn "1. Point DNS $SITE_NAME to your server IP"
echo_warn "2. Update SITES in production.env"
echo_warn "3. Change admin password after login"
echo_warn "4. Wait for SSL certificate (few minutes)"
echo ""
echo_info "Set as default: docker compose -p $PROJECT_NAME exec backend bench use $SITE_NAME"
