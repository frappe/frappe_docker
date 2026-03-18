# GitHub Actions Workflows

## Активация workflows

Для публикации workflow-файлов нужен Personal Access Token (PAT) со scope `workflow`.

### Создание токена:
1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **Generate new token (classic)**
3. Выбрать scopes: ✅ `repo` + ✅ `workflow`
4. Скопировать токен

### Обновление remote URL:
```bash
cd /home/mkr/frappe-project
git remote set-url origin https://<NEW_TOKEN>@github.com/abounoone/frappe_docker.git
git push origin main
```

---

## Описание workflows

### `check-app-updates.yml`
- **Когда:** каждый понедельник в 06:00 UTC + ручной запуск
- **Что делает:** проверяет новые теги на GitHub для каждого приложения из `apps.json`
- **Результат:** создаёт PR с обновлёнными версиями

### `build-image.yml`
- **Когда:** push в `main` с изменениями `apps.json` или `Containerfile`
- **Что делает:** собирает `frappe-custom:v16` и пушит в GHCR
- **Образ:** `ghcr.io/abounoone/frappe-custom:v16`
- **Теги:** `v16`, `v16-YYYYMMDD`, `latest`

### Использование образа из GHCR в .env:
```env
CUSTOM_IMAGE=ghcr.io/abounoone/frappe-custom
CUSTOM_TAG=v16
PULL_POLICY=always
```
