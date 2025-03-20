#!/bin/bash

# Read email configuration
source email.env

# Path to your docker-compose files
COMPOSE_FILES="-f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.https.yaml"

# Configure email settings
docker compose $COMPOSE_FILES exec backend bench --site erpnext.appsatile.com set-config -g mail_server "$MAIL_HOST"
docker compose $COMPOSE_FILES exec backend bench --site erpnext.appsatile.com set-config -g mail_port "$MAIL_PORT"
docker compose $COMPOSE_FILES exec backend bench --site erpnext.appsatile.com set-config -g use_tls "$MAIL_USE_TLS"
docker compose $COMPOSE_FILES exec backend bench --site erpnext.appsatile.com set-config -g mail_login "$MAIL_LOGIN"
docker compose $COMPOSE_FILES exec backend bench --site erpnext.appsatile.com set-config -g mail_password "$MAIL_PASSWORD"
docker compose $COMPOSE_FILES exec backend bench --site erpnext.appsatile.com set-config -g auto_email_id "$MAIL_EMAIL_ID"
docker compose $COMPOSE_FILES exec backend bench --site erpnext.appsatile.com set-config -g email_sender_name "$MAIL_SENDER_NAME"

# Make these configurations take effect
docker compose $COMPOSE_FILES restart backend

echo "Email configuration completed" 