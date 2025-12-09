#!/bin/bash
# ERPNext Database Cleanup Script
# Prevents database bloat by cleaning old logs and versions
# Run monthly via cron or manually with interactive prompts

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default retention policies
DEFAULT_COMMUNICATION_RETENTION=180
DEFAULT_VERSION_RETENTION=90
DEFAULT_JOB_LOG_RETENTION=30
DEFAULT_ERROR_LOG_RETENTION=90

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to display help
show_help() {
    cat << EOF
ERPNext Database Cleanup Script

DESCRIPTION:
    Prevents database bloat by cleaning old communications, versions, logs, and deleted documents.
    Supports both interactive and automated modes with configurable retention policies.

USAGE:
    $0 [OPTIONS] [SITE]

ARGUMENTS:
    SITE                    ERPNext site name (default: erp.localhost)

OPTIONS:
    --comm-retention DAYS   Retention days for communications/emails (default: $DEFAULT_COMMUNICATION_RETENTION)
    --version-retention DAYS Retention days for edit history (default: $DEFAULT_VERSION_RETENTION)
    --job-retention DAYS    Retention days for job logs (default: $DEFAULT_JOB_LOG_RETENTION)
    --error-retention DAYS  Retention days for error logs (default: $DEFAULT_ERROR_LOG_RETENTION)
    --dry-run               Show what would be cleaned without actually doing it
    -h, --help              Show this help message
    -v, --version           Show script version

EXAMPLES:
    # Interactive mode with default site
    $0

    # Interactive mode for specific site
    $0 erp.production.com

    # Automated mode with custom retention
    $0 erp.production.com --comm-retention 365 --version-retention 180

    # Dry run to see what would be cleaned
    $0 --dry-run

    # Conservative cleanup (keep more data)
    $0 --comm-retention 365 --version-retention 180 --job-retention 90 --error-retention 180

RETENTION POLICIES:
    Communications: Email and notification history
    Versions: Document edit history and audit trail
    Job Logs: Background job execution logs
    Error Logs: System error and exception logs

NOTES:
    - All retention periods are in days
    - Tables are optimized after cleanup to reclaim space
    - Safe mode is temporarily disabled during cleanup
    - Run monthly or as needed to prevent database bloat

EOF
}

# Function to show version
show_version() {
    echo "ERPNext Database Cleanup Script v1.0.0"
    echo "For ERPNext v15+ with MariaDB"
}

# Function to validate site exists
validate_site() {
    local site="$1"
    local result=1
    log_info "Validating site: $site"

    # Run docker command and capture result
    docker compose -f "$PROJECT_DIR/production.yaml" -p erpnext-production exec -T backend \
      bench --site "$site" mariadb -e "SELECT 1;" >/dev/null 2>&1
    result=$?

    if [[ $result -eq 0 ]]; then
        log_info "✓ Site '$site' exists and is accessible"
        return 0
    else
        log_error "✗ Site '$site' does not exist or is not accessible"
        log_error "Available sites:"
        # List sites safely
        local sites_output
        sites_output=$(docker compose -f "$PROJECT_DIR/production.yaml" -p erpnext-production exec -T backend \
          ls sites/ 2>/dev/null | grep -v -E '\.(json|txt)$' | sed 's/^/  - /' 2>/dev/null || echo "  - Unable to list sites")
        echo "$sites_output" >&2
        return 1
    fi
}

# Function to get database size
get_db_size() {
    local size
    size=$(docker compose -f "$PROJECT_DIR/production.yaml" -p erpnext-production exec -T backend \
      bench --site "$SITE" mariadb -N -e "
      SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2)
      FROM information_schema.tables
      WHERE table_schema = DATABASE();" 2>/dev/null | tr -d '\r\n')
    echo "$size"
}

# Function to count records that would be deleted
count_records_to_delete() {
    local table_name="$1"
    local table_query="$2"
    local retention_days="$3"

    docker compose -f "$PROJECT_DIR/production.yaml" -p erpnext-production exec -T backend \
      bench --site "$SITE" mariadb -N -e "
      SET SQL_SAFE_UPDATES = 0;
      SELECT COUNT(*) FROM $table_query
      WHERE modified < DATE_SUB(NOW(), INTERVAL $retention_days DAY);" 2>/dev/null | tr -d '\r\n'
}

