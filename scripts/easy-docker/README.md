# Easy-Frappe-Docker

Easy installation script for Frappe Docker for development and production

## Run

```bash
bash easy-docker.sh
```

## Dependencies

- `gum` is used for the TUI and is installed automatically when possible
- `docker` CLI is required and checked on startup
- `docker compose` (Compose v2 command) is required and checked on startup
- Docker Desktop includes Compose v2 by default; on Linux Engine-only setups you may need the `docker-compose-plugin` package
- Docker daemon must be running before the TUI starts
- Required docker commands are validated (`docker ps/exec/inspect/cp` and `docker compose config/up/down/logs/exec/pull/ps`)
- If package manager installation for `gum` fails, the script can use a GitHub binary fallback

## Options

- `-h`, `--help`
  - Shows usage and exits without starting the TUI
- `--no-installation-fallback`
  - Disables GitHub binary fallback for `gum`
  - If package manager installation fails, the script exits with manual installation guidance

## Apps Catalog

- App options in the wizard are read from:
  - `scripts/easy-docker/config/apps.tsv`
- Format per line:
  - `id<TAB>label<TAB>repo<TAB>default_branch<TAB>branches_csv`
- Example:
  - `erpnext<TAB>ERPNext<TAB>https://github.com/frappe/erpnext<TAB>version-15<TAB>version-15,version-16,develop`
- The install selection in the wizard is limited to apps from this catalog.
- For each selected app, the wizard shows the configured branch list from this catalog and prompts branch selection.

## Frappe Version Profiles

- During new stack creation (after stack name), the wizard asks for a Frappe branch profile from:
  - `scripts/easy-docker/config/frappe.tsv`
- Format per line:
  - `id<TAB>label<TAB>frappe_branch`
- Example:
  - `v16<TAB>Frappe v16 (version-16)<TAB>version-16`
- The selected `frappe_branch` is saved in stack `metadata.json` and used as default branch suggestion for app branch selection.
- In `metadata.json`, this value is stored top-level as:
  - `"frappe_branch": "version-16"` (example)
