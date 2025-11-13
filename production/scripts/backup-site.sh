#!/bin/bash

# Backup ERPNext Site Script
# Usage: ./backup-site.sh <site-name> [options]

set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# Helper functions
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_debug() { [[ "${DEBUG:-}" == "1" ]] && echo -e "${BLUE}[DEBUG]${NC} $1" || true; }
log_action() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "/tmp/erpnext-backup-$(date '+%Y%m%d').log"; }

# Cleanup on error
cleanup() {
    local exit_code=$?
    [[ $exit_code -ne 0 ]] && echo_error "Script failed with exit code $exit_code" && log_action "FAILED: ${SITE_NAME:-unknown}"
    exit $exit_code
}
trap cleanup EXIT

# Configuration
PROJECT_NAME="${PROJECT_NAME:-erpnext-production}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(dirname "$SCRIPT_DIR")"

# Docker helpers
dc_exec() { docker compose --project-name "$PROJECT_NAME" exec backend "$@"; }
dc_cmd() { docker compose --project-name "$PROJECT_NAME" "$@"; }

cd "$PRODUCTION_DIR"

# Help function
show_help() {
    cat << EOF
Usage: $0 <site-name> [options]

Options:
    --with-files     Include files in backup
    --compress       Compress the backup
    --auto-copy      Copy backups to host ./backups/
    --cleanup-old    Remove backups older than BACKUP_RETENTION_DAYS
    --encrypt        Encrypt with GPG (requires BACKUP_PASSPHRASE env var)
    --debug          Enable debug output
    -h, --help       Show this help

Environment Variables:
    PROJECT_NAME             Docker project name (default: erpnext-production)
    BACKUP_RETENTION_DAYS    Keep backups for N days (default: 30)
    BACKUP_PASSPHRASE        GPG encryption passphrase
    AUTO_COPY                Auto-copy to host (set to 1)
    CLEANUP_OLD              Auto-cleanup old backups (set to 1)

Examples:
    $0 erp.example.com --with-files --auto-copy
    BACKUP_PASSPHRASE='secret' $0 erp.example.com --encrypt --auto-copy

Decryption:
    gpg --decrypt backup-file.gpg > backup-file
EOF
}

# Parse arguments
SITE_NAME="" WITH_FILES="" COMPRESS=""
AUTO_COPY="${AUTO_COPY:-0}" CLEANUP_OLD="${CLEANUP_OLD:-0}" ENCRYPT="${ENCRYPT:-0}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        --with-files) WITH_FILES="--with-files"; shift ;;
        --compress) COMPRESS="--compress"; shift ;;
        --auto-copy) AUTO_COPY=1; shift ;;
        --cleanup-old) CLEANUP_OLD=1; shift ;;
        --encrypt) ENCRYPT=1; shift ;;
        --debug) DEBUG=1; shift ;;
        *) [[ -z "$SITE_NAME" ]] && SITE_NAME="$1" || { echo_error "Unknown: $1"; show_help; exit 1; }; shift ;;
    esac
done

# Get site name if not provided
if [[ -z "$SITE_NAME" ]]; then
    echo_warn "Site name required"
    read -p "Enter site name (e.g., erp.example.com): " SITE_NAME
fi

[[ -z "$SITE_NAME" ]] && { echo_error "Site name cannot be empty"; exit 1; }

# Validate site name format
if [[ ! "$SITE_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$ ]]; then
    echo_warn "Site name format looks unusual: $SITE_NAME"
    read -p "Continue? (y/N): " -n 1 -r; echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

echo_debug "Site: $SITE_NAME, Project: $PROJECT_NAME"

# Check encryption requirements
if [[ "$ENCRYPT" == "1" ]]; then
    [[ -z "${BACKUP_PASSPHRASE:-}" ]] && { echo_error "BACKUP_PASSPHRASE not set"; exit 1; }
    command -v gpg >/dev/null 2>&1 || { echo_error "GPG not installed"; exit 1; }
    echo_debug "Encryption ready"
fi

# Validate environment
[[ ! -f "production.yaml" ]] && { echo_error "production.yaml not found"; exit 1; }
docker info >/dev/null 2>&1 || { echo_error "Docker not running"; exit 1; }
dc_exec echo "test" >/dev/null 2>&1 || { echo_error "Backend container not running"; exit 1; }

# Verify site exists
echo_info "Verifying site: $SITE_NAME"
if ! dc_exec bench --site "$SITE_NAME" list-apps >/dev/null 2>&1; then
    echo_error "Site '$SITE_NAME' not found"
    echo_info "Available sites:"
    dc_exec find /home/frappe/frappe-bench/sites -maxdepth 1 -type d \( -name "*.local" -o -name "*.*" \) | \
        sed 's|.*/||' | grep -v "^$" || echo "  None found"
    exit 1
fi

# Create backup
echo_info "Creating backup for: $SITE_NAME"
log_action "STARTED: $SITE_NAME"
BACKUP_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

if ! dc_exec bench --site "$SITE_NAME" backup $WITH_FILES $COMPRESS; then
    echo_error "Backup command failed!"
    log_action "FAILED: Backup command"
    exit 1
fi

# Verify backup files
BACKUP_PATH="/home/frappe/frappe-bench/sites/$SITE_NAME/private/backups"
BACKUP_FILES=$(dc_exec find "$BACKUP_PATH" -type f -mmin -2 2>/dev/null | tr -d '\r' || echo "")

if [[ -z "$BACKUP_FILES" ]]; then
    echo_error "No backup files found!"
    log_action "FAILED: No files"
    exit 1
fi

# Display backup info
BACKUP_COUNT=$(echo "$BACKUP_FILES" | wc -l)
echo_info "✓ Created $BACKUP_COUNT file(s)"
echo_info "Files:"

TOTAL_SIZE=0
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    SIZE_BYTES=$(dc_exec stat -c%s "$file" 2>/dev/null | tr -d '\r' || echo "0")
    SIZE_HR=$(numfmt --to=iec-i --suffix=B "$SIZE_BYTES" 2>/dev/null || echo "$SIZE_BYTES bytes")
    echo_info "  - $(basename "$file") ($SIZE_HR)"
    TOTAL_SIZE=$((TOTAL_SIZE + SIZE_BYTES))
done <<< "$BACKUP_FILES"

[[ $TOTAL_SIZE -gt 0 ]] && echo_info "Total size: $(numfmt --to=iec-i --suffix=B "$TOTAL_SIZE" 2>/dev/null || echo "$TOTAL_SIZE bytes")"

log_action "SUCCESS: $BACKUP_COUNT files, $TOTAL_SIZE bytes"

# Auto-copy to host
if [[ "$AUTO_COPY" == "1" ]]; then
    echo_info "Copying to host ./backups/"
    mkdir -p ./backups
    
    BACKEND_CONTAINER=$(dc_cmd ps -q backend)
    if docker cp "${BACKEND_CONTAINER}:${BACKUP_PATH}/." ./backups/ 2>/dev/null; then
        echo_info "✓ Copied to ./backups/"
        
        # Encrypt if requested
        if [[ "$ENCRYPT" == "1" ]]; then
            echo_info "Encrypting backups..."
            TIMESTAMP_PREFIX="${BACKUP_TIMESTAMP:0:12}"
            RECENT_BACKUPS=$(find ./backups -type f -mmin -1 -name "${TIMESTAMP_PREFIX}*" ! -name "*.gpg" 2>/dev/null || true)
            
            if [[ -n "$RECENT_BACKUPS" ]]; then
                ENCRYPTED_COUNT=0
                while IFS= read -r backup_file; do
                    [[ ! -f "$backup_file" ]] && continue
                    
                    if echo "$BACKUP_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
                        --symmetric --cipher-algo AES256 -o "${backup_file}.gpg" "$backup_file" 2>/dev/null; then
                        
                        [[ -f "${backup_file}.gpg" ]] && rm -f "$backup_file" && ((ENCRYPTED_COUNT++))
                        echo_info "  ✓ Encrypted: $(basename "${backup_file}.gpg")"
                    else
                        echo_warn "  ✗ Encryption failed: $(basename "$backup_file")"
                    fi
                done <<< "$RECENT_BACKUPS"
                
                echo_info "✓ Encrypted $ENCRYPTED_COUNT file(s)"
                log_action "SUCCESS: Encrypted $ENCRYPTED_COUNT files"
            fi
        fi
        
        # Show latest files
        echo_info "Latest in ./backups/:"
        ls -lht ./backups/ | head -n 6 || true
    else
        echo_warn "Copy failed. Files remain in container."
    fi
else
    echo_info "Backup location: ${BACKUP_PATH}/"
    echo_info "To copy: docker cp \$(docker compose -p $PROJECT_NAME ps -q backend):${BACKUP_PATH}/. ./backups/"
fi

# Cleanup old backups
if [[ "$CLEANUP_OLD" == "1" ]] && [[ "$BACKUP_RETENTION_DAYS" -gt 0 ]]; then
    echo_info "Cleaning backups older than $BACKUP_RETENTION_DAYS days"
    
    # Container cleanup
    dc_exec find "$BACKUP_PATH" -type f -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null && \
        echo_info "✓ Container cleanup done" || echo_warn "Container cleanup failed"
    
    # Host cleanup
    if [[ -d "./backups" ]]; then
        DELETED=$(find "./backups" -type f -mtime +$BACKUP_RETENTION_DAYS 2>/dev/null | wc -l)
        [[ "$DELETED" -gt 0 ]] && find "./backups" -type f -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null
        echo_info "✓ Host cleanup: removed $DELETED file(s)"
    fi
fi

echo_info "✓ Backup completed successfully!"