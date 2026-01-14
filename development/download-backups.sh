# Download backups from production server
#
# Usage: ./download-backups.sh <site_name> [backup_timestamp]
#
# Arguments:
#   site_name         Required. The site to download backups for (e.g., qa.ignis.academy)
#   backup_timestamp  Optional. Specific backup timestamp to download (e.g., 20260114_150602)
#                     If not provided, downloads the latest backup set.
#
# Examples:
#   ./download-backups.sh qa.ignis.academy                    # Download latest backup
#   ./download-backups.sh qa.ignis.academy 20260114_150602    # Download specific backup
#
# The script will:
#   1. Check if the site is live (has backups in the Docker volume)
#   2. If not live or no backups, check the archived sites folder
#   3. For archived sites, find the latest archive directory matching the site name
#   4. Download only files matching the specified/latest backup timestamp to the development/backups folder
#
# Requires: HETZNER_SSH_PASSWORD environment variable set in .env file
# Requires: sshpass (sudo apt install sshpas)

# Check if site name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <site_name> [backup_timestamp]"
    echo "Example: $0 qa.ignis.academy"
    echo "Example: $0 qa.ignis.academy 20260114_150602"
    exit 1
fi

SITE_NAME="$1"
BACKUP_TIMESTAMP="${2:-}"  # Optional: specific backup timestamp to download
SERVER="root@188.245.211.114"
LIVE_PATH="/var/lib/docker/volumes/frappe-deployment_sites/_data/${SITE_NAME}/private/backups/"

# Load environment variables from .env file
source .env

# Function to download only the latest backup set (files with the same timestamp prefix)
# Args: $1 = backup path, $2 = "true" if path is inside container, "false" if on host
download_latest_backup_set() {
    local BACKUP_PATH="$1"
    local IS_CONTAINER="$2"
    local PREFIX=""

    if [ -n "$BACKUP_TIMESTAMP" ]; then
        # Verify the provided timestamp exists
        PREFIX="$BACKUP_TIMESTAMP"
        echo "Looking for backup timestamp: ${PREFIX}"

        if [ "$IS_CONTAINER" = "true" ]; then
            FILE_COUNT=$(sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "docker exec frappe-deployment-backend-1 sh -c \"ls ${BACKUP_PATH}/${PREFIX}* 2>/dev/null | wc -l\"")
        else
            FILE_COUNT=$(sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "ls ${BACKUP_PATH}/${PREFIX}* 2>/dev/null | wc -l")
        fi

        if [ "$FILE_COUNT" -eq 0 ]; then
            echo "Error: No backup files found with timestamp ${PREFIX} in ${BACKUP_PATH}."
            return 1
        fi
        echo "Found ${FILE_COUNT} files with timestamp: ${PREFIX}"
    else
        # Find the latest backup timestamp
        if [ "$IS_CONTAINER" = "true" ]; then
            # Get latest prefix from inside container
            PREFIX=$(sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "docker exec frappe-deployment-backend-1 sh -c \"ls -t ${BACKUP_PATH}/ 2>/dev/null | head -1 | cut -d'-' -f1\"")
        else
            # Get latest prefix from host filesystem
            PREFIX=$(sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "ls -t ${BACKUP_PATH}/ 2>/dev/null | head -1 | cut -d'-' -f1")
        fi
        echo "Found latest backup set: ${PREFIX}"
    fi

    if [ -z "$PREFIX" ]; then
        echo "Error: No backup files found in ${BACKUP_PATH}."
        return 1
    fi

    LATEST_PREFIX="$PREFIX"

    TEMP_DIR="/tmp/backup_${SITE_NAME}"
    mkdir -p ./development/backups

    if [ "$IS_CONTAINER" = "true" ]; then
        # Copy from container: use tar to stream only matching files
        sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "rm -rf ${TEMP_DIR} && mkdir -p ${TEMP_DIR} && docker exec frappe-deployment-backend-1 sh -c 'cd ${BACKUP_PATH} && tar cf - ${LATEST_PREFIX}*' | tar xf - -C ${TEMP_DIR}"
    else
        # Copy from host: copy only matching files to temp dir
        sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "rm -rf ${TEMP_DIR} && mkdir -p ${TEMP_DIR} && cp ${BACKUP_PATH}/${LATEST_PREFIX}* ${TEMP_DIR}/"
    fi

    sshpass -p "$HETZNER_SSH_PASSWORD" scp "${SERVER}:${TEMP_DIR}/"* ./development/backups/
    sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "rm -rf ${TEMP_DIR}"

    echo "Download complete."
}

# Function to download from archived location
download_from_archive() {
    echo "Checking archived location..."

    ARCHIVED_BASE="/home/frappe/frappe-bench/archived/sites"

    # Find the latest archived directory matching the site name pattern (sorted by modification time)
    LATEST_ARCHIVED=$(sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "docker exec frappe-deployment-backend-1 sh -c \"ls -td ${ARCHIVED_BASE}/${SITE_NAME}* 2>/dev/null | head -1\"")

    if [ -n "$LATEST_ARCHIVED" ]; then
        ARCHIVED_BACKUP_PATH="${LATEST_ARCHIVED}/private/backups"
        echo "Found latest archived site: ${LATEST_ARCHIVED}"

        # Check if backup directory exists in the archived site
        if sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "docker exec frappe-deployment-backend-1 test -d '${ARCHIVED_BACKUP_PATH}'"; then
            echo "Downloading from archived location..."
            download_latest_backup_set "$ARCHIVED_BACKUP_PATH" "true"
        else
            echo "Error: Backup directory not found in archived site ${LATEST_ARCHIVED}."
            exit 1
        fi
    else
        echo "Error: Site ${SITE_NAME} not found in live or archived locations."
        exit 1
    fi
}

# Check if live site exists and has backup files
echo "Checking if site ${SITE_NAME} is live..."
if sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "[ -d '$LIVE_PATH' ]"; then
    # Check if backup directory has files
    if sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "[ -n \"\$(ls -A '$LIVE_PATH' 2>/dev/null)\" ]"; then
        echo "Site is live with backup files. Downloading from live location..."
        download_latest_backup_set "$LIVE_PATH" "false"
    else
        echo "Site is live but has no backup files."
        download_from_archive
    fi
else
    echo "Site is not live."
    download_from_archive
fi
