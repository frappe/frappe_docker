# Download backups from production server

# Check if site name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <site_name>"
    echo "Example: $0 qa.ignis.academy"
    exit 1
fi

SITE_NAME="$1"
SERVER="root@188.245.211.114"
LIVE_PATH="/var/lib/docker/volumes/frappe-deployment_sites/_data/${SITE_NAME}/private/backups/"
ARCHIVED_PATH="/home/frappe/frappe-bench/archived/sites/${SITE_NAME}/private/backups"

# Load environment variables from .env file
source .env

# Function to download from archived location
download_from_archive() {
    echo "Checking archived location..."
    if sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "docker exec frappe-deployment-backend-1 test -d '${ARCHIVED_PATH}'"; then
        echo "Site is archived. Downloading from archived location..."

        # Copy from container to host temp location, then scp to local
        TEMP_DIR="/tmp/backup_${SITE_NAME}"
        sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "rm -rf ${TEMP_DIR} && docker cp frappe-deployment-backend-1:${ARCHIVED_PATH} ${TEMP_DIR}"
        sshpass -p "$HETZNER_SSH_PASSWORD" scp -r "${SERVER}:${TEMP_DIR}" ./development/backups
        sshpass -p "$HETZNER_SSH_PASSWORD" ssh "$SERVER" "rm -rf ${TEMP_DIR}"

        echo "Download complete."
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
        sshpass -p "$HETZNER_SSH_PASSWORD" scp -r "${SERVER}:${LIVE_PATH}" ./development
        echo "Download complete."
    else
        echo "Site is live but has no backup files."
        download_from_archive
    fi
else
    echo "Site is not live."
    download_from_archive
fi
