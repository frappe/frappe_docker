#!/usr/bin/env bash
#
# Локальная сборка образа Habibi.
#
# Штатный путь сборки — CI (.github/workflows/habibi-image.yml), он пушит
# образ в ghcr.io с версионным тегом. Этот скрипт нужен, когда собрать
# надо руками: на сервере без доступа к registry или при отладке.
#
# Собирает layered-образ: frappe (по FRAPPE_BRANCH) + все приложения
# из habibi/apps.json. Ассеты собираются внутри образа при bench init.
#
# Требуется Docker Engine v23+ — apps.json передаётся BuildKit-секретом,
# чтобы токены приватных репозиториев не попали в слои образа.
#
# Запуск из корня репозитория:
#   habibi/build.sh
#
# После сборки в .env должно быть:
#   CUSTOM_IMAGE=habibi
#   CUSTOM_TAG=16
#   PULL_POLICY=never
# иначе compose попытается тянуть образ из registry вместо локального.

set -euo pipefail

cd "$(dirname "$0")/.."

FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-16}"
FRAPPE_PATH="${FRAPPE_PATH:-https://github.com/frappe/frappe}"
IMAGE="${IMAGE:-habibi}"
TAG="${TAG:-16}"
APPS_JSON="${APPS_JSON:-habibi/apps.json}"

if [ ! -s "$APPS_JSON" ]; then
  echo "ошибка: $APPS_JSON отсутствует или пуст" >&2
  exit 1
fi

if ! jq empty "$APPS_JSON" 2>/dev/null; then
  echo "ошибка: $APPS_JSON не является валидным JSON" >&2
  exit 1
fi

# CACHE_BUST инвалидирует слой bench init. Без него Docker переиспользует
# кеш и НЕ подтянет новые коммиты приложений: сборка пройдёт «успешно»
# со старым кодом.
#
# Считаем из фактических SHA репозиториев — так же, как в CI. Тот же набор
# коммитов даёт тот же ключ, лишней пересборки не будет.
if [ -z "${CACHE_BUST:-}" ]; then
  bust=""
  while read -r url branch; do
    sha=$(git ls-remote "$url" "refs/heads/$branch" | cut -f1)
    if [ -z "$sha" ]; then
      echo "ошибка: не удалось разрешить $url @ $branch" >&2
      exit 1
    fi
    echo "  $url @ $branch -> $sha"
    bust="${bust}${sha}"
  done < <(jq -r '.[] | "\(.url) \(.branch)"' "$APPS_JSON")
  # sha256sum есть в coreutils (Linux), shasum — в macOS
  if command -v sha256sum >/dev/null 2>&1; then
    CACHE_BUST=$(printf '%s' "$bust" | sha256sum | cut -c1-16)
  else
    CACHE_BUST=$(printf '%s' "$bust" | shasum -a 256 | cut -c1-16)
  fi
fi

echo
echo "frappe:     ${FRAPPE_PATH} @ ${FRAPPE_BRANCH}"
echo "образ:      ${IMAGE}:${TAG}"
echo "cache bust: ${CACHE_BUST}"
echo

docker build \
  --build-arg="FRAPPE_PATH=${FRAPPE_PATH}" \
  --build-arg="FRAPPE_BRANCH=${FRAPPE_BRANCH}" \
  --build-arg="CACHE_BUST=${CACHE_BUST}" \
  --secret="id=apps_json,src=${APPS_JSON}" \
  --tag="${IMAGE}:${TAG}" \
  --tag="${IMAGE}:${TAG}-${CACHE_BUST}" \
  --file=images/layered/Containerfile \
  .

echo
echo "готово:"
echo "  ${IMAGE}:${TAG}"
echo "  ${IMAGE}:${TAG}-${CACHE_BUST}"
echo
echo "проверить состав:  docker run --rm --entrypoint bash ${IMAGE}:${TAG} -lc 'ls -1 apps'"
