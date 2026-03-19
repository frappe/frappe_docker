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
  -f overrides/compose.local-origin.yaml \
  -f overrides/compose.backup-cron.yaml

APPS_JSON_B64 := $(shell base64 -w 0 apps.json)

# Приложения с pre-built esbuild-бандлами (public/dist/).
# Vue SPA (crm, builder, helpdesk, insights, gameplan, drive) используют public/frontend/ —
# они синхронизируются отдельной веткой внутри sync-assets.
DIST_APPS := frappe erpnext hrms lms print_designer webshop education lending newsletter

# Имя именованного тома Docker Compose (проект = имя директории)
COMPOSE_PROJECT := $(notdir $(CURDIR))
ASSETS_VOL      := $(COMPOSE_PROJECT)_assets

.PHONY: help build up down restart update migrate assets sync-assets backup logs ps shell

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
	@echo "    make assets         — пересобрать JS/CSS бандлы и синхронизировать"
	@echo "    make sync-assets    — только скопировать dist в assets volume (без rebuild)"
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
	@echo "→ Пересборка assets (bench build --production)..."
	docker compose $(COMPOSE_OVERRIDES) exec backend bench build --production
	$(MAKE) sync-assets
	@echo "✓ Assets пересобраны"

# ── Синхронизация dist → frappe-project_assets volume ────────
# bench build пишет файлы в overlay-слой backend-контейнера, а nginx
# читает из именованного тома. Эта цель копирует dist-файлы туда.
sync-assets:
	@echo "→ Синхронизация dist-файлов в $(ASSETS_VOL)..."
	@TMPDIR=$$(mktemp -d) && \
	trap "rm -rf $$TMPDIR" EXIT && \
	BACKEND=$$(docker compose $(COMPOSE_OVERRIDES) ps -q backend) && \
	docker cp $$BACKEND:/home/frappe/frappe-bench/sites/assets/assets.json \
	  $$TMPDIR/assets.json && \
	for app in $(DIST_APPS); do \
	  SRC=/home/frappe/frappe-bench/apps/$$app/$$app/public/dist; \
	  if docker cp $$BACKEND:$$SRC $$TMPDIR/$$app-dist 2>/dev/null; then \
	    echo "  ✓ $$app"; \
	  else \
	    echo "  - $$app (нет dist, пропущено)"; \
	  fi; \
	done && \
	docker run --rm \
	  -v $$TMPDIR:/src:ro \
	  -v $(ASSETS_VOL):/assets \
	  alpine sh -c ' \
	    cp -f /src/assets.json /assets/assets.json; \
	    for d in /src/*-dist; do \
	      [ -d "$$d" ] || continue; \
	      app=$$(basename "$$d" -dist); \
	      rm -f /assets/$$app; \
	      mkdir -p /assets/$$app/dist; \
	      cp -rf "$$d/." /assets/$$app/dist/; \
	    done \
	  '
	@echo "→ Сброс кэша assets_json в Redis..."
	@docker compose $(COMPOSE_OVERRIDES) exec backend \
	  bench --site $(SITE) clear-cache
	@docker compose $(COMPOSE_OVERRIDES) exec backend bash -c \
	  ". /home/frappe/frappe-bench/env/bin/activate && \
	   python -c \"import redis; r=redis.Redis(host='redis-cache'); \
	   deleted=r.delete('assets_json'); \
	   print('assets_json удалён из Redis' if deleted else 'assets_json отсутствовал')\""
	@docker compose $(COMPOSE_OVERRIDES) restart frontend
	@echo "✓ Синхронизация завершена"

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
