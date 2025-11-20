#!/bin/bash

###############################################################################
# ERPNext Backup Management Helper Script
# Manages periodic backup setup with Digital Ocean Spaces (S3)
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step()  { echo -e "${BLUE}[STEP]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$SCRIPT_DIR"

cd "$BACKUP_DIR"

show_help() {
    cat <<EOF
ERPNext Backup Management

Usage: $0 [COMMAND]

Commands:
  setup         Interactive setup of backup configuration
  start         Start backup services
  stop          Stop backup services  
  restart       Restart backup services
  test          Run a test backup immediately
  status        Show backup service status
  logs          Show backup logs (follow mode)
  list-s3       List backups in S3
  validate      Validate configuration
  help          Show this help

Examples:
  $0 setup      # Configure backup settings
  $0 start      # Start periodic backups
  $0 test       # Run immediate backup
  $0 logs       # Watch backup logs

EOF
}

validate_config() {
    echo_step "Validating configuration..."
    
    if [[ ! -f "backup.env" ]]; then
        echo_error "backup.env not found. Run '$0 setup' first."
        return 1
    fi
    
    # Source the env file safely by exporting variables
    set -a
    source backup.env 2>/dev/null || {
        echo_error "Failed to load backup.env - check for syntax errors"
        return 1
    }
    set +a
    
    local errors=0
    
    # Check required variables
    if [[ "${S3_ACCESS_KEY_ID:-}" == "CHANGEME"* ]] || [[ -z "${S3_ACCESS_KEY_ID:-}" ]]; then
        echo_error "S3_ACCESS_KEY_ID not configured"
        ((errors++))
    fi
    
    if [[ "${S3_SECRET_ACCESS_KEY:-}" == "CHANGEME"* ]] || [[ -z "${S3_SECRET_ACCESS_KEY:-}" ]]; then
        echo_error "S3_SECRET_ACCESS_KEY not configured"
        ((errors++))
    fi
    
    if [[ -z "${S3_ENDPOINT_URL:-}" ]]; then
        echo_error "S3_ENDPOINT_URL not configured"
        ((errors++))
    fi
    
    if [[ -z "${S3_BUCKET_NAME:-}" ]]; then
        echo_error "S3_BUCKET_NAME not configured"
        ((errors++))
    fi
    
    if [[ -z "${BACKUP_SITES:-}" ]]; then
        echo_warn "BACKUP_SITES not configured, will default to 'erp.localhost'"
    fi
    
    if [[ $errors -gt 0 ]]; then
        echo_error "Configuration has $errors error(s). Please fix backup.env"
        return 1
    fi
    
    echo_info "✓ Configuration valid"
    return 0
}

setup_backup_config() {
    echo_step "Backup Configuration Setup"
    echo ""
    
    # Check if backup.env exists
    if [[ -f "backup.env" ]]; then
        read -p "backup.env exists. Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo_info "Keeping existing configuration. Edit backup.env manually if needed."
            return 0
        fi
    fi
    
    # Infrastructure constants (hardcoded)
    local BUCKET_NAME="erp-is-backup"
    local REGION="blr1"
    
    # Interactive prompts
    echo_warn "⚠️  SECURITY: Never commit credentials to git!"
    echo_info "Enter your Digital Ocean Spaces credentials:"
    echo ""
    
    read -p "Spaces Access Key ID: " ACCESS_KEY
    read -sp "Spaces Secret Access Key: " SECRET_KEY
    echo ""
    echo ""
    
    read -p "Environment (production/staging/development) [default: development]: " ENV_PREFIX
    ENV_PREFIX=${ENV_PREFIX:-development}
    
    read -p "Site name to backup (default: erp.localhost): " SITE_NAME
    SITE_NAME=${SITE_NAME:-erp.localhost}
    
    echo ""
    echo_info "Backup schedules (automated via Docker Compose):"
    echo "  • Hourly: Database only (every hour)"
    echo "  • Daily: Full backup with files (3:00 AM)"
    echo ""
    
    read -p "Local retention days (default: 1): " LOCAL_RETENTION
    LOCAL_RETENTION=${LOCAL_RETENTION:-1}
    
    read -p "S3 retention days (default: 5): " S3_RETENTION
    S3_RETENTION=${S3_RETENTION:-5}
    
    # Create backup.env
    cat > backup.env <<EOF
# Backup Configuration for ERPNext Production
# Generated on $(date)
# ⚠️  WARNING: This file contains secrets - DO NOT commit to git!

# ============================================
# S3-Compatible Storage (Digital Ocean Spaces)
# ============================================
S3_ENDPOINT_URL=https://${REGION}.digitaloceanspaces.com
S3_BUCKET_NAME=${BUCKET_NAME}
S3_REGION=${REGION}
S3_ACCESS_KEY_ID=${ACCESS_KEY}
S3_SECRET_ACCESS_KEY=${SECRET_KEY}

# ============================================
# Environment Segregation
# ============================================
# Creates S3 folders: s3://bucket/{ENV_PREFIX}/{site}/{YYYY-MM-DD}/
ENV_PREFIX=${ENV_PREFIX}

# ============================================
# Backup Retention Policy
# ============================================
BACKUP_RETENTION_DAYS=${LOCAL_RETENTION}
S3_BACKUP_RETENTION_DAYS=${S3_RETENTION}

# ============================================
# Backup Options
# ============================================
# Schedules are defined in compose.backup-s3.yaml:
#   - Hourly: Database only (BACKUP_WITH_FILES=0)
#   - Daily 3AM: Full backup with files (BACKUP_WITH_FILES=1)
#
# Note: bench backup only supports --with-files (all files) or no flag (DB only)
# There are no granular options for individual file types

BACKUP_WITH_FILES=0              # 0=DB only, 1=DB+all files
BACKUP_COMPRESS=1                # Compress backups

# ============================================
# Site Configuration
# ============================================
BACKUP_SITES=${SITE_NAME}

# ============================================
# Advanced Options
# ============================================
BACKUP_DEBUG=0
S3_STORAGE_CLASS=STANDARD
BACKUP_ENCRYPT=0
EOF
    
    chmod 600 backup.env
    echo_info "✓ Configuration saved to backup.env"
}

start_backup_services() {
    echo_step "Starting backup services..."
    
    validate_config || exit 1
    
    # Export ENV_PREFIX for docker compose variable substitution
    export $(grep ^ENV_PREFIX backup.env | xargs)
    
    if ! docker compose -f "$PRODUCTION_DIR/production.yaml" -f "$BACKUP_DIR/compose.backup-s3.yaml" config > /dev/null 2>&1; then
        echo_error "Docker Compose configuration validation failed"
        exit 1
    fi
    
    echo_info "Starting backup-cron and updating scheduler with backup volume..."
    # Force recreate backup-cron to ensure it picks up latest schedule labels
    docker compose --project-name erpnext-production \
        -f "$PRODUCTION_DIR/production.yaml" \
        -f "$BACKUP_DIR/compose.backup-s3.yaml" \
        up -d --force-recreate backup-cron scheduler
    
    # Wait for services to be ready
    sleep 2
    
    # Verify backup script is mounted
    if docker compose --project-name erpnext-production \
        -f "$PRODUCTION_DIR/production.yaml" \
        exec -T scheduler test -f /usr/local/bin/backup-to-s3.sh 2>/dev/null; then
        echo_info "✓ Backup script mounted successfully"
    else
        echo_error "Backup script not found in scheduler container"
        exit 1
    fi
    
    echo_info "✓ Backup services started"
    echo_info "  - Hourly DB backup: Every hour"
    echo_info "  - Daily full backup: 3:00 AM"
}

stop_backup_services() {
    echo_step "Stopping backup services..."
    
    docker compose --project-name erpnext-production \
        -f "$PRODUCTION_DIR/production.yaml" \
        -f "$BACKUP_DIR/compose.backup-s3.yaml" \
        stop backup-cron
    
    echo_info "✓ Backup services stopped"
}

restart_backup_services() {
    stop_backup_services
    sleep 2
    start_backup_services
}

run_test_backup() {
    echo_step "Running test backup..."
    
    validate_config || exit 1
    
    # Check if scheduler has backup script mounted
    echo_info "Checking backup script availability..."
    if ! docker compose --project-name erpnext-production \
        -f "$PRODUCTION_DIR/production.yaml" \
        exec -T scheduler test -f /usr/local/bin/backup-to-s3.sh 2>/dev/null; then
        echo_warn "Backup script not mounted. Starting backup services first..."
        start_backup_services
    fi
    
    echo_info "Executing backup script manually..."
    docker compose --project-name erpnext-production \
        -f "$PRODUCTION_DIR/production.yaml" \
        -f "$BACKUP_DIR/compose.backup-s3.yaml" \
        exec scheduler /bin/bash /usr/local/bin/backup-to-s3.sh
    
    echo_info "✓ Test backup completed"
}

show_status() {
    echo_step "Backup Service Status"
    echo ""
    
    # Check if containers are running
    if docker ps --filter "name=erpnext-production-backup-cron" --format "{{.Status}}" | grep -q "Up"; then
        echo_info "✓ Backup cron service: Running"
        # Show cron jobs
        echo_info "  Active jobs:"
        docker exec erpnext-production-backup-cron-1 ofelia jobs 2>/dev/null | grep -E "backup-db|backup-full" || echo "    (unable to list jobs)"
    else
        echo_warn "✗ Backup cron service: Not running"
        echo_info "  Run: $0 start"
    fi
    
    if docker ps --filter "name=erpnext-production-scheduler" --format "{{.Status}}" | grep -q "Up"; then
        echo_info "✓ Scheduler service: Running"
        
        # Check if backup script is mounted
        if docker compose --project-name erpnext-production \
            -f "$PRODUCTION_DIR/production.yaml" \
            exec -T scheduler test -f /usr/local/bin/backup-to-s3.sh 2>/dev/null; then
            echo_info "  ✓ Backup script mounted"
        else
            echo_warn "  ✗ Backup script NOT mounted - run: $0 restart"
        fi
    else
        echo_warn "✗ Scheduler service: Not running"
    fi
    
    echo ""
    echo_step "Recent backups in container:"
    docker compose --project-name erpnext-production exec scheduler \
        ls -lht /home/frappe/frappe-bench/sites/*/private/backups/ 2>/dev/null | head -10 || echo_warn "No backups found"
}

show_logs() {
    echo_step "Following backup logs (Ctrl+C to exit)..."
    docker compose --project-name erpnext-production logs -f backup-cron scheduler
}

list_s3_backups() {
    echo_step "Listing S3 backups..."
    
    validate_config || exit 1
    
    # Variables already loaded by validate_config
    
    docker compose --project-name erpnext-production \
        -f "$PRODUCTION_DIR/production.yaml" \
        exec scheduler bash -c "
            export AWS_ACCESS_KEY_ID='${S3_ACCESS_KEY_ID}'
            export AWS_SECRET_ACCESS_KEY='${S3_SECRET_ACCESS_KEY}'
            
            if ! command -v aws &>/dev/null; then
                pip3 install --user awscli --upgrade
                export PATH=\"\$HOME/.local/bin:\$PATH\"
            fi
            
            aws s3 ls s3://${S3_BUCKET_NAME}/ --recursive --endpoint-url=${S3_ENDPOINT_URL} --human-readable
        "
}

# Main command dispatcher
case "${1:-help}" in
    setup)
        setup_backup_config
        echo ""
        echo_info "Next steps:"
        echo "  1. Review backup.env"
        echo "  2. Run: $0 validate"
        echo "  3. Run: $0 start"
        ;;
    start)
        start_backup_services
        ;;
    stop)
        stop_backup_services
        ;;
    restart)
        restart_backup_services
        ;;
    test)
        run_test_backup
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    list-s3)
        list_s3_backups
        ;;
    validate)
        validate_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
