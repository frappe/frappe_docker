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
