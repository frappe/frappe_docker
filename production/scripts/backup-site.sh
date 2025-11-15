#!/bin/bash

# Backup ERPNext Site Script
# Usage: ./backup-site.sh <site-name> [options]

set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_debug() { [[ "${DEBUG:-0}" == "1" ]] && echo -e "${BLUE}[DEBUG]${NC} $1" || true; }
log_action() { echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "/tmp/erpnext-backup-$(date '+%Y%m%d').log"; }

cleanup() {
	local exit_code=$?
	if [[ $exit_code -ne 0 ]]; then
		echo_error "Script failed with exit code $exit_code"
		log_action "FAILED: ${SITE_NAME:-unknown}"
	fi
	exit $exit_code
}
trap cleanup EXIT

# Configuration
PROJECT_NAME="${PROJECT_NAME:-erpnext-production}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
HOST_BACKUP_ROOT="${HOST_BACKUP_ROOT:-./backups}"
HOST_BACKUP_LAYOUT="${HOST_BACKUP_LAYOUT:-flat}"
AUTO_COPY="${AUTO_COPY:-0}"
CLEANUP_OLD="${CLEANUP_OLD:-0}"
CLEANUP_POLICY="${CLEANUP_POLICY:-}"
HOST_ONLY="${HOST_ONLY:-0}"
COMPOSE_FILE="${COMPOSE_FILE:-production.yaml}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_PATH="$PRODUCTION_DIR/$COMPOSE_FILE"

cd "$PRODUCTION_DIR"

[[ -f "$COMPOSE_PATH" ]] || { echo_error "Compose file '$COMPOSE_PATH' not found"; exit 1; }

dc_exec() { docker compose --project-name "$PROJECT_NAME" -f "$COMPOSE_PATH" exec backend "$@"; }
dc_cmd()  { docker compose --project-name "$PROJECT_NAME" -f "$COMPOSE_PATH" "$@"; }

show_help() {
	cat <<EOF
Usage: $0 <site-name> [options]

Options:
	--with-files             Include public/private files in the bench backup
	--compress               Compress the SQL dump (bench flag)
	--auto-copy              Copy the new backup files to the host (flat layout by default)
	--flat-host-path         Store host copies directly in \$HOST_BACKUP_ROOT (default)
	--nested-host-path       Store host copies in \$HOST_BACKUP_ROOT/<site>/<timestamp>/
	--host-only              Delete container copies after a successful host copy
	--cleanup-old[=policy]   Remove stale backups. Policy examples:
							   (empty) → BACKUP_RETENTION_DAYS days
							   7       → files older than 7 days
							   keep:5  → keep newest 5 runs
							   latest  → keep only backups from this run
	--retention-days N       Deprecated alias for --cleanup-old N
	--encrypt                Encrypt host copies with GPG (needs BACKUP_PASSPHRASE)
	--debug                  Verbose logging
	-h, --help               Show this help

Environment Variables:
	PROJECT_NAME             Docker Compose project name (default: erpnext-production)
	BACKUP_RETENTION_DAYS    Default days to keep when no policy passed (default: 30)
	HOST_BACKUP_ROOT         Host destination directory (default: ./backups)
	HOST_BACKUP_LAYOUT       "flat" (default) or "nested"
	AUTO_COPY                Set to 1 to copy on every run
	HOST_ONLY                Set to 1 to delete container copies when AUTO_COPY=1
	CLEANUP_OLD              Set to 1 to always prune when script runs
	CLEANUP_POLICY           Default cleanup policy (keep:7, latest, etc.)
	BACKUP_PASSPHRASE        Required when --encrypt is used
	COMPOSE_FILE             Compose file relative to production/ (default: production.yaml)

Examples:
	$0 erp.example.com --with-files --auto-copy --cleanup-old keep:7
	$0 erp.example.com --with-files --auto-copy --host-only --cleanup-old latest
	AUTO_COPY=1 CLEANUP_OLD=1 CLEANUP_POLICY=keep:5 $0 erp.example.com
EOF
}

require_int() {
	local value="$1"; shift
	[[ "$value" =~ ^[0-9]+$ ]] || { echo_error "$*"; exit 1; }
}

