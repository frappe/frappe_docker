#!/bin/bash
set -e

ASSETS_DIR="/home/frappe/frappe-bench/sites/assets"
APPS_DIR="/home/frappe/frappe-bench/apps"

echo "Syncing assets from apps to shared volume..."

for app in frappe erpnext hrms lms education lending newsletter drive helpdesk; do
    echo "Syncing $app..."
    rm -rf "$ASSETS_DIR/$app"
    mkdir -p "$ASSETS_DIR/$app/dist"
    cp -r "$APPS_DIR/$app/$app/public/dist/"* "$ASSETS_DIR/$app/dist/" 2>/dev/null || true
    
    if [ -d "$APPS_DIR/$app/$app/public/images" ]; then
        mkdir -p "$ASSETS_DIR/$app/images"
        cp -r "$APPS_DIR/$app/$app/public/images/"* "$ASSETS_DIR/$app/images/" 2>/dev/null || true
    fi
    
    if [ -d "$APPS_DIR/$app/$app/public/icons" ]; then
        mkdir -p "$ASSETS_DIR/$app/icons"
        cp -r "$APPS_DIR/$app/$app/public/icons/"* "$ASSETS_DIR/$app/icons/" 2>/dev/null || true
    fi
    
    if [ -d "$APPS_DIR/$app/$app/public/manifest" ]; then
        mkdir -p "$ASSETS_DIR/$app/manifest"
        cp -r "$APPS_DIR/$app/$app/public/manifest/"* "$ASSETS_DIR/$app/manifest/" 2>/dev/null || true
    fi
done

echo "Assets synced successfully"
