#!/bin/bash

# Add cron job to run Google Drive backup daily at 2 AM
CRON_JOB="0 2 * * * $(pwd)/run-gdrive-backup.sh >> $(pwd)/gdrive-backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run-gdrive-backup.sh"; then
  echo "Google Drive backup cron job already exists"
else
  # Add new cron job
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  echo "Google Drive backup cron job added"
fi 