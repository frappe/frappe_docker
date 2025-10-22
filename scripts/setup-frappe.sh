#!/bin/bash

# Frappe/ERPNext Initial Setup Script for Zerops
# This script should be run after the services are deployed and running

set -e

echo "🚀 Starting Frappe/ERPNext setup on Zerops..."

# Check if required environment variables are set
if [ -z "$SITE_NAME" ]; then
    echo "❌ Error: SITE_NAME environment variable is required"
    echo "   Set it to your domain name (e.g., mycompany.example.com)"
    exit 1
fi

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Error: DB_PASSWORD environment variable is required"
    exit 1
fi

if [ -z "$ADMIN_PASSWORD" ]; then
    echo "❌ Error: ADMIN_PASSWORD environment variable is required"
    echo "   This will be the password for the ERPNext admin user"
    exit 1
fi

echo "📋 Configuration:"
echo "   Site Name: $SITE_NAME"
echo "   Database Host: ${DB_HOST:-db}"
echo "   Admin Email: ${ADMIN_EMAIL:-administrator@$SITE_NAME}"

# Navigate to frappe bench directory
cd /home/frappe/frappe-bench

echo "🏗️  Creating new site: $SITE_NAME"
bench new-site "$SITE_NAME" \
    --db-root-password "$DB_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --set-default

echo "📦 Installing ERPNext application..."
bench --site "$SITE_NAME" install-app erpnext

echo "👤 Setting up admin user..."
if [ -n "$ADMIN_EMAIL" ]; then
    bench --site "$SITE_NAME" set-admin-password "$ADMIN_PASSWORD"
fi

echo "🔧 Final configuration..."
# Set site as default
bench use "$SITE_NAME"

# Clear cache
bench --site "$SITE_NAME" clear-cache

# Migrate database (in case there are any pending migrations)
bench --site "$SITE_NAME" migrate

echo "✅ Setup completed successfully!"
echo ""
echo "🌐 Your ERPNext site is ready at: $SITE_NAME"
echo "👤 Admin login: administrator"
echo "🔑 Admin password: [as set in ADMIN_PASSWORD]"
echo ""
echo "📚 Next steps:"
echo "   1. Configure your domain to point to this Zerops service"
echo "   2. Access your site and complete the setup wizard"
echo "   3. Configure SSL certificates if needed"
echo ""
echo "🔧 Useful commands:"
echo "   - bench restart: Restart all processes"
echo "   - bench --site $SITE_NAME console: Open Python console"  
echo "   - bench --site $SITE_NAME migrate: Run database migrations"
echo "   - bench update: Update apps and migrate"