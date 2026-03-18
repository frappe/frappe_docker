# Frappe ERP — развёртывание и обновление

## Стратегия обновления приложений

| Приложение | Ветка | Почему |
|------------|-------|--------|
| `frappe`   | `version-16` | стабильная ветка мажорной версии |
| `erpnext`  | `version-16` | стабильная ветка мажорной версии |
| `hrms`     | `version-16` | стабильная ветка мажорной версии |
| `crm`      | `main`        | нет ветки version-16, main = стабильный |
| `helpdesk` | `main`        | нет ветки version-16 |
| `insights` | `main`        | v2.x line, v3.x — отдельная мажорная версия |
| `lms`      | `main`        | нет ветки version-16 |
| `payments` | `develop`     | нет релизов, активная разработка |
| `telephony`| `develop`     | нет релизов, активная разработка |

**Автоматические обновления** — GitHub Actions каждый понедельник проверяет новые теги
и создаёт PR при наличии обновлений (`.github/workflows/check-app-updates.yml`).

**Автосборка образа** — при merge в `main` с изменениями `apps.json` автоматически
стартует сборка и публикация образа в GHCR (`.github/workflows/build-image.yml`).

---

## Структура репозитория

```
frappe_docker/
├── apps.json                          ← список приложений для образа
├── compose.yaml                       ← основной docker-compose
├── .env                               ← конфигурация (не в git, создать из .env.example)
├── .env.example                       ← шаблон конфигурации
├── Makefile                           ← все команды управления
├── DEPLOY.md                          ← эта документация
│
├── .github/
│   └── workflows/
│       ├── check-app-updates.yml      ← еженедельная проверка обновлений → PR
│       └── build-image.yml            ← сборка образа при изменении apps.json
│
├── images/
│   ├── layered/Containerfile          ← сборка на базе frappe/build (быстро)
│   └── custom/Containerfile           ← сборка с нуля (полный контроль)
│
├── overrides/
│   ├── compose.assets-volume.yaml     ← общий том assets (обязателен)
│   ├── compose.mariadb.yaml           ← встроенная MariaDB
│   └── ...                            ← другие оверрайды (proxy, ssl, etc.)
│
└── scripts/
    ├── build.sh                       ← сборка образа
    ├── update-apps.sh                 ← проверка обновлений приложений
    └── new-site.sh                    ← создание нового сайта
```

---

## Первый запуск

```bash
# 1. Создать конфигурацию
cp .env.example .env
# Отредактировать .env: задать DB_PASSWORD, FRAPPE_SITE_NAME_HEADER и т.д.

# 2. Собрать образ с приложениями из apps.json
make build

# 3. Запустить стек
make up

# 4. Создать сайт (если ещё не создан)
./scripts/new-site.sh erp.local YourAdminPassword
```

---

## Обновление приложений

### Шаг 1 — проверить доступные обновления

```bash
./scripts/update-apps.sh
```

Скрипт покажет последние коммиты каждого приложения из `apps.json`.

### Шаг 2 — обновить apps.json при необходимости

Если нужна конкретная ветка или тег:

```json
// apps.json
[
  { "url": "https://github.com/frappe/erpnext",  "branch": "version-16" },
  { "url": "https://github.com/frappe/crm",       "branch": "main" }
]
```

### Шаг 3 — полный цикл обновления

```bash
make update
```

Это выполнит:
1. `make build`   — пересборка образа frappe-custom:v16
2. `docker compose up -d --no-deps` — замена контейнеров без даунтайма DB/Redis
3. `bench migrate` — применение миграций БД
4. `bench build`  — пересборка JS/CSS assets
5. Перезапуск nginx

---

## Частичные операции

```bash
make migrate          # только миграции (после ручного обновления)
make assets           # только пересборка JS/CSS
make restart          # перезапуск backend/frontend
make backup           # резервная копия сайта
make logs             # логи backend в реальном времени
make shell            # bash в контейнере backend
make ps               # статус всех контейнеров
```

---

## Смена версии (например, v16 → v17)

```bash
# 1. Обновить ветки в apps.json
# 2. Пересобрать с новым тегом
make build TAG=v17

# 3. Обновить .env
# CUSTOM_TAG=v17

# 4. Пересоздать стек
make up
make migrate
```

---

## Добавление нового приложения

1. Добавить в `apps.json`:
```json
{ "url": "https://github.com/frappe/hrms", "branch": "version-16" }
```

2. Пересобрать образ и обновить:
```bash
make update
```

3. Установить на сайт:
```bash
make shell
bench --site erp.local install-app hrms
```

---

## Переменные окружения (.env)

| Переменная              | Описание                                 | Пример              |
|-------------------------|------------------------------------------|---------------------|
| `CUSTOM_IMAGE`          | Имя Docker-образа                        | `frappe-custom`     |
| `CUSTOM_TAG`            | Тег образа                               | `v16`               |
| `PULL_POLICY`           | `missing` — использовать локальный образ | `missing`           |
| `DB_PASSWORD`           | Пароль MariaDB                           | (сильный пароль)    |
| `FRAPPE_SITE_NAME_HEADER` | Имя сайта                             | `erp.local`         |
| `HTTP_PUBLISH_PORT`     | Внешний порт HTTP                        | `8090`              |
| `BACKUP_CRONSTRING`     | Расписание бэкапов                       | `@every 6h`         |
