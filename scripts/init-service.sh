#!/bin/bash

# Simple service initialization for Frappe services
# This script runs on services that don't need to create sites

set -e

SERVICE_NAME=${1:-"frappe-service"}

echo "🔧 Initializing $SERVICE_NAME..."
cd /home/frappe/frappe-bench

# Basic configuration (site creation handled by backend service)
if [ -f sites/common_site_config.json ] && [ -n "${FRAPPE_SITE_NAME_HEADER}" ]; then
    if [ -d "sites/${FRAPPE_SITE_NAME_HEADER}" ]; then
        bench use "${FRAPPE_SITE_NAME_HEADER}" || echo "Site will be set by backend"
    fi
fi

echo "✅ $SERVICE_NAME ready"