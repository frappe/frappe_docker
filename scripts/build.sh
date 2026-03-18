#!/usr/bin/env bash
# ============================================================
#  Сборка образа frappe-custom
#  Использование: ./scripts/build.sh [tag]
#  По умолчанию: tag = v16
# ============================================================
set -euo pipefail

TAG="${1:-v16}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-16}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "╔══════════════════════════════════════════════╗"
echo "  Сборка frappe-custom:${TAG}"
echo "  Ветка Frappe : ${FRAPPE_BRANCH}"
echo "  Репозиторий  : ${REPO_DIR}"
echo "╚══════════════════════════════════════════════╝"

cd "$REPO_DIR"

# Проверяем apps.json
if [ ! -f apps.json ]; then
  echo "✗ Файл apps.json не найден"
  exit 1
fi

echo "→ Приложения из apps.json:"
python3 -c "import json; [print('   -', a['url'].split('/')[-1], '@', a['branch']) for a in json.load(open('apps.json'))]"

# Кодируем apps.json в base64
APPS_JSON_B64=$(base64 -w 0 apps.json)

echo ""
echo "→ Запуск docker build..."
docker build \
  --build-arg APPS_JSON_BASE64="$APPS_JSON_B64" \
  --build-arg FRAPPE_BRANCH="$FRAPPE_BRANCH" \
  -t "frappe-custom:${TAG}" \
  -f images/layered/Containerfile \
  .

echo ""
echo "✓ Образ frappe-custom:${TAG} собран"
echo ""
echo "Следующий шаг:"
echo "  make update   # пересоздать контейнеры, мигрировать БД, пересобрать assets"
echo "  make up       # просто запустить (если контейнеры не существуют)"
