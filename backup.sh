#!/bin/bash

# Path to your docker-compose files
COMPOSE_FILES="-f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.https.yaml"

# Create backup with files
docker compose $COMPOSE_FILES exec backend bench --site all backup --with-files

# Optional: Copy backups to a local directory outside the Docker volume
# Create a backups directory if it doesn't exist
mkdir -p ./backups
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
docker compose $COMPOSE_FILES exec backend mkdir -p /home/frappe/frappe-bench/backups-export
docker compose $COMPOSE_FILES exec backend cp -r /home/frappe/frappe-bench/sites/*/backup/* /home/frappe/frappe-bench/backups-export/

# Copy the backups from the container to the host
docker compose $COMPOSE_FILES cp backend:/home/frappe/frappe-bench/backups-export/ ./backups/$TIMESTAMP

# Cleanup the temporary directory in the container
docker compose $COMPOSE_FILES exec backend rm -rf /home/frappe/frappe-bench/backups-export

echo "Backup completed at ./backups/$TIMESTAMP"

# Optional: Implement backup rotation/cleanup to prevent using too much disk space
# Keep only the last 7 days of backups
find ./backups -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true 