# Download backups from production server

# Load environment variables from .env file
source .env

sshpass -p "$HETZNER_SSH_PASSWORD" scp -r root@188.245.211.114:/var/lib/docker/volumes/frappe-deployment_sites/_data/qa.ignis.academy/private/backups/ ./development
