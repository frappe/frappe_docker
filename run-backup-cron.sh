#!/bin/bash

# Path to your docker-compose files
COMPOSE_FILES="-f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.https.yaml -f overrides/compose.backup-cron.yaml"

# Start the backup cron service
docker compose --env-file backup.env $COMPOSE_FILES up -d cron 