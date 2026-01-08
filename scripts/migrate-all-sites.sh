#!/bin/bash
# Script to run migrations on all Frappe sites

set -e

echo "🔄 Starting migration for all sites..."

# Get list of all sites
SITES=$(docker compose exec -T backend ls -1 /home/frappe/frappe-bench/sites | grep -v '^apps.txt$' | grep -v '^apps.json$' | grep -v '^common_site_config.json$' | grep -v '^assets$' | grep -v '^\..*$')

if [ -z "$SITES" ]; then
    echo "❌ No sites found!"
else
    echo "📋 Found sites:"
    echo "$SITES"
    echo ""

    # Run migrate for each site
    for site in $SITES; do
        echo "🔧 Migrating site: $site"
        
        # Run bench migrate
        docker compose exec -T backend bench --site "$site" migrate || {
            echo "❌ Migration failed for site: $site"
            exit 1
        }
        
        # Clear cache
        docker compose exec -T backend bench --site "$site" clear-cache || {
            echo "⚠️  Warning: Failed to clear cache for site: $site"
        }
        
        echo "✅ Migration completed for site: $site"
        echo ""
    done

    echo "🎉 All migrations completed successfully!"

    # Optional: Run bench doctor to check system health
    echo "🏥 Running system health check..."
    docker compose exec -T backend bench doctor || {
        echo "⚠️  Warning: Some health checks failed"
    }

    echo "✨ Migration process finished!"
fi
