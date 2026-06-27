#!/bin/bash
echo "Installing CosmOS ERP Server..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    exit 1
fi
export $(grep -v '^#' .env | xargs)
echo "Starting containers..."
docker compose up -d
echo "Deployment complete. Ensure image custom/cosmos:v16.23.2 is present."