# Function to perform cleanup
perform_cleanup() {
    log_info "Running cleanup operations..."
    docker compose -f "$PROJECT_DIR/production.yaml" -p erpnext-production exec -T backend \
      bench --site "$SITE" mariadb <<EOF
SET SQL_SAFE_UPDATES = 0;

-- Clean old communications (emails)
DELETE FROM tabCommunication
WHERE modified < DATE_SUB(NOW(), INTERVAL $COMMUNICATION_RETENTION_DAYS DAY);

DELETE FROM \`tabCommunication Link\`
WHERE modified < DATE_SUB(NOW(), INTERVAL $COMMUNICATION_RETENTION_DAYS DAY);

-- Clean old version history
DELETE FROM tabVersion
WHERE modified < DATE_SUB(NOW(), INTERVAL $VERSION_RETENTION_DAYS DAY);

-- Clean job logs
DELETE FROM \`tabScheduled Job Log\`
WHERE modified < DATE_SUB(NOW(), INTERVAL $JOB_LOG_RETENTION_DAYS DAY);

-- Clean error logs
DELETE FROM \`tabError Log\`
WHERE modified < DATE_SUB(NOW(), INTERVAL $ERROR_LOG_RETENTION_DAYS DAY);

-- Clean deleted documents (soft deletes)
DELETE FROM \`tabDeleted Document\`
WHERE modified < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Clean route history
DELETE FROM \`tabRoute History\`
WHERE modified < DATE_SUB(NOW(), INTERVAL 90 DAY);

SET SQL_SAFE_UPDATES = 1;

-- Optimize tables to reclaim space
OPTIMIZE TABLE
  tabCommunication,
  \`tabCommunication Link\`,
  tabVersion,
  \`tabScheduled Job Log\`,
  \`tabError Log\`,
  \`tabDeleted Document\`,
  \`tabRoute History\`;
EOF
}

# Parse command line arguments
DRY_RUN=false
SITE_PROVIDED=false
SITE=""
COMMUNICATION_RETENTION_PROVIDED=false
VERSION_RETENTION_PROVIDED=false
JOB_RETENTION_PROVIDED=false
ERROR_RETENTION_PROVIDED=false
COMMUNICATION_RETENTION_DAYS=""
VERSION_RETENTION_DAYS=""
JOB_LOG_RETENTION_DAYS=""
ERROR_LOG_RETENTION_DAYS=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --comm-retention)
      COMMUNICATION_RETENTION_DAYS="$2"
      COMMUNICATION_RETENTION_PROVIDED=true
      shift 2
      ;;
    --version-retention)
      VERSION_RETENTION_DAYS="$2"
      VERSION_RETENTION_PROVIDED=true
      shift 2
      ;;
    --job-retention)
      JOB_LOG_RETENTION_DAYS="$2"
      JOB_RETENTION_PROVIDED=true
      shift 2
      ;;
    --error-retention)
      ERROR_LOG_RETENTION_DAYS="$2"
      ERROR_RETENTION_PROVIDED=true
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    -v|--version)
      show_version
      exit 0
      ;;
    -*)
      log_error "Unknown option: $1"
      log_error "Use '$0 --help' for usage information."
      exit 1
      ;;
    *)
      if [[ -z "$SITE" ]]; then
        SITE="$1"
        SITE_PROVIDED=true
      else
        log_error "Multiple sites specified. Use '$0 --help' for usage."
        exit 1
      fi
      shift
      ;;
  esac
done

# Set defaults
SITE="${SITE:-erp.localhost}"
COMMUNICATION_RETENTION_DAYS="${COMMUNICATION_RETENTION_DAYS:-$DEFAULT_COMMUNICATION_RETENTION}"
VERSION_RETENTION_DAYS="${VERSION_RETENTION_DAYS:-$DEFAULT_VERSION_RETENTION}"
JOB_LOG_RETENTION_DAYS="${JOB_LOG_RETENTION_DAYS:-$DEFAULT_JOB_LOG_RETENTION}"
ERROR_LOG_RETENTION_DAYS="${ERROR_LOG_RETENTION_DAYS:-$DEFAULT_ERROR_LOG_RETENTION}"

# Interactive mode for non-dry-run
if [[ "$DRY_RUN" == "false" ]]; then
  # Ask for site if not provided via command line
  if [[ "$SITE_PROVIDED" == "false" ]]; then
    while true; do
      read -p "Enter ERPNext site name [erp.localhost]: " USER_SITE
      SITE="${USER_SITE:-erp.localhost}"

      # Validate site (temporarily disable set -e)
      set +e
      validate_site "$SITE"
      validation_result=$?
      set -e

      if [[ $validation_result -eq 0 ]]; then
        break
      else
        echo ""
        # Use read with timeout or check if interactive
        if [[ -t 0 ]]; then
          read -p "Try a different site name? (y/n) [y]: " TRY_AGAIN
        else
          read TRY_AGAIN || TRY_AGAIN="n"  # Default to no on read failure
        fi
        TRY_AGAIN="${TRY_AGAIN:-y}"
        if [[ ! "$TRY_AGAIN" =~ ^[Yy]$ ]]; then
          log_info "Operation cancelled by user."
          exit 0
        fi
        echo ""
      fi
    done
  fi

  # Ask for retention policies if not provided
  if [[ "$COMMUNICATION_RETENTION_PROVIDED" == "false" ]]; then
    read -p "Enter retention days for communications (emails) [$DEFAULT_COMMUNICATION_RETENTION]: " COMMUNICATION_RETENTION_DAYS
    COMMUNICATION_RETENTION_DAYS="${COMMUNICATION_RETENTION_DAYS:-$DEFAULT_COMMUNICATION_RETENTION}"
  fi

  if [[ "$VERSION_RETENTION_PROVIDED" == "false" ]]; then
    read -p "Enter retention days for versions (edit history) [$DEFAULT_VERSION_RETENTION]: " VERSION_RETENTION_DAYS
    VERSION_RETENTION_DAYS="${VERSION_RETENTION_DAYS:-$DEFAULT_VERSION_RETENTION}"
  fi

  if [[ "$JOB_RETENTION_PROVIDED" == "false" ]]; then
    read -p "Enter retention days for job logs [$DEFAULT_JOB_LOG_RETENTION]: " JOB_LOG_RETENTION_DAYS
    JOB_LOG_RETENTION_DAYS="${JOB_LOG_RETENTION_DAYS:-$DEFAULT_JOB_LOG_RETENTION}"
  fi

  if [[ "$ERROR_RETENTION_PROVIDED" == "false" ]]; then
    read -p "Enter retention days for error logs [$DEFAULT_ERROR_LOG_RETENTION]: " ERROR_LOG_RETENTION_DAYS
    ERROR_LOG_RETENTION_DAYS="${ERROR_LOG_RETENTION_DAYS:-$DEFAULT_ERROR_LOG_RETENTION}"
  fi
fi

# Validate site exists (for command-line provided sites)
if [[ "$SITE_PROVIDED" == "true" ]] && ! validate_site "$SITE"; then
  exit 1
fi

# Validate inputs
for var in COMMUNICATION_RETENTION_DAYS VERSION_RETENTION_DAYS JOB_LOG_RETENTION_DAYS ERROR_LOG_RETENTION_DAYS; do
  if ! [[ ${!var} =~ ^[0-9]+$ ]] || [[ ${!var} -le 0 ]]; then
    log_error "Invalid retention days for $var: ${!var}. Must be a positive integer."
    exit 1
  fi

  # Warn about dangerous values
  if [[ ${!var} -gt 3650 ]]; then
    log_warn "Warning: $var is set to ${!var} days. This will keep a very large amount of data."
  elif [[ ${!var} -lt 7 ]]; then
    log_warn "Warning: $var is set to ${!var} days. This will delete data very aggressively."
  fi
done

# Validate inputs (aggressive check)
AGGRESSIVE_COUNT=0
for var in COMMUNICATION_RETENTION_DAYS VERSION_RETENTION_DAYS JOB_LOG_RETENTION_DAYS ERROR_LOG_RETENTION_DAYS; do
  if [[ ${!var} -lt 7 ]]; then
    AGGRESSIVE_COUNT=$((AGGRESSIVE_COUNT + 1))
  fi
done

if [[ $AGGRESSIVE_COUNT -gt 0 ]] && [[ "$DRY_RUN" == "false" ]]; then
  echo ""
  log_warn "⚠️  AGGRESSIVE CLEANUP DETECTED ⚠️"
  log_warn "You're about to delete data older than:"
  log_warn "  - Communications: $COMMUNICATION_RETENTION_DAYS days"
  log_warn "  - Versions: $VERSION_RETENTION_DAYS days"
  log_warn "  - Job logs: $JOB_LOG_RETENTION_DAYS days"
  log_warn "  - Error logs: $ERROR_LOG_RETENTION_DAYS days"
  echo ""
  read -p "This will permanently delete historical data. Continue? (yes/no): " CONFIRM
  if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "Cleanup cancelled by user."
    exit 0
  fi
  echo ""
fi

# Main execution
if [[ "$DRY_RUN" == "true" ]]; then
  log_info "DRY RUN MODE - No changes will be made"
fi

log_info "Retention policies:"
log_info "  - Communications: $COMMUNICATION_RETENTION_DAYS days"
log_info "  - Versions: $VERSION_RETENTION_DAYS days"
log_info "  - Job logs: $JOB_LOG_RETENTION_DAYS days"
log_info "  - Error logs: $ERROR_LOG_RETENTION_DAYS days"

# Get initial database size
log_info "Checking database size before cleanup..."
SIZE_BEFORE=$(get_db_size)
log_info "Database size before: ${SIZE_BEFORE} MB"

# Dry run mode
if [[ "$DRY_RUN" == "true" ]]; then
  log_info "DRY RUN: Would clean the following data older than specified retention periods:"

  # Count records for each table
  declare -A tables=(
    ["Communications"]="tabCommunication"
    ["Communication Links"]="\`tabCommunication Link\`"
    ["Versions"]="tabVersion"
    ["Job Logs"]="\`tabScheduled Job Log\`"
    ["Error Logs"]="\`tabError Log\`"
  )

  declare -A retentions=(
    ["Communications"]="$COMMUNICATION_RETENTION_DAYS"
    ["Communication Links"]="$COMMUNICATION_RETENTION_DAYS"
    ["Versions"]="$VERSION_RETENTION_DAYS"
    ["Job Logs"]="$JOB_LOG_RETENTION_DAYS"
    ["Error Logs"]="$ERROR_LOG_RETENTION_DAYS"
  )

  for table_name in "${!tables[@]}"; do
    count=$(count_records_to_delete "$table_name" "${tables[$table_name]}" "${retentions[$table_name]}")
    [[ "$count" -gt 0 ]] && log_info "  - $table_name: $count records"
  done

  # Count deleted documents and route history
  deleted_docs=$(count_records_to_delete "Deleted Documents" "\`tabDeleted Document\`" "90")
  route_history=$(count_records_to_delete "Route History" "\`tabRoute History\`" "90")

  [[ "$deleted_docs" -gt 0 ]] && log_info "  - Deleted Documents: $deleted_docs records"
  [[ "$route_history" -gt 0 ]] && log_info "  - Route History: $route_history records"

  log_info "DRY RUN complete - no changes made"
  exit 0
fi

# Perform actual cleanup
if perform_cleanup; then
  log_info "✓ Cleanup completed successfully"
else
  log_error "✗ Cleanup failed"
  exit 1
fi

# Get final database size
log_info "Checking database size after cleanup..."
SIZE_AFTER=$(get_db_size)
log_info "Database size after: ${SIZE_AFTER} MB"

# Calculate savings
SAVED=$(echo "$SIZE_BEFORE - $SIZE_AFTER" | bc 2>/dev/null || echo "0")
PERCENT=$(echo "scale=2; ($SAVED / $SIZE_BEFORE) * 100" | bc 2>/dev/null || echo "0.00")

log_info "✓ Cleanup complete!"
log_info "  Space recovered: ${SAVED} MB (${PERCENT}%)"

exit 0