# Easy-Frappe-Docker

Easy installation script for Frappe Docker for development and production

## Run

```bash
bash ./easy-docker.sh
```

Run the entrypoint from a real Bash environment.

- On Linux, use your normal shell session.
- On Windows, use WSL or Git Bash.
- If you start `bash` from PowerShell, that usually means WSL, so keep the path
  in Bash form such as `bash ./easy-docker.sh`, not `bash .\easy-docker.sh`.

## Dependencies

- `gum` is used for the TUI and is installed automatically when possible
- `docker` CLI is required and checked on startup
- `docker compose` (Compose v2 command) is required and checked on startup
- `jq` is required for stack JSON handling and is checked on startup
- Docker Desktop includes Compose v2 by default; on Linux Engine-only setups you may need the `docker-compose-plugin` package
- Docker daemon must be running before the TUI starts
- Required docker commands are validated (`docker ps/exec/inspect/cp` and `docker compose config/up/down/logs/exec/pull/ps`)
- Startup validation order is: CLI options, `gum`, `docker`, then `jq`
- If package manager installation for `gum` or `jq` fails, the script can use a pinned GitHub binary fallback
- The `gum` fallback is pinned to `gum` `v0.17.0` and verifies SHA256 checksums from `scripts/easy-docker/config/gum-checksums.tsv`
- The `jq` fallback is pinned to `jq` `1.8.1` and verifies SHA256 checksums from `scripts/easy-docker/config/jq-checksums.tsv`
- `docker` still has no installation fallback path and must already be present
- Runtime `jq` resolution accepts either `jq` or `jq.exe`, so Windows-native setups with only `jq.exe` on `PATH` are supported

## JSON Handling

- `metadata.json` remains the source of truth for stack state
- `apps.json` is still generated from stack metadata and still used for the image build
- `easy-docker` now reads and writes stack JSON through `jq` instead of line-based `awk` parsing
- This is an internal robustness change only; the generated layout of `metadata.json` and `apps.json` is intended to stay the same for users

## Options

- `-h`, `--help`
  - Shows usage and exits without starting the TUI
- `--no-installation-fallback`
  - Disables GitHub binary fallback prompts for `gum` and `jq`
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
