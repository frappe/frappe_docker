#!/usr/bin/env bash
# ============================================================
#  Обновление версий приложений в apps.json
#  Проверяет последние коммиты каждого приложения
#  Использование: ./scripts/update-apps.sh
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
APPS_FILE="$REPO_DIR/apps.json"

echo "╔══════════════════════════════════════════════╗"
echo "  Проверка обновлений приложений"
echo "╚══════════════════════════════════════════════╝"
echo ""

python3 -c "
import json, urllib.request, sys

apps = json.load(open('$APPS_FILE'))

for app in apps:
    url  = app['url']
    branch = app['branch']
    name = url.rstrip('/').split('/')[-1]

    # GitHub API: последний коммит ветки
    api_url = url.replace('https://github.com/', 'https://api.github.com/repos/') + '/commits/' + branch
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'frappe-update-check'})
        data = json.loads(urllib.request.urlopen(req, timeout=5).read())
        sha  = data['sha'][:8]
        date = data['commit']['committer']['date'][:10]
        msg  = data['commit']['message'].splitlines()[0][:60]
        print(f'  {name:20s} [{branch}]  последний коммит: {sha} ({date})')
        print(f'    {msg}')
    except Exception as e:
        print(f'  {name:20s} [{branch}]  ошибка проверки: {e}')
    print()
"

echo ""
echo "Чтобы обновить образ после изменения apps.json:"
echo "  make build   — только пересобрать образ"
echo "  make update  — полный цикл (build + migrate + assets)"
