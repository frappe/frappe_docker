#!/bin/bash

# Stop ERPNext Production Services
# Usage: ./stop.sh [--all]

set -e

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Helpers
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Navigate to production directory
cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" || exit 1

PROJECT_ROOT="$(dirname "$(pwd)")"

# Check for help first
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    cat << EOF
Usage: $0 [--all]

Options:
  --all         Stop ERPNext, MariaDB, and Traefik
  -h, --help    Show this help

Examples:
  $0            # Stop ERPNext only (interactive)
  $0 --all      # Stop all services (no prompt)

EOF
    exit 0
fi

# Stop service helper
stop_service() {
    local name=$1 project=$2
    shift 2
    
    if docker ps | grep -q "$name"; then
        echo_info "Stopping $name..."
        docker compose --project-name "$project" "$@" down
        echo_info "✓ $name stopped"
    else
        echo_warn "$name not running"
    fi
}

echo_info "Stopping ERPNext services..."

# Stop ERPNext
stop_service "erpnext-production" "erpnext-production" -f production.yaml

# Ask about stopping dependencies
STOP_ALL="${1:-}"
if [[ "$STOP_ALL" != "--all" ]]; then
    read -p "Stop MariaDB and Traefik too? (yes/no): " STOP_ALL
fi

if [[ "$STOP_ALL" == "yes" ]] || [[ "$STOP_ALL" == "--all" ]]; then
    stop_service "mariadb" "mariadb" --env-file mariadb.env -f "$PROJECT_ROOT/overrides/compose.mariadb-shared.yaml"
    stop_service "traefik" "traefik" --env-file traefik.env -f "$PROJECT_ROOT/overrides/compose.traefik.yaml" -f "$PROJECT_ROOT/overrides/compose.traefik-ssl.yaml"
fi

echo ""
echo_info "✓ Services stopped. Restart: ./scripts/deploy.sh"
