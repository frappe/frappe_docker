#!/usr/bin/env bash
# ============================================================
#  Создание нового Frappe-сайта
#  Использование: ./scripts/new-site.sh <site-name> <admin-password>
#  Пример:        ./scripts/new-site.sh mycompany.local Admin123
# ============================================================
set -euo pipefail

SITE="${1:-}"
ADMIN_PASS="${2:-}"

if [ -z "$SITE" ] || [ -z "$ADMIN_PASS" ]; then
  echo "Использование: $0 <site-name> <admin-password>"
  echo "Пример:        $0 mycompany.local Admin123"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cd "$REPO_DIR"

COMPOSE_OVERRIDES="-f compose.yaml -f overrides/compose.assets-volume.yaml"

echo "→ Создание сайта: $SITE"

docker compose $COMPOSE_OVERRIDES exec backend \
  bench new-site "$SITE" \
    --mariadb-root-password "$(grep DB_PASSWORD .env | cut -d= -f2)" \
    --admin-password "$ADMIN_PASS" \
    --install-app erpnext

echo "→ Устанавливаем дополнительные приложения..."
for APP in crm helpdesk payments insights lms; do
  echo "   + $APP"
  docker compose $COMPOSE_OVERRIDES exec backend \
    bench --site "$SITE" install-app "$APP" || echo "   ! $APP пропущен (возможно не нужен)"
done

echo "→ Запуск миграций..."
docker compose $COMPOSE_OVERRIDES exec backend \
  bench --site "$SITE" migrate

echo ""
echo "✓ Сайт $SITE создан"
echo "  URL:      http://localhost:${HTTP_PUBLISH_PORT:-8090}"
echo "  Логин:    Administrator"
echo "  Пароль:   $ADMIN_PASS"
