# Stack management with Makefile

The `Makefile` in the project root provides a single entry point for all common operations. It always uses the full set of override files required to run ERPNext locally.

## Included overrides

Every `make` command runs `docker compose` with:

```
compose.yaml
overrides/compose.mariadb.yaml
overrides/compose.redis.yaml
overrides/compose.assets-volume.yaml
overrides/compose.noproxy.yaml
overrides/compose.backup-cron.yaml
```

## Commands

| Command | What it does |
|---|---|
| `make help` | Print all available commands with descriptions |
| `make up` | Start the full stack in detached mode |
| `make down` | Stop and remove all containers |
| `make restart` | Restart `backend`, `frontend`, `websocket` |
| `make ps` | Show container status |
| `make logs` | Stream `backend` logs live |
| `make shell` | Open `bash` in the backend container |
| `make backup` | Create a manual backup of the site |
| `make migrate` | Run `bench migrate` on the site (after app updates) |
| `make assets` | Rebuild JS/CSS bundles and restart frontend |
| `make build` | Build the `frappe-custom:v16` image from `apps.json` |
| `make update` | Full update cycle: build → recreate containers → migrate → assets |

## Variables

The Makefile exposes two overridable variables:

```bash
SITE ?= erp.local   # site name used in bench commands
TAG  ?= v16         # image tag used in build
```

Override on the command line:

```bash
make migrate SITE=mycompany.local
make build TAG=v17
```

## First-run checklist

```bash
# 1. Start the stack (MariaDB, Redis and all Frappe services)
make up

# 2. Wait ~10 seconds for MariaDB to become healthy, then create the site
make shell
bench new-site \
  --mariadb-user-host-login-scope=% \
  --db-root-password <DB_PASSWORD from .env> \
  --admin-password <your-admin-password> \
  erp.local

# 3. Install apps on the site
bench --site erp.local install-app erpnext
bench --site erp.local install-app crm
# ... other apps as needed

exit   # leave the shell

# 4. Open http://localhost:8090 in your browser
```

> `DB_PASSWORD` is set in `.env`. The default value is a random string generated during project setup.

## Updating the stack

When `apps.json` changes (new app version or added app):

```bash
make update
# equivalent to: make build && docker compose up -d (backend services) && make migrate && make assets
```

For a config-only change that doesn't require a new image:

```bash
make down && make up
```
