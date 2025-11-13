#!/bin/bash

# ERPNext Production Deployment Script
# Usage: ./deploy.sh [--setup|--regenerate]

set -e

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Helpers
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$PRODUCTION_DIR")"

cd "$PRODUCTION_DIR"

# Parse arguments
case "${1:-}" in
    --help|-h)
        cat << EOF
Usage: $0 [OPTIONS]

Options:
  --setup       Setup environment files from templates
  --regenerate  Only regenerate production.yaml (don't deploy)
  --help, -h    Show this help

Examples:
  $0              # Normal deployment
  $0 --setup      # Create env files first
  $0 --regenerate # Regenerate production.yaml only
EOF
        exit 0
        ;;
    --setup) MODE="setup" ;;
    --regenerate) MODE="regenerate" ;;
    "") MODE="deploy" ;;
    *) echo_error "Unknown: $1 (use --help)"; exit 1 ;;
esac

# Setup mode: create env files
if [[ "$MODE" == "setup" ]]; then
    echo_info "Setting up environment files..."
    
    [[ ! -f "production.env.example" ]] && { echo_error "Template files missing!"; exit 1; }
    
    for template in production.env.example traefik.env.example mariadb.env.example; do
        target="${template%.example}"
        if [[ -f "$target" ]]; then
            echo_warn "$target exists, skipping..."
        else
            cp "$template" "$target" && chmod 600 "$target"
            echo_info "✓ Created $target"
        fi
    done
    
    echo ""
    echo_info "Edit these files before deploying:"
    echo_info "  1. production.env - SITES, passwords, email"
    echo_info "  2. mariadb.env - DB_PASSWORD"
    echo_info "  3. traefik.env - domain, email, password"
    exit 0
fi

# Validate prerequisites
[[ $EUID -eq 0 ]] && { echo_error "Don't run as root"; exit 1; }
command -v docker &> /dev/null || { echo_error "Docker not installed"; exit 1; }
docker compose version &> /dev/null || { echo_error "Docker Compose V2 not installed"; exit 1; }

echo_info "ERPNext Production Deployment"

# Check env files exist
for file in production.env traefik.env mariadb.env; do
    [[ ! -f "$file" ]] && { echo_error "$file not found! Run: $0 --setup"; exit 1; }
done

# Validate configuration
echo_info "Validating configuration..."
./scripts/validate-env.sh || { echo_error "Validation failed!"; exit 1; }

# Warn about defaults
if grep -q "changeit" production.env mariadb.env traefik.env 2>/dev/null; then
    echo_warn "Default passwords detected!"
    read -p "Updated all passwords? (yes/no): " confirm
    [[ "$confirm" != "yes" ]] && { echo_error "Update passwords first"; exit 1; }
fi

if grep -q "yourdomain.com\|CHANGEME_" production.env traefik.env 2>/dev/null; then
    echo_warn "Default domains detected!"
    read -p "Updated all domains? (yes/no): " confirm
    [[ "$confirm" != "yes" ]] && { echo_error "Update domains first"; exit 1; }
fi

# Generate production.yaml helper
generate_yaml() {
    [[ -f "production.yaml" ]] && cp production.yaml "production.yaml.backup.$(date +%Y%m%d_%H%M%S)"
    
    docker compose --project-name erpnext-production \
      --env-file production.env \
      -f "$PROJECT_ROOT/compose.yaml" \
      -f "$PROJECT_ROOT/overrides/compose.redis.yaml" \
      -f "$PROJECT_ROOT/overrides/compose.multi-bench.yaml" \
      -f "$PROJECT_ROOT/overrides/compose.multi-bench-ssl.yaml" \
      config > production.yaml
}

# Regenerate mode: just regenerate yaml
if [[ "$MODE" == "regenerate" ]]; then
    echo_info "Regenerating production.yaml..."
    generate_yaml
    echo_info "✓ Regenerated. Apply: docker compose -f production.yaml up -d"
    exit 0
fi

# Deploy services
echo ""
echo_info "Step 1: Deploying Traefik..."
docker compose --project-name traefik \
  --env-file traefik.env \
  -f "$PROJECT_ROOT/overrides/compose.traefik.yaml" \
  -f "$PROJECT_ROOT/overrides/compose.traefik-ssl.yaml" \
  up -d
echo_info "✓ Traefik deployed"

echo_info "Step 2: Deploying MariaDB..."
docker compose --project-name mariadb \
  --env-file mariadb.env \
  -f "$PROJECT_ROOT/overrides/compose.mariadb-shared.yaml" \
  up -d
echo_info "✓ MariaDB deployed. Waiting 30s for initialization..."
sleep 30

echo_info "Step 3: Generating production.yaml..."
generate_yaml
echo_info "✓ Generated"

echo_info "Step 4: Deploying ERPNext..."
docker compose --project-name erpnext-production -f production.yaml up -d
echo_info "✓ ERPNext deployed"

# Success message
TRAEFIK_DOMAIN=$(grep "^TRAEFIK_DOMAIN=" traefik.env | cut -d'=' -f2)
echo ""
echo_info "✓ Deployment complete!"
echo_info "Next steps:"
echo_info "  1. Check health: docker ps"
echo_info "  2. Create site: ./scripts/create-site.sh"
echo_info "  3. Traefik: https://$TRAEFIK_DOMAIN"
echo_warn "Note: SSL certificates may take a few minutes"