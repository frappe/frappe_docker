# Download backups from production server

# Check if site name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <site_name>"
    echo "Example: $0 qa.ignis.academy"
    exit 1
fi

SITE_NAME="$1"

# Load environment variables from .env file
source .env

sshpass -p "$HETZNER_SSH_PASSWORD" scp -r root@188.245.211.114:/var/lib/docker/volumes/frappe-deployment_sites/_data/${SITE_NAME}/private/backups/ ./development
