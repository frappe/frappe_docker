# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

This is a **frappe-bench** — a containerized development workspace that manages multiple Frappe Framework applications. Frappe is a full-stack Python web framework (Flask/Werkzeug-based) with a built-in DocType ORM, Vue.js 3 frontend, Redis-backed queues/cache, and real-time Socket.io communication.

**Installed apps** (under `apps/`):
- `frappe/` — core framework (v15.x)
- `frappe_whatsapp/` — WhatsApp Cloud API integration (direct Meta API)
- `chatwoot_erp/` — Chatwoot customer support integration

## Commands

### Starting Dev Servers
```bash
honcho start          # start all processes (web, socketio, watch, schedule, worker)
bench serve           # web server only (port 8000)
bench watch           # asset watcher only
```

### Building Assets
```bash
# from apps/frappe/
npm run watch         # development watch mode
npm run build         # development build
npm run production    # production build (minified)

# or via bench CLI (from bench root)
bench build [--app <app>] [--production] [--hard-link] [--force]
```

### Running Tests
```bash
# Python unit tests
bench --site site1.localhost run-tests --app <app>
bench --site site1.localhost run-tests --app <app> --module <module.path>
bench --site site1.localhost run-tests --app <app> --doctype "DocType Name"
bench --site site1.localhost run-tests --app <app> --case TestClassName

# Parallel tests (CI)
bench --site site1.localhost run-parallel-tests --app <app> --build-number 1 --total-builds 4

# UI/E2E tests (Cypress)
bench --site site1.localhost run-ui-tests --app <app>
```

### Linting
```bash
# Python (from apps/frappe/ or any app dir)
ruff check .
ruff format .

# JavaScript
cd apps/frappe && npx eslint .
cd apps/frappe && npx prettier --check .

# All pre-commit hooks
pre-commit run --all-files
```

### Database / Site Management
```bash
bench --site site1.localhost migrate          # run pending schema migrations
bench --site site1.localhost console          # Python REPL with frappe context
bench --site site1.localhost mariadb          # MariaDB shell
bench --site site1.localhost install-app <app>
bench new-site <sitename> --db-name <db>
```

## Architecture

### Multi-App Structure
Each directory in `apps/` is an independent Frappe app with its own `pyproject.toml`, `hooks.py`, and package layout. The `sites/apps.txt` and `sites/apps.json` define which apps are active. Apps communicate through Frappe's hooks system rather than direct imports.

### DocType System (Core Concept)
Frappe's data model is built around **DocTypes** — schema definitions stored as JSON in `<app>/<module>/<doctype>/` directories. Each DocType has:
- A JSON schema file (defines fields, permissions, child tables)
- An optional Python controller class (inherits `frappe.model.document.Document`)
- Optional client-side JS controller

ORM usage: `frappe.get_doc("DocType Name", name)`, `frappe.new_doc("DocType Name")`, `frappe.db.get_value(...)`.

### Hooks System
`hooks.py` in each app is the primary extensibility point. Key hooks:
- `doc_events` — fire Python functions on document create/update/delete
- `scheduler_events` — cron-like background job scheduling
- `override_doctype_class` — replace core document classes
- `app_include_js/css`, `web_include_js/css` — inject assets
- `website_route_rules` — custom URL routing

### Asset Pipeline
JavaScript and Vue.js components are compiled with **esbuild** (configured in `apps/frappe/esbuild/`). CSS uses PostCSS + Sass. Output lands in `sites/assets/`. In development, `bench watch` / `npm run watch` recompiles on change.

### Background Jobs & Real-time
- **RQ workers** (`apps/frappe/frappe/utils/background_jobs.py`) handle async jobs via Redis queues.
- **Socket.io** server (Node.js, `apps/frappe/socketio.js`) handles real-time desk updates.
- **Scheduler** runs `scheduler_events` hooks on cron intervals.

### Multi-Tenancy
A single bench can serve multiple sites. Each site has its own database and configuration in `sites/<sitename>/`. The `sites/common_site_config.json` holds Redis connection strings and shared settings.

## Code Style

Python (enforced by ruff in `apps/frappe/`):
- Python 3.10+, tabs for indentation, double quotes, 110-char line length
- Rules: F, E, W, I, UP, B, RUF — E501 and F401 are ignored

JavaScript/Vue: ESLint + Prettier (config in `apps/frappe/.eslintrc` / `prettier.config.js`).

## Key File Locations

| What | Where |
|------|-------|
| Site config | `sites/site1.localhost/site_config.json` |
| Shared Redis/DB config | `sites/common_site_config.json` |
| Process definitions | `Procfile` |
| Frappe Python entry point | `apps/frappe/frappe/app.py` |
| CLI commands | `apps/frappe/frappe/commands/` |
| Core DocType controllers | `apps/frappe/frappe/core/` |
| WhatsApp webhook utils | `apps/frappe_whatsapp/frappe_whatsapp/utils/` |
| Chatwoot hooks | `apps/chatwoot_erp/chatwoot_erp/hooks.py` |
