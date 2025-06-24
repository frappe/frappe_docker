#!/bin/sh

# Usage: ./stack.sh up -d   or   ./stack.sh down --remove-orphans

set -e

ACTION="$1"
shift
ARGS="$@"

if [ "$ACTION" != "up" ] && [ "$ACTION" != "down" ]; then
    echo "Usage: $0 up|down [extra docker compose flags]"
    exit 1
fi

cd /home/frappe/frappe_docker || {
    echo "Cannot find directory /home/frappe/frappe_docker"
    exit 1
}

# Uncomment this block when using traefik container by frappe
# echo "==> Traefik $ACTION $ARGS"
# docker compose \
#   --project-name traefik \
#   --env-file /home/frappe/gitops/traefik.env \
#   -f overrides/compose.traefik.yaml \
#   -f overrides/compose.traefik-ssl.yaml \
#   "$ACTION" $ARGS

# Uncomment this block when using mariadb container by frappe
echo "==> MariaDB $ACTION $ARGS"
docker compose \
  --project-name mariadb \
  --env-file /home/frappe/gitops/mariadb.env \
  -f overrides/compose.mariadb-shared.yaml \
  "$ACTION" $ARGS

echo "==> ERPNext $ACTION $ARGS"
docker compose \
  --project-name erpnext-one \
  -f /home/frappe/gitops/erpnext-one.yaml \
  "$ACTION" $ARGS
