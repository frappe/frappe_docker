#!/bin/bash

# Frappe/ERPNext Site Installation Script
# This script creates and configures a new Frappe site with ERPNext and custom apps
# Runs during Zerops deployment before starting application services

set -e

echo "🚀 Starting Frappe site installation..."

# Configuration from environment variables
SITE_NAME=${FRAPPE_SITE_NAME_HEADER:-"localhost"}
DB_PASSWORD=${DB_PASSWORD:-"admin"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"admin"}
DB_HOST=${DB_HOST:-"db"}
DB_PORT=${DB_PORT:-"3306"}

echo "📋 Site Configuration:"
echo "  - Site Name: $SITE_NAME"
echo "  - Database Host: $DB_HOST:$DB_PORT"
echo "  - Admin Password: [CONFIGURED]"

# Start with a fresh container to install the site
echo "📦 Starting temporary Frappe container for site installation..."

# Run the installation inside a Docker container
docker compose -f docker-compose.zerops.yaml run --rm -e FRAPPE_SITE_NAME_HEADER="$SITE_NAME" \
  -e DB_HOST="$DB_HOST" -e DB_PORT="$DB_PORT" -e DB_PASSWORD="$DB_PASSWORD" \
  -e ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  configurator bash -c '
    echo "🏗️  Setting up Frappe configuration..."
    
    # Navigate to bench directory
    cd /home/frappe/frappe-bench
    
    # Set up basic configuration
    ls -1 apps > sites/apps.txt
    bench set-config -g db_host $DB_HOST
    bench set-config -gp db_port $DB_PORT
    bench set-config -g redis_cache "redis://$REDIS_CACHE"
    bench set-config -g redis_queue "redis://$REDIS_QUEUE"
    bench set-config -g redis_socketio "redis://$REDIS_QUEUE"
    bench set-config -gp socketio_port $SOCKETIO_PORT
    
    echo "✅ Frappe configuration completed"
    
    # Check if site already exists
    if [ ! -d "sites/$FRAPPE_SITE_NAME_HEADER" ]; then
      echo "🆕 Creating new site: $FRAPPE_SITE_NAME_HEADER"
      
      bench new-site "$FRAPPE_SITE_NAME_HEADER" \
        --mariadb-root-password "$DB_PASSWORD" \
        --admin-password "$ADMIN_PASSWORD" \
        --no-mariadb-socket
      
      echo "✅ Site created successfully"
      
      echo "📦 Installing ERPNext app..."
      bench --site "$FRAPPE_SITE_NAME_HEADER" install-app erpnext
      echo "✅ ERPNext installed successfully"
      
      echo "🔧 Installing custom XML Importer app..."
      if [ ! -d "apps/erpnext_xml_importer" ]; then
        echo "📥 Downloading XML Importer app from GitHub..."
        bench get-app https://github.com/UhrinDavid/erpnext_xml_importer.git
      fi
      
      bench --site "$FRAPPE_SITE_NAME_HEADER" install-app erpnext_xml_importer
      echo "✅ XML Importer app installed successfully"
      
      echo "🔄 Running site migration..."
      bench --site "$FRAPPE_SITE_NAME_HEADER" migrate
      echo "✅ Site migration completed"
      
      echo "🎉 Site installation completed successfully!"
    else
      echo "♻️  Site $FRAPPE_SITE_NAME_HEADER already exists"
      echo "🔄 Running migration to ensure site is up to date..."
      bench --site "$FRAPPE_SITE_NAME_HEADER" migrate
      echo "✅ Migration completed"
    fi
  '

echo "🎯 Frappe site installation script completed!"