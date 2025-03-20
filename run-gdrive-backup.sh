#!/bin/bash

# Path to your Google Drive backup configuration
GDRIVE_BACKUP_FILE="gdrive-backup.yaml"

# Run the backup with Google Drive environment variables
docker compose -f $GDRIVE_BACKUP_FILE --env-file gdrive-backup.env up backup

echo "Google Drive backup completed at $(date)" 