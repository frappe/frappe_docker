# ============================================================
#  Frappe ERP — управление стеком
#  Использование: make <target>
# ============================================================

SHELL := /bin/bash
SITE  ?= erp.local
TAG   ?= v16

COMPOSE_OVERRIDES := \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.assets-volume.yaml \
  -f overrides/compose.noproxy.yaml \
  -f overrides/compose.backup-cron.yaml

APPS_JSON_B64 := $(shell base64 -w 0 apps.json)

.PHONY: help build up down restart update migrate assets backup logs ps shell

# ── Справка ─────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Frappe ERP — доступные команды:"
	@echo ""
	@echo "  Образ:"
	@echo "    make build          — собрать frappe-custom:$(TAG) из apps.json"
	@echo "    make build TAG=v17  — собрать с другим тегом"
	@echo ""
	@echo "  Стек:"
	@echo "    make up             — запустить все контейнеры"
	@echo "    make down           — остановить и удалить контейнеры"
	@echo "    make restart        — перезапустить backend/frontend"
	@echo "    make ps             — статус контейнеров"
	@echo ""
	@echo "  Обновление:"
	@echo "    make update         — rebuild образа + up + migrate + assets"
	@echo "    make migrate        — bench migrate на сайте $(SITE)"
	@echo "    make assets         — пересобрать JS/CSS бандлы"
	@echo ""
	@echo "  Обслуживание:"
	@echo "    make backup         — создать резервную копию сайта"
	@echo "    make logs           — логи backend (live)"
	@echo "    make shell          — bash в backend контейнере"
	@echo ""

# ── Сборка образа ────────────────────────────────────────────
build:
	@echo "→ Сборка frappe-custom:$(TAG) из apps.json..."
	docker build \
	  --build-arg APPS_JSON_BASE64=$(APPS_JSON_B64) \
	  --build-arg FRAPPE_BRANCH=version-16 \
	  -t frappe-custom:$(TAG) \
	  -f images/layered/Containerfile \
	  .
	@echo "✓ Образ frappe-custom:$(TAG) готов"

# ── Запуск стека ─────────────────────────────────────────────
up:
	docker compose $(COMPOSE_OVERRIDES) up -d
	@echo "✓ Стек запущен. Сайт: http://localhost:$${HTTP_PUBLISH_PORT:-8090}"

down:
	docker compose $(COMPOSE_OVERRIDES) down

restart:
	docker compose $(COMPOSE_OVERRIDES) restart backend frontend websocket

ps:
	docker compose $(COMPOSE_OVERRIDES) ps

# ── Обновление (полный цикл) ─────────────────────────────────
update: build
	@echo "→ Пересоздаём контейнеры с новым образом..."
	docker compose $(COMPOSE_OVERRIDES) up -d --no-deps backend websocket queue-short queue-long scheduler
	@echo "→ Ждём готовности backend..."
	sleep 10
	$(MAKE) migrate
	$(MAKE) assets
	docker compose $(COMPOSE_OVERRIDES) restart frontend
	@echo "✓ Обновление завершено"

# ── Миграции БД ──────────────────────────────────────────────
migrate:
	@echo "→ bench migrate --site $(SITE)..."
	docker compose $(COMPOSE_OVERRIDES) exec backend \
	  bench --site $(SITE) migrate
	@echo "✓ Миграция завершена"

# ── Пересборка JS/CSS ────────────────────────────────────────
assets:
	@echo "→ Пересборка assets..."
	docker compose $(COMPOSE_OVERRIDES) exec backend \
	  bash -c "cd apps/frappe && node esbuild --production"
	docker compose $(COMPOSE_OVERRIDES) exec backend \
	  bench build
	docker compose $(COMPOSE_OVERRIDES) restart frontend
	@echo "✓ Assets пересобраны"

# ── Резервная копия ──────────────────────────────────────────
backup:
	@echo "→ Создание резервной копии сайта $(SITE)..."
	docker compose $(COMPOSE_OVERRIDES) exec backend \
	  bench --site $(SITE) backup --with-files
	@echo "✓ Бэкап создан (см. sites/$(SITE)/private/backups/)"

# ── Логи и отладка ───────────────────────────────────────────
logs:
	docker compose $(COMPOSE_OVERRIDES) logs -f backend

shell:
	docker compose $(COMPOSE_OVERRIDES) exec backend bash
