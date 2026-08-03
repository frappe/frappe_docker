---
title: Docker Development Setup
---

# Docker Development Setup

A complete guide for setting up a Frappe development environment on x86 and ARM based computers running UNIX based OSes by running containers directly and working inside them via the terminal. No VS Code Dev Containers extension needed.

> [!IMPORTANT]
> Devcontainers are the intended development setup for Frappe Framework but in case you don't want to use that method follow these instructions to use the CLI directly instead

---

## Prerequisites

- **Docker Desktop** (Applicable only for MacOS) — [download here](https://www.docker.com/products/docker-desktop/)
- **Git**
- A terminal (iTerm2, or the built-in Terminal.app)

### Docker Desktop Resource Allocation (Critical)

1. Open Docker Desktop → **Settings** → **Resources**
2. **Memory**: at least **6 GB** (8 GB recommended)
3. **CPUs**: at least **4**
4. **Disk image size**: at least **60 GB**
5. Click **Apply & Restart**

---

## Step 1 — Set ARM64 as Default Platform (ONLY FOR ARM BASED SYSTEMS)

```bash
export DOCKER_DEFAULT_PLATFORM=linux/arm64
```

Make it permanent:

```bash
echo 'export DOCKER_DEFAULT_PLATFORM=linux/arm64' >> ~/.zshrc
source ~/.zshrc
```

---

## Step 2 — Clone the Repo

```bash
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

---

## Step 3 — Set Up the Dev Container Config

The `devcontainer-example/` folder contains a ready-made `docker-compose.yml` for development. Copy it into place:

```bash
cp -R devcontainer-example .devcontainer
```

This gives you `.devcontainer/docker-compose.yml` which defines all the services you need:

- `frappe` — the main development container (Debian, Python, Node, bench)
- `mariadb` — the database
- `redis-cache` — cache layer
- `redis-queue` — background job queue

### Configure ports for CLI-only use

The example configuration is intended for VS Code Dev Containers and forwards development ports through VS Code. Because this setup runs Docker Compose directly, add the following environment variable and loopback-only port mappings to the `frappe` service in `.devcontainer/docker-compose.yml`:

```yaml
services:
  frappe:
    # ... existing config
    environment:
      - SHELL=/bin/bash
      - FRAPPE_BIND_ADDR=0.0.0.0
    ports:
      - "127.0.0.1:8000-8005:8000-8005"
      - "127.0.0.1:9000-9005:9000-9005"
```

Frappe's development server binds to `127.0.0.1` by default. `FRAPPE_BIND_ADDR=0.0.0.0` makes it reachable through Docker's port mappings, while binding the published ports to `127.0.0.1` keeps them accessible only from your local machine.

---

## Step 4 — Add ARM64 Platform to All Services

Open `.devcontainer/docker-compose.yml` in any editor and add `platform: linux/arm64` to every service block. It should look like this:

```yaml
services:
  frappe:
    image: frappe/bench:latest
    platform: linux/arm64
    # ... rest of config

  mariadb:
    image: mariadb:10.8
    platform: linux/arm64
    # ...

  redis-cache:
    image: redis:6.2-alpine
    platform: linux/arm64
    # ...

  redis-queue:
    image: redis:6.2-alpine
    platform: linux/arm64
    # ...
```

> Without this, Docker may pull amd64 images and emulate them via Rosetta — things will work but be noticeably slower.

---

## Step 5 — Start the Containers

```bash
docker compose -f .devcontainer/docker-compose.yml up -d
```

Verify everything is running:

```bash
docker compose -f .devcontainer/docker-compose.yml ps
```

You should see all services with status `Up`.

In case you get any errors along the lines of,

```log
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint devcontainer-frappe-1 (44b337b68d100e914fab0ce446ed08d791cc73aaffb05cf47c347c00ff88f567): Bind for 0.0.0.0:9001 failed: port is already allocated
```

- Check if the port is being used by another service with `lsof -i :PORT`
  > Usually on MacOS ports 8000 and 9000 are usually reserved for system use
- Change the host-side port ranges under the `frappe` service

Eg:

```yaml
ports:
  - "127.0.0.1:8100-8105:8000-8005"
  - "127.0.0.1:9100-9105:9000-9005"
```

With this example, open the first site on port `8100` instead of `8000`.

---

## Step 6 — Enter the Development Container

```bash
docker exec -e "TERM=xterm-256color" -w /workspace/development -it devcontainer-frappe-1 bash
```

> The container name is typically `devcontainer-frappe-1`. If it differs, check with `docker ps` and use the actual name shown.

You are now inside the container as the `frappe` user. All subsequent commands in this guide run **inside the container** unless noted otherwise.

---

## Step 7 — Initialize a Bench

```bash
bench init --skip-redis-config-generation --frappe-branch version-16 frappe-bench
cd frappe-bench
```

Use `version-16` for the latest stable release. Swap for `version-15` if needed.

This creates:

```
development/
└── frappe-bench/
    ├── apps/          ← All Frappe apps live here
    ├── sites/         ← Your sites (databases, uploaded files)
    ├── env/           ← Python virtualenv
    ├── logs/
    └── Procfile
```

---

## Step 8 — Configure Service Hosts

Tell bench to use the containerised services (not localhost):

```bash
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379
```

If any command fails, edit the file directly:

```bash
nano sites/common_site_config.json
```

Paste:

```json
{
  "db_host": "mariadb",
  "redis_cache": "redis://redis-cache:6379",
  "redis_queue": "redis://redis-queue:6379",
  "redis_socketio": "redis://redis-queue:6379"
}
```

---

## Step 9 — Fix the Procfile

Redis runs in separate containers, so remove it from Honcho's Procfile to avoid conflicts:

```bash
sudo sed -i '/redis/d' ./Procfile
```

---

## Step 10 — Create a Site

```bash
bench new-site \
  --db-root-password 123 \
  --admin-password admin \
  --mariadb-user-host-login-scope=% \
  development.localhost
```

- MariaDB root password: `123` (set in the docker-compose defaults)
- Admin password: `admin` (change this to whatever you want)
- Site name **must end in `.localhost`**

---

## Step 11 — Enable Developer Mode

```bash
bench --site development.localhost set-config developer_mode 1
bench --site development.localhost clear-cache
```

---

## Step 12 — Add development.localhost to /etc/hosts (on your Mac)

Run this **on your Mac** (not inside the container):

```bash
echo "127.0.0.1 development.localhost" | sudo tee -a /etc/hosts
```

---

## Step 13 — Start the Dev Server

```bash
bench build # (optional)
bench start
```

Open your browser at **http://development.localhost:8000**
Login: `Administrator` / `admin`
