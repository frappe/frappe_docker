#!/bin/bash
# Production-ready site creation script

SITE_NAME=$1
ADMIN_PASSWORD=$2
DB_ROOT_PASSWORD=$3

if [ -z "$SITE_NAME" ] || [ -z "$ADMIN_PASSWORD" ] || [ -z "$DB_ROOT_PASSWORD" ]; then
    echo "Usage: $0 <site-name> <admin-password> <db-root-password>"
    exit 1
fi

echo "Creating site: $SITE_NAME"

# Create the site with proper database configuration
docker compose exec backend bench new-site $SITE_NAME \
    --admin-password $ADMIN_PASSWORD \
    --db-root-password $DB_ROOT_PASSWORD \
    --db-host mariadb \
    --mariadb-root-username root \
    --no-mariadb-socket

# Install required apps
echo "Installing LMS app..."
docker compose exec backend bench --site $SITE_NAME install-app lms

echo "Installing AI Tutor Chat app..."
docker compose exec backend bench --site $SITE_NAME install-app ai_tutor_chat

# Set site configuration
echo "Configuring site..."
docker compose exec backend bench --site $SITE_NAME set-config db_host mariadb
docker compose exec backend bench --site $SITE_NAME set-config ai_tutor_api_url "http://langchain-service:8000"

# Set as default site (optional)
docker compose exec backend bench use $SITE_NAME

echo "Site $SITE_NAME created successfully!"
echo "Access it at: http://$SITE_NAME (make sure to add it to your hosts file or DNS)"
