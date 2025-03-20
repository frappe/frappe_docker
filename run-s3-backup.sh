#!/bin/bash

# Path to your S3 backup configuration
S3_BACKUP_FILE="s3-backup.yaml"

# Run the backup with appropriate environment variables
docker compose -f $S3_BACKUP_FILE --env-file backup.env up backup

echo "S3 backup completed at $(date)" 