set_policy() {
	[[ "$CLEANUP_OLD" -ne 1 ]] && { CLEANUP_MODE=""; CLEANUP_VALUE=""; return; }

	local policy_value="$1"
	[[ -z "$policy_value" ]] && policy_value="$BACKUP_RETENTION_DAYS"

	case "$policy_value" in
		latest|keep-latest)
			CLEANUP_MODE="keep"
			CLEANUP_VALUE=1
			;;
		keep:*)
			local keep_count="${policy_value#keep:}"
			require_int "$keep_count" "keep:<n> expects an integer"
			(( keep_count < 1 )) && keep_count=1
			CLEANUP_MODE="keep"
			CLEANUP_VALUE="$keep_count"
			;;
		days:*)
			local day_count="${policy_value#days:}"
			require_int "$day_count" "days:<n> expects an integer"
			CLEANUP_MODE="days"
			CLEANUP_VALUE="$day_count"
			;;
		"")
			CLEANUP_MODE="days"
			CLEANUP_VALUE="$BACKUP_RETENTION_DAYS"
			;;
		*)
			if [[ "$policy_value" =~ ^[0-9]+$ ]]; then
				if [[ "$policy_value" -eq 0 ]]; then
					CLEANUP_MODE="keep"
					CLEANUP_VALUE=1
				else
					CLEANUP_MODE="days"
					CLEANUP_VALUE="$policy_value"
				fi
			else
				echo_error "Invalid cleanup policy: $policy_value"
				exit 1
			fi
			;;
	esac
}

cleanup_container_days() {
	local days="$1"
	local minutes=$((days * 1440))
	echo_info "Pruning container backups older than $days day(s)"
	dc_exec bash -lc "find '$BACKUP_PATH' -maxdepth 1 -type f -mmin +$minutes -delete" || true
}

cleanup_container_keep() {
	local keep_runs="$1"
	echo_info "Keeping newest $keep_runs container backup run(s)"
	mapfile -t prefixes < <(dc_exec bash -lc "cd '$BACKUP_PATH' && ls -1t 2>/dev/null | awk -F'-' '!seen[$1]++ {print $1}'") || true
	if [[ ${#prefixes[@]} -le $keep_runs ]]; then
		echo_info "Nothing to prune in container"
		return
	fi
	prefixes=(${prefixes[@]:$keep_runs})
	for prefix in "${prefixes[@]}"; do
		[[ -z "$prefix" ]] && continue
		dc_exec bash -lc "find '$BACKUP_PATH' -maxdepth 1 -type f -name '${prefix}-*' -delete"
	done
}

cleanup_host_days() {
	local days="$1"
	if [[ "$HOST_LAYOUT_MODE" == "nested" ]]; then
		[[ -d "$HOST_SITE_ROOT" ]] || return
		echo_info "Pruning host backups older than $days day(s)"
		find "$HOST_SITE_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +$days -print -exec rm -rf {} + || true
	else
		[[ -d "$HOST_BACKUP_ROOT" ]] || return
		echo_info "Pruning host backup files older than $days day(s)"
		find "$HOST_BACKUP_ROOT" -maxdepth 1 -type f -name "*-${SITE_FILE_KEY}-*" -mtime +$days -print -delete || true
	fi
}

cleanup_host_keep() {
	local keep_runs="$1"
	if [[ "$HOST_LAYOUT_MODE" == "nested" ]]; then
		[[ -d "$HOST_SITE_ROOT" ]] || return
		mapfile -t dirs < <(ls -1dt "$HOST_SITE_ROOT"/* 2>/dev/null) || true
		if [[ ${#dirs[@]} -le $keep_runs ]]; then
			return
		fi
		echo_info "Keeping newest $keep_runs host backup run(s)"
		for dir in "${dirs[@]:$keep_runs}"; do
			rm -rf "$dir"
		done
	else
		[[ -d "$HOST_BACKUP_ROOT" ]] || return
		mapfile -t prefixes < <(find "$HOST_BACKUP_ROOT" -maxdepth 1 -type f -name "*-${SITE_FILE_KEY}-*" -printf '%f\n' | sort -r | awk -F'-' '!seen[$1]++ {print $1}') || true
		if [[ ${#prefixes[@]} -le $keep_runs ]]; then
			return
		fi
		echo_info "Keeping newest $keep_runs host backup run(s)"
		prefixes=(${prefixes[@]:$keep_runs})
		for prefix in "${prefixes[@]}"; do
			find "$HOST_BACKUP_ROOT" -maxdepth 1 -type f -name "${prefix}-${SITE_FILE_KEY}-*" -delete
		done
	fi
}

copy_backups_to_host() {
	[[ "$AUTO_COPY" -ne 1 ]] && return
	[[ ${#BACKUP_FILES[@]} -eq 0 ]] && return

	local dest
	if [[ "$HOST_LAYOUT_MODE" == "nested" ]]; then
		dest="$HOST_SITE_ROOT/$CURRENT_PREFIX"
	else
		dest="$HOST_BACKUP_ROOT"
	fi
	mkdir -p "$dest"

	BACKEND_CONTAINER=$(dc_cmd ps -q backend)
	[[ -z "$BACKEND_CONTAINER" ]] && { echo_error "Backend container not running"; exit 1; }

	HOST_RUN_FILES=()
	for file_path in "${BACKUP_FILES[@]}"; do
		local base target
		base=$(basename "$file_path")
		target="$dest/$base"
		if docker cp "${BACKEND_CONTAINER}:${file_path}" "$target" 2>/dev/null; then
			echo_info "  → Copied $base"
			HOST_RUN_FILES+=("$target")
		else
			echo_warn "  ✗ Failed to copy $base"
		fi
	done

	if [[ ${#HOST_RUN_FILES[@]} -gt 0 ]]; then
		HOST_COPY_SUCCESS=1
		HOST_RUN_DIR="$dest"
		echo_info "✓ Host copy complete: $dest"
	else
		echo_warn "No files copied to host"
	fi
}

encrypt_host_backups() {
	[[ "$ENCRYPT" -ne 1 ]] && return
	[[ "$HOST_COPY_SUCCESS" -ne 1 ]] && { echo_warn "Cannot encrypt – host copy missing"; return; }

	command -v gpg >/dev/null 2>&1 || { echo_error "GPG not installed"; exit 1; }
	[[ -z "${BACKUP_PASSPHRASE:-}" ]] && { echo_error "BACKUP_PASSPHRASE not set"; exit 1; }

	local encrypted=0
	for backup_file in "${HOST_RUN_FILES[@]}"; do
		[[ -f "$backup_file" ]] || continue
		if echo "$BACKUP_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
			--symmetric --cipher-algo AES256 -o "${backup_file}.gpg" "$backup_file"; then
			rm -f "$backup_file"
			((encrypted++))
			echo_info "  ✓ Encrypted $(basename "${backup_file}.gpg")"
		else
			echo_warn "  ✗ Encryption failed for $(basename "$backup_file")"
		fi
	done

	echo_info "Encrypted $encrypted file(s)"
	log_action "SUCCESS: Encrypted $encrypted files"
}

remove_container_backups() {
	[[ "$HOST_ONLY" -ne 1 ]] && return
	echo_info "Removing container backups (host-only mode)"
	dc_exec bash -lc "find '$BACKUP_PATH' -maxdepth 1 -type f -delete" || true
}

verify_backup_presence() {
	if [[ "$AUTO_COPY" -eq 1 ]]; then
		if [[ "$HOST_COPY_SUCCESS" -ne 1 ]] || [[ ${#HOST_RUN_FILES[@]} -eq 0 ]]; then
			echo_error "Host backup missing after copy attempt"
			exit 1
		fi
		for backup_file in "${HOST_RUN_FILES[@]}"; do
			[[ -f "$backup_file" || -f "${backup_file}.gpg" ]] && continue
			echo_error "Host backup file missing: $(basename "$backup_file")"
			exit 1
		done
	else
		for base in "${BACKUP_BASENAMES[@]}"; do
			if ! dc_exec test -f "$BACKUP_PATH/$base"; then
				echo_error "Container backup file missing: $base"
				exit 1
			fi
		done
	fi
}

print_host_summary() {
	[[ "$AUTO_COPY" -ne 1 ]] && { echo_info "Use --auto-copy to mirror backups onto the host"; return; }
	if [[ "$HOST_LAYOUT_MODE" == "nested" ]]; then
		echo_info "Latest host backups:"
		ls -lht "$HOST_SITE_ROOT" 2>/dev/null | head -n 6 || true
	else
		echo_info "Latest host backup files:"
		if [[ -d "$HOST_BACKUP_ROOT" ]]; then
			(ls -lht "$HOST_BACKUP_ROOT" 2>/dev/null | grep "$SITE_FILE_KEY" | head -n 6) || true
		fi
	fi
}

# Runtime values
SITE_NAME=""
WITH_FILES=0
COMPRESS=0
ENCRYPT=0
DEBUG="${DEBUG:-0}"
CLEANUP_MODE=""
CLEANUP_VALUE=""
HOST_LAYOUT_OVERRIDE=""
HOST_LAYOUT_MODE=""
HOST_SITE_ROOT=""
SITE_SAFE_NAME=""
SITE_FILE_KEY=""
BACKUP_PATH=""
MARKER=""
CURRENT_PREFIX=""
BACKEND_CONTAINER=""
HOST_COPY_SUCCESS=0
HOST_RUN_DIR=""
declare -a BACKUP_FILES=()
declare -a BACKUP_BASENAMES=()
declare -a HOST_RUN_FILES=()

# Parse arguments
while [[ $# -gt 0 ]]; do
	case "$1" in
		-h|--help) show_help; exit 0 ;;
		--with-files) WITH_FILES=1; shift ;;
		--compress) COMPRESS=1; shift ;;
		--auto-copy) AUTO_COPY=1; shift ;;
		--host-only) HOST_ONLY=1; AUTO_COPY=1; shift ;;
		--flat-host-path) AUTO_COPY=1; HOST_LAYOUT_OVERRIDE="flat"; shift ;;
		--nested-host-path) AUTO_COPY=1; HOST_LAYOUT_OVERRIDE="nested"; shift ;;
		--cleanup-old)
			CLEANUP_OLD=1
			if [[ -n "${2:-}" && ! "${2}" =~ ^- ]]; then
				CLEANUP_POLICY="$2"
				shift 2
			else
				shift
			fi
			;;
		--cleanup-old=*)
			CLEANUP_OLD=1
			CLEANUP_POLICY="${1#*=}"
			shift
			;;
		--retention-days)
			CLEANUP_OLD=1
			[[ -n "${2:-}" ]] || { echo_error "--retention-days needs an integer"; exit 1; }
			CLEANUP_POLICY="$2"
			shift 2
			;;
		--retention-days=*)
			CLEANUP_OLD=1
			CLEANUP_POLICY="${1#*=}"
			shift
			;;
		--encrypt) ENCRYPT=1; shift ;;
		--debug) DEBUG=1; shift ;;
		*)
			if [[ -z "$SITE_NAME" ]]; then
				SITE_NAME="$1"
				shift
			else
				echo_error "Unknown argument: $1"
				show_help
				exit 1
			fi
			;;
	esac
done

if [[ -z "$SITE_NAME" ]]; then
	read -rp "Enter site name (e.g., erp.example.com): " SITE_NAME
fi

[[ -z "$SITE_NAME" ]] && { echo_error "Site name is required"; exit 1; }

[[ "$BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ ]] || { echo_error "BACKUP_RETENTION_DAYS must be a non-negative integer"; exit 1; }

HOST_LAYOUT_MODE="${HOST_LAYOUT_OVERRIDE:-$HOST_BACKUP_LAYOUT}"
HOST_LAYOUT_MODE="${HOST_LAYOUT_MODE,,}"
case "$HOST_LAYOUT_MODE" in
	flat|nested) ;;
	*) echo_warn "Unknown HOST_BACKUP_LAYOUT '$HOST_LAYOUT_MODE', defaulting to flat"; HOST_LAYOUT_MODE="flat" ;;
esac

SITE_SAFE_NAME="${SITE_NAME//[^A-Za-z0-9._-]/_}"
SITE_FILE_KEY="$(echo "$SITE_NAME" | sed 's/[^A-Za-z0-9]/_/g')"
HOST_SITE_ROOT="$HOST_BACKUP_ROOT/$SITE_SAFE_NAME"
BACKUP_PATH="/home/frappe/frappe-bench/sites/$SITE_NAME/private/backups"
MARKER="/tmp/backup-${SITE_NAME//[^A-Za-z0-9]/-}-$$.marker"

set_policy "$CLEANUP_POLICY"

echo_debug "Site: $SITE_NAME"
docker info >/dev/null 2>&1 || { echo_error "Docker not running"; exit 1; }
dc_exec echo "test" >/dev/null 2>&1 || { echo_error "Backend container not running"; exit 1; }

echo_info "Verifying site: $SITE_NAME"
if ! dc_exec bench --site "$SITE_NAME" list-apps >/dev/null 2>&1; then
	echo_error "Site '$SITE_NAME' not found"
	exit 1
fi

dc_exec bash -lc "touch '$MARKER'"

echo_info "Creating backup for: $SITE_NAME"
log_action "STARTED: $SITE_NAME"

bench_cmd=(bench --site "$SITE_NAME" backup)
(( WITH_FILES )) && bench_cmd+=(--with-files)
(( COMPRESS )) && bench_cmd+=(--compress)

if ! dc_exec "${bench_cmd[@]}"; then
	echo_error "Backup command failed"
	log_action "FAILED: backup command"
	exit 1
fi

mapfile -t BACKUP_FILES < <(dc_exec bash -lc "find '$BACKUP_PATH' -maxdepth 1 -type f -newer '$MARKER' -print") || true
dc_exec bash -lc "rm -f '$MARKER'" || true

if [[ ${#BACKUP_FILES[@]} -eq 0 ]]; then
	echo_error "No backup files detected"
	log_action "FAILED: no files"
	exit 1
fi

TOTAL_SIZE=0
for file_path in "${BACKUP_FILES[@]}"; do
	[[ -z "$file_path" ]] && continue
	base=$(basename "$file_path")
	BACKUP_BASENAMES+=("$base")
	size_bytes=$(dc_exec stat -c%s "$file_path" 2>/dev/null | tr -d '\r' || echo "0")
	TOTAL_SIZE=$((TOTAL_SIZE + size_bytes))
	size_hr=$(numfmt --to=iec-i --suffix=B "$size_bytes" 2>/dev/null || echo "$size_bytes bytes")
	echo_info "  - $base ($size_hr)"
done

CURRENT_PREFIX="${BACKUP_BASENAMES[0]%%-*}"
[[ -z "$CURRENT_PREFIX" ]] && CURRENT_PREFIX="$(date '+%Y%m%d_%H%M%S')"

[[ $TOTAL_SIZE -gt 0 ]] && echo_info "Total size: $(numfmt --to=iec-i --suffix=B "$TOTAL_SIZE" 2>/dev/null || echo "$TOTAL_SIZE bytes")"
log_action "SUCCESS: ${#BACKUP_FILES[@]} files, $TOTAL_SIZE bytes"

if [[ "$AUTO_COPY" -eq 1 ]]; then
	if [[ "$HOST_LAYOUT_MODE" == "nested" ]]; then
		echo_info "Copying backups to $HOST_SITE_ROOT/$CURRENT_PREFIX"
	else
		echo_info "Copying backups to $HOST_BACKUP_ROOT"
	fi
	copy_backups_to_host
	encrypt_host_backups
else
	echo_info "Backups stored inside container: $BACKUP_PATH"
fi

remove_container_backups

if [[ "$CLEANUP_OLD" -eq 1 ]]; then
	if [[ "$CLEANUP_MODE" == "days" ]]; then
		cleanup_container_days "$CLEANUP_VALUE"
		[[ "$AUTO_COPY" -eq 1 ]] && cleanup_host_days "$CLEANUP_VALUE"
	elif [[ "$CLEANUP_MODE" == "keep" ]]; then
		cleanup_container_keep "$CLEANUP_VALUE"
		[[ "$AUTO_COPY" -eq 1 ]] && cleanup_host_keep "$CLEANUP_VALUE"
	fi
fi

verify_backup_presence
print_host_summary

echo_info "✓ Backup completed successfully!"
