#!/usr/bin/env bash
# One-click restaurant POS deploy: ERPNext v16 + restaurant_management on frappe_docker.
# Run from the frappe_docker repo root. Re-runnable: every step skips what already exists.
#
#   SITE=frontend ADMIN_PASSWORD=change-me ./restaurant/deploy.sh
#
# Optional env:
#   SITE              site name, must match FRAPPE_SITE_NAME_HEADER in .env (default: frontend)
#   ADMIN_PASSWORD    Administrator password for a newly created site (default: admin)
#   DB_ROOT_PASSWORD  MariaDB root password (default: 123 = frappe_docker's compose default)
#   ERPNEXT_VERSION   pinned erpnext tag baked into the image (default: v16.6.0)
#   SEED_DEMO=1       load demo restaurant: menu, tables, customers, ingredients, BOMs
#   SIMULATE=1        additionally run a 10-order service + back-flush (implies SEED_DEMO)

set -euo pipefail
cd "$(dirname "$0")/.."

SITE="${SITE:-frontend}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-123}"
ERPNEXT_VERSION="${ERPNEXT_VERSION:-v16.6.0}"
IMAGE="custom-erpnext:${ERPNEXT_VERSION}"

log() { echo "==> $*"; }

[ -f .env ] || { cp example.env .env; echo "FRAPPE_SITE_NAME_HEADER=${SITE}" >> .env; }
grep -q '^CUSTOM_IMAGE=' .env || cat >> .env <<EOF
CUSTOM_IMAGE=custom-erpnext
CUSTOM_TAG=${ERPNEXT_VERSION}
PULL_POLICY=never
EOF

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  log "building ${IMAGE} (frappe + erpnext ${ERPNEXT_VERSION} + restaurant_management)"
  DOCKER_BUILDKIT=1 docker build \
    --secret id=apps_json,src=apps-restaurant.json \
    --build-arg FRAPPE_BRANCH=version-16 \
    -t "$IMAGE" -f images/layered/Containerfile .
  log "applying v16 compatibility patches to the restaurant app"
  docker build -t "$IMAGE" -f patch-restaurant.dockerfile .
fi

log "starting the stack"
docker compose up -d

log "waiting for backend"
for _ in $(seq 1 30); do
  docker compose exec -T backend true 2>/dev/null && break
  sleep 2
done

if ! docker compose exec -T backend test -d "sites/${SITE}"; then
  log "creating site ${SITE} (this installs erpnext + restaurant_management, ~5 min)"
  docker compose exec -T backend bench new-site "$SITE" \
    --mariadb-user-host-login-scope='%' \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --install-app erpnext --install-app restaurant_management
else
  log "site ${SITE} exists — ensuring apps are installed"
  docker compose exec -T backend bench --site "$SITE" install-app restaurant_management 2>/dev/null || true
  docker compose exec -T backend bench --site "$SITE" migrate
fi

log "site configuration the restaurant app needs on v16"
[ -n "${SITE_URL:-}" ] && docker compose exec -T backend bench --site "$SITE" set-config host_name "$SITE_URL"
docker compose exec -T backend bench --site "$SITE" enable-scheduler
docker compose exec -T backend bench --site "$SITE" console <<'PY'
frappe.db.set_value("POS Settings", None, "invoice_type", "POS Invoice")
frappe.db.set_value("UOM", "Nos", "must_be_whole_number", 0)
frappe.db.commit()
print("POS Settings -> POS Invoice mode; UOM Nos allows fractions (wine by the glass)")
PY

if [ "${SIMULATE:-0}" = "1" ]; then SEED_DEMO=1; fi
if [ "${SEED_DEMO:-0}" = "1" ]; then
  log "seeding demo restaurant"
  docker cp restaurant/demo_seed.py "$(docker compose ps -q backend)":/home/frappe/frappe-bench/apps/restaurant_management/restaurant_management/demo_seed.py
  SEED_CALLS="seed(); seed_inventory()"
  [ "${SIMULATE:-0}" = "1" ] && SEED_CALLS="$SEED_CALLS; simulate(); backflush()"
  docker compose exec -T backend bench --site "$SITE" console <<PY
exec(open("/home/frappe/frappe-bench/apps/restaurant_management/restaurant_management/demo_seed.py").read(), globals())
${SEED_CALLS}
PY
fi

log "done — login: Administrator / ${ADMIN_PASSWORD}"
log "put a reverse proxy in front of 127.0.0.1:8080 (see restaurant/README.md)"
