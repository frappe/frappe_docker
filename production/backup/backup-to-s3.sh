#!/bin/bash

###############################################################################
# ERPNext Backup to S3 (Digital Ocean Spaces) Script
# 
# This script creates ERPNext backups and uploads them to S3-compatible storage
# (Digital Ocean Spaces). It handles multiple sites, retention policies, and
# provides detailed logging and error handling.
#
# Usage: /usr/local/bin/backup-to-s3.sh
#
# Environment Variables Required:
#   S3_ENDPOINT_URL          - S3 endpoint (e.g., https://blr1.digitaloceanspaces.com)
#   S3_BUCKET_NAME          - S3 bucket name
#   AWS_ACCESS_KEY_ID       - S3 access key
#   AWS_SECRET_ACCESS_KEY   - S3 secret key
#   BACKUP_SITES            - Space-separated list of sites to backup
#
# Optional Environment Variables:
#   BACKUP_WITH_FILES       - Include files (default: 1)
#   BACKUP_COMPRESS         - Compress backups (default: 1)
#   BACKUP_RETENTION_DAYS   - Local retention in days (default: 7)
#   S3_BACKUP_RETENTION_DAYS - S3 retention in days (default: 30)
#   BACKUP_DEBUG            - Enable debug logging (default: 0)
#   S3_REGION               - S3 region (default: blr1)
#   S3_STORAGE_CLASS        - S3 storage class (default: STANDARD)
###############################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info()  { echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_debug() { [[ "${BACKUP_DEBUG:-0}" == "1" ]] && echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" || true; }

# Configuration with defaults
BACKUP_WITH_FILES="${BACKUP_WITH_FILES:-1}"
BACKUP_COMPRESS="${BACKUP_COMPRESS:-1}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
S3_BACKUP_RETENTION_DAYS="${S3_BACKUP_RETENTION_DAYS:-30}"
BACKUP_DEBUG="${BACKUP_DEBUG:-0}"
S3_REGION="${S3_REGION:-blr1}"
S3_STORAGE_CLASS="${S3_STORAGE_CLASS:-STANDARD}"
BACKUP_SITES="${BACKUP_SITES:-}"
ENV_PREFIX="${ENV_PREFIX:-production}"

# Counters
TOTAL_BACKUPS=0
SUCCESSFUL_BACKUPS=0
FAILED_BACKUPS=0
UPLOADED_FILES=0

###############################################################################
# Function: check_prerequisites
# Description: Verify all required tools and environment variables are present
###############################################################################
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for bench command
    if ! command -v bench &> /dev/null; then
        log_error "Required command 'bench' not found. Is this running in ERPNext container?"
        exit 1
    fi
    
    # Check for AWS CLI, install if missing
    if ! command -v aws &> /dev/null; then
        log_info "AWS CLI not found. Installing..."
        # Install AWS CLI
        pip3 install --user --no-warn-script-location awscli > /tmp/aws-install.log 2>&1
        export PATH="$HOME/.local/bin:$PATH"
        
        # Verify installation
        if command -v aws &> /dev/null || [ -f "$HOME/.local/bin/aws" ]; then
            log_info "AWS CLI installed successfully"
        else
            log_error "Failed to install AWS CLI"
            log_debug "Install log: $(cat /tmp/aws-install.log)"
            exit 1
        fi
    fi
    
    # Check required environment variables
    local required_vars=(
        "S3_ENDPOINT_URL"
        "S3_BUCKET_NAME"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "BACKUP_SITES"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable '$var' is not set"
            exit 1
        fi
    done
    
    log_debug "S3_ENDPOINT_URL: $S3_ENDPOINT_URL"
    log_debug "S3_BUCKET_NAME: $S3_BUCKET_NAME"
    log_debug "S3_REGION: $S3_REGION"
    log_debug "BACKUP_SITES: $BACKUP_SITES"
    
    log_info "Prerequisites check passed"
}

###############################################################################
# Function: configure_aws_cli
# Description: Configure AWS CLI for Digital Ocean Spaces
###############################################################################
configure_aws_cli() {
    log_info "Configuring AWS CLI for Digital Ocean Spaces..."
    
    mkdir -p "$HOME/.aws"
    
    cat > "$HOME/.aws/credentials" <<EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF
    
    cat > "$HOME/.aws/config" <<EOF
[default]
region = ${S3_REGION}
output = json
EOF
    
    chmod 600 "$HOME/.aws/credentials"
    chmod 600 "$HOME/.aws/config"
    
    log_info "AWS CLI configured successfully"
}

