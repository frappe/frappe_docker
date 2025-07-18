#!/bin/bash
# Script to create a new Frappe site with Academy apps

set -e

# Check if site name is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <site-name>"
    echo "Example: $0 academy.example.com"
    exit 1
fi

SITE_NAME=$1

echo "🌐 Creating new site: $SITE_NAME"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -E '^[A-Z_][A-Z0-9_]*=' | sed 's/#.*$//' | xargs)
else
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Create the site
echo "📦 Creating Frappe site..."
docker compose exec -T backend bench new-site \
    --no-mariadb-socket \
    --admin-password="$ADMIN_PASSWORD" \
    --db-root-password="$MARIADB_ROOT_PASSWORD" \
    "$SITE_NAME"

# Install LMS
echo "📦 Installing Academy LMS..."
docker compose exec -T backend bench --site "$SITE_NAME" install-app lms

# Install AI Tutor Chat
echo "📦 Installing AI Tutor Chat..."
docker compose exec -T backend bench --site "$SITE_NAME" install-app ai_tutor_chat

# Set as default site (optional)
SET_DEFAULT_SITE_FLAG="${2:-n}"
echo
if [[ $SET_DEFAULT_SITE_FLAG =~ ^[Yy]$ ]]; then
    docker compose exec -T backend bench use "$SITE_NAME"
    echo "✅ Set as default site"
fi

# Clear cache
echo "🧹 Clearing cache..."
docker compose exec -T backend bench --site "$SITE_NAME" clear-cache

# Run migrations
echo "🔄 Running migrations..."
docker compose exec -T backend bench --site "$SITE_NAME" migrate

echo "✅ Site created successfully!"
echo ""
echo "📋 Site details:"
echo "URL: http://$SITE_NAME"
echo "Username: Administrator"
echo "Password: $ADMIN_PASSWORD"
echo ""
echo "🔐 Remember to:"
echo "1. Update your DNS to point to the server IP"
echo "2. Configure SSL certificate for production"
echo "3. Update nginx configuration if needed"
