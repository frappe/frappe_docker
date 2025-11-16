#!/bin/bash

# Build custom Frappe Docker image with ERPNext and HRMS
# This script builds a custom image using the apps.json file

set -e

echo "Building custom Frappe image with ERPNext and HRMS..."

# Check if apps.json exists
if [ ! -f "apps.json" ]; then
    echo "Error: apps.json file not found!"
    exit 1
fi

# Encode apps.json to base64
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    APPS_JSON_BASE64=$(base64 -i apps.json)
else
    # Linux
    APPS_JSON_BASE64=$(base64 -w 0 apps.json)
fi

echo "Building image for AMD64 architecture (for Windows Server deployment)..."
echo "This may take 15-30 minutes depending on your system..."

# Build the image using layered Containerfile
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --platform=linux/amd64 \
  --tag=frappe-custom:v15 \
  --file=images/layered/Containerfile .

echo ""
echo "✅ Build complete!"
echo "Image tagged as: frappe-custom:v15"
echo ""
echo "Next steps:"
echo "1. Run: docker compose -f pwd.yml up -d"
echo "2. Wait for all services to start (2-3 minutes)"
echo "3. Access ERPNext at: http://localhost:8080"
echo "   Username: Administrator"
echo "   Password: admin"