###############################################################################
# Function: test_s3_connection
# Description: Test connection to S3 bucket
###############################################################################
test_s3_connection() {
    log_info "Testing S3 connection..."
    
    if aws s3 ls "s3://${S3_BUCKET_NAME}" --endpoint-url="${S3_ENDPOINT_URL}" &> /dev/null; then
        log_info "S3 connection successful"
        return 0
    else
        log_error "Failed to connect to S3 bucket: ${S3_BUCKET_NAME}"
        log_error "Endpoint: ${S3_ENDPOINT_URL}"
        return 1
    fi
}

###############################################################################
# Function: create_backup
# Description: Create backup for a specific site
# Arguments: $1 - site name
###############################################################################
create_backup() {
    local site="$1"
    local backup_dir="/home/frappe/frappe-bench/sites/${site}/private/backups"
    
    log_info "Creating backup for site: ${site}"
    
    # Build bench backup command
    local bench_cmd="bench --site ${site} backup"
    
    # Add options based on configuration
    if [[ "$BACKUP_WITH_FILES" == "1" ]]; then
        bench_cmd="${bench_cmd} --with-files"
        log_debug "Backup mode: Full (database + files)"
    else
        log_debug "Backup mode: Database only"
    fi
    
    [[ "$BACKUP_COMPRESS" == "1" ]] && bench_cmd="${bench_cmd} --compress"
    
    log_debug "Executing: ${bench_cmd}"
    
    # Create marker file to identify new backups
    local marker="/tmp/backup-marker-${site}-$$.tmp"
    touch "$marker"
    sleep 1
    
    # Execute backup (redirect output to avoid polluting file list)
    if eval "$bench_cmd" > /tmp/backup-output-$$.log 2>&1; then
        log_info "Backup created successfully for ${site}"
        
        # Find new backup files
        local new_files
        new_files=$(find "$backup_dir" -type f -newer "$marker" 2>/dev/null || true)
        rm -f "$marker"
        
        if [[ -z "$new_files" ]]; then
            log_warn "No new backup files found for ${site}"
            cat /tmp/backup-output-$$.log >&2
            rm -f /tmp/backup-output-$$.log
            return 1
        fi
        
        rm -f /tmp/backup-output-$$.log
        echo "$new_files"
        return 0
    else
        log_error "Backup failed for ${site}"
        cat /tmp/backup-output-$$.log >&2
        rm -f "$marker" /tmp/backup-output-$$.log
        return 1
    fi
}

###############################################################################
# Function: upload_to_s3
# Description: Upload backup files to S3
# Arguments: $1 - site name, $2 - file path
###############################################################################
upload_to_s3() {
    local site="$1"
    local file_path="$2"
    local file_name=$(basename "$file_path")
    local timestamp=$(date '+%Y-%m-%d')
    # S3 path structure: s3://bucket/{env}/{site}/{YYYY-MM-DD}/{filename}
    local s3_path="s3://${S3_BUCKET_NAME}/${ENV_PREFIX}/${site}/${timestamp}/${file_name}"
    
    log_info "Uploading ${file_name} to S3..."
    log_debug "S3 path: ${s3_path}"
    
    if aws s3 cp "$file_path" "$s3_path" \
        --endpoint-url="${S3_ENDPOINT_URL}" \
        --storage-class="${S3_STORAGE_CLASS}" \
        --no-progress 2>&1 | while IFS= read -r line; do log_debug "$line"; done; then
        
        local file_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "0")
        local file_size_hr=$(numfmt --to=iec-i --suffix=B "$file_size" 2>/dev/null || echo "${file_size} bytes")
        
        log_info "✓ Uploaded ${file_name} (${file_size_hr})"
        ((UPLOADED_FILES++))
        return 0
    else
        log_error "✗ Failed to upload ${file_name}"
        return 1
    fi
}

###############################################################################
# Function: cleanup_old_local_backups
# Description: Remove old local backup files
# Arguments: $1 - site name
###############################################################################
cleanup_old_local_backups() {
    local site="$1"
    local backup_dir="/home/frappe/frappe-bench/sites/${site}/private/backups"
    
    log_info "Cleaning up old local backups for ${site} (keeping ${BACKUP_RETENTION_DAYS} days)..."
    
    if [[ ! -d "$backup_dir" ]]; then
        log_warn "Backup directory not found: ${backup_dir}"
        return 0
    fi
    
    local deleted_count=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
        log_debug "Deleted old local backup: $(basename "$file")"
    done < <(find "$backup_dir" -type f -mtime "+${BACKUP_RETENTION_DAYS}" -print0 2>/dev/null || true)
    
    if [[ $deleted_count -gt 0 ]]; then
        log_info "Deleted ${deleted_count} old local backup file(s)"
    else
        log_debug "No old local backups to delete"
    fi
}

###############################################################################
# Function: cleanup_old_s3_backups
# Description: Remove old S3 backup files
# Arguments: $1 - site name
###############################################################################
cleanup_old_s3_backups() {
    local site="$1"
    local cutoff_date=$(date -u -d "${S3_BACKUP_RETENTION_DAYS} days ago" +%s 2>/dev/null || date -u -v-${S3_BACKUP_RETENTION_DAYS}d +%s 2>/dev/null || echo "0")
    
    log_info "Cleaning up old S3 backups for ${site} (keeping ${S3_BACKUP_RETENTION_DAYS} days)..."
    
    local deleted_count=0
    local s3_prefix="s3://${S3_BUCKET_NAME}/${ENV_PREFIX}/${site}/"
    
    # List all objects and filter by date
    while IFS= read -r line; do
        local object_date=$(echo "$line" | awk '{print $1, $2}')
        local object_key=$(echo "$line" | awk '{$1=$2=$3=""; print $0}' | sed 's/^[ \t]*//')
        
        if [[ -z "$object_key" ]]; then
            continue
        fi
        
        local object_timestamp=$(date -u -d "$object_date" +%s 2>/dev/null || date -u -j -f "%Y-%m-%d %H:%M:%S" "$object_date" +%s 2>/dev/null || echo "0")
        
        if [[ "$object_timestamp" -lt "$cutoff_date" ]]; then
            if aws s3 rm "s3://${S3_BUCKET_NAME}/${object_key}" --endpoint-url="${S3_ENDPOINT_URL}" &>/dev/null; then
                ((deleted_count++))
                log_debug "Deleted old S3 backup: ${object_key}"
            fi
        fi
    done < <(aws s3 ls "${s3_prefix}" --endpoint-url="${S3_ENDPOINT_URL}" --recursive 2>/dev/null || true)
    
    if [[ $deleted_count -gt 0 ]]; then
        log_info "Deleted ${deleted_count} old S3 backup file(s)"
    else
        log_debug "No old S3 backups to delete"
    fi
}

###############################################################################
# Function: process_site_backup
# Description: Complete backup workflow for a single site
# Arguments: $1 - site name
###############################################################################
process_site_backup() {
    local site="$1"
    ((TOTAL_BACKUPS++))
    
    log_info "=========================================="
    log_info "Processing backup for: ${site}"
    log_info "=========================================="
    
    # Create backup
    local backup_files
    if ! backup_files=$(create_backup "$site"); then
        log_error "Backup creation failed for ${site}"
        ((FAILED_BACKUPS++))
        return 1
    fi
    
    # Upload each backup file to S3
    local upload_success=true
    while IFS= read -r file; do
        # Skip empty lines and non-file paths
        [[ -z "$file" ]] && continue
        [[ ! -f "$file" ]] && continue
        
        if ! upload_to_s3 "$site" "$file"; then
            upload_success=false
        fi
    done <<< "$backup_files"
    
    if [[ "$upload_success" == "true" ]]; then
        ((SUCCESSFUL_BACKUPS++))
        log_info "✓ Backup completed successfully for ${site}"
    else
        ((FAILED_BACKUPS++))
        log_error "✗ Some uploads failed for ${site}"
    fi
    
    # Cleanup old backups
    cleanup_old_local_backups "$site"
    cleanup_old_s3_backups "$site"
    
    return 0
}

###############################################################################
# Function: send_notification
# Description: Send notification about backup status (placeholder for future)
###############################################################################
send_notification() {
    local status="$1"
    local message="$2"
    
    # TODO: Implement email or Slack notifications
    log_debug "Notification: ${status} - ${message}"
}

###############################################################################
# Main execution
###############################################################################
main() {
    local start_time=$(date +%s)
    
    log_info "=========================================="
    log_info "ERPNext Backup to S3 Started"
    log_info "=========================================="
    
    # Check prerequisites
    check_prerequisites
    
    # Configure AWS CLI
    configure_aws_cli
    
    # Test S3 connection
    if ! test_s3_connection; then
        log_error "Cannot proceed without S3 connection"
        exit 1
    fi
    
    # Process each site
    IFS=' ' read -ra SITES <<< "$BACKUP_SITES"
    for site in "${SITES[@]}"; do
        [[ -z "$site" ]] && continue
        process_site_backup "$site" || true
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Summary
    log_info "=========================================="
    log_info "Backup Summary"
    log_info "=========================================="
    log_info "Total sites processed: ${TOTAL_BACKUPS}"
    log_info "Successful backups: ${SUCCESSFUL_BACKUPS}"
    log_info "Failed backups: ${FAILED_BACKUPS}"
    log_info "Files uploaded to S3: ${UPLOADED_FILES}"
    log_info "Duration: ${duration} seconds"
    log_info "=========================================="
    
    if [[ $FAILED_BACKUPS -gt 0 ]]; then
        send_notification "WARNING" "Some backups failed. Check logs for details."
        exit 1
    else
        send_notification "SUCCESS" "All backups completed successfully."
        exit 0
    fi
}

# Execute main function
main "$@"
