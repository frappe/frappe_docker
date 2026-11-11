---
title: Environment Variables
---

# Environment Variables Reference

Environment variables configure your Frappe Docker setup. They can be set directly in the container or defined in a `.env` file referenced by Docker Compose.

**Getting Started:**

```bash
cp example.env .env
```

Then edit `.env` and set variables according to your needs.

---

## Required Variables

| Variable          | Purpose                                          | Example                          | Notes                                                            |
| ----------------- | ------------------------------------------------ | -------------------------------- | ---------------------------------------------------------------- |
| `FRAPPE_PATH`     | Frappe framework path                            | https://github.com/frappe/frappe |                                                                  |
| `FRAPPE_BRANCH`   | Frappe Branch                                    | `version-15`                     | See [Frappe releases](https://github.com/frappe/frappe/releases) |
| `ERPNEXT_VERSION` | ERPNext release version                          | `v15.67.0`                       | Required although its never used                                 |
| `DB_PASSWORD`     | Password for database root (MariaDB or Postgres) | `secure_password_123`            | Not needed if using `DB_PASSWORD_SECRETS_FILE`                   |

---

## Database Configuration

| Variable                   | Purpose                                   | Default                              | When to Set                        |
| -------------------------- | ----------------------------------------- | ------------------------------------ | ---------------------------------- |
| `DB_PASSWORD`              | Database root user password               | 123                                  | Always (unless using secrets file) |
| `DB_PASSWORD_SECRETS_FILE` | Path to file containing database password | —                                    | Setup mariadb-secrets overrider    |
| `DB_HOST`                  | Database hostname or IP                   | `db` (service name)                  | Only if using external database    |
| `DB_PORT`                  | Database port                             | `3306` (MariaDB) / `5432` (Postgres) | Only if using external database    |

---

## Redis Configuration

| Variable      | Purpose                                             | Default                      | When to Set                           |
| ------------- | --------------------------------------------------- | ---------------------------- | ------------------------------------- |
| `REDIS_CACHE` | Redis hostname for caching                          | `redis-cache` (service name) | Only if using external Redis instance |
| `REDIS_QUEUE` | Redis hostname for job queues and real-time updates | `redis-queue` (service name) | Only if using external Redis instance |

---

## Volume Bind Mounts

| Variable                    | Purpose                                                                                      | Default | When to Set                                        |
| --------------------------- | -------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------- |
| `SITES_DATA_LOCATION`       | Host directory for the `sites` volume; must be an absolute path and already exist            | -       | Required for `compose.bind-mount-sites.yaml`       |
| `DB_DATA_LOCATION`          | Host directory for the `db-data` volume; must be an absolute path and already exist          | -       | Required for `compose.bind-mount-db-data.yaml`     |
| `REDIS_QUEUE_DATA_LOCATION` | Host directory for the `redis-queue-data` volume; must be an absolute path and already exist | -       | Required for `compose.bind-mount-redis-queue.yaml` |

The host directory must exist before `docker compose up -d` and must be writable by the user the container runs as:

| Directory          | Owner / Permissions                                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `sites`            | uid `1000`, gid `0` (root group) with group write permissions (`chmod -R g=u` or `775`), supporting arbitrary UIDs in OpenShift |
| `db-data`          | uid/gid `999` (the `mariadb` or `postgres` image)                                                                               |
| `redis-queue-data` | uid/gid `999` (the `redis` image)                                                                                               |

> Warning: with a bind mount, the data lives on the host, not inside the Docker volume. Removing the volume (for example with `docker compose down -v`) will **not** delete the data. To actually erase the data, delete the host directory manually with `rm -r <data path>`.

**Example:**

```bash
mkdir -p /srv/frappe/{sites,db-data,redis-queue-data}
chown 1000:0 /srv/frappe/sites && chmod 775 /srv/frappe/sites
chown 999:999 /srv/frappe/db-data /srv/frappe/redis-queue-data
```

```bash
SITES_DATA_LOCATION=/srv/frappe/sites
DB_DATA_LOCATION=/srv/frappe/db-data
REDIS_QUEUE_DATA_LOCATION=/srv/frappe/redis-queue-data
```

---

## Reverse Proxy and SSL (HTTPS) Configuration

### Traefik (compose.proxy.yaml / compose.https.yaml)

| Variable            | Purpose                                          | Default | When to Set                                  |
| ------------------- | ------------------------------------------------ | ------- | -------------------------------------------- |
| `LETSENCRYPT_EMAIL` | Email for Let's Encrypt certificate registration | -       | Required for `compose.https.yaml`            |
| `SITES_RULE`        | Domains for routing (Traefik rule expression)    | -       | Required for Traefik routing/HTTPS overrides |

**Format for `SITES_RULE`:**

```bash
# Single site
SITES_RULE=Host(`mysite.example.com`)

# Multiple sites
SITES_RULE=Host(`a.example.com`) || Host(`b.example.com`)
```

> Note: The Traefik v3 migration is complete. Use `SITES_RULE` as a full v3 rule expression; `SITES` is deprecated.
> Rule syntax now defaults to v3, so no `core.defaultRuleSyntax` or per-router `ruleSyntax` settings are required.

### nginx-proxy + acme-companion (compose.nginxproxy\*.yaml)

| Variable            | Purpose                                   | Default | When to Set                                |
| ------------------- | ----------------------------------------- | ------- | ------------------------------------------ |
| `LETSENCRYPT_EMAIL` | Email for Let's Encrypt certificate       | -       | Required for `compose.nginxproxy-ssl.yaml` |
| `NGINX_PROXY_HOSTS` | Comma-separated hostnames for nginx-proxy | -       | Required for `compose.nginxproxy*.yaml`    |

**Example:**

```bash
NGINX_PROXY_HOSTS=example.com,www.example.com
```

> Note: Automatic certificates require port 80 to be reachable (HTTP-01).

### Published Ports (Traefik and nginx-proxy)

| Variable             | Purpose              | Default                         | When to Set                  |
| -------------------- | -------------------- | ------------------------------- | ---------------------------- |
| `HTTP_PUBLISH_PORT`  | Published HTTP port  | `80` (proxy) / `8080` (noproxy) | Change if port is in use     |
| `HTTPS_PUBLISH_PORT` | Published HTTPS port | `443`                           | Change if port 443 is in use |

---

## Site Configuration

| Variable                  | Purpose                          | Default                                  | When to Set                                     |
| ------------------------- | -------------------------------- | ---------------------------------------- | ----------------------------------------------- |
| `FRAPPE_SITE_NAME_HEADER` | Site name for multi-tenant setup | `$host` (resolved from request hostname) | When accessing by IP or need explicit site name |

**Examples:**

If your site is named `mysite` but you want to access it via `127.0.0.1`:

```bash
FRAPPE_SITE_NAME_HEADER=mysite
```

If your site is named `example.com` and you access it via that domain, no need to set this (defaults to hostname).

---

## Image Configuration

| Variable         | Purpose                        | Default               | Notes                                                   |
| ---------------- | ------------------------------ | --------------------- | ------------------------------------------------------- |
| `CUSTOM_IMAGE`   | Custom Docker image repository | Frappe official image | Leave empty to use default                              |
| `CUSTOM_TAG`     | Custom Docker image tag        | Latest stable         | Corresponds to `FRAPPE_VERSION`                         |
| `PULL_POLICY`    | Image pull behavior            | `always`              | Options: `always`, `never`, `if-not-present`            |
| `RESTART_POLICY` | Container restart behavior     | `unless-stopped`      | Options: `no`, `always`, `unless-stopped`, `on-failure` |

---

## Backend (Gunicorn) Configuration

| Variable              | Purpose                                                        | Default         | When to Set / Allowed Values                                                                 |
| :-------------------- | :------------------------------------------------------------- | :-------------- | :------------------------------------------------------------------------------------------- |
| `GUNICORN_WORKERS`    | Number of worker processes handling web requests               | `2`             | Scale up for multi-core CPUs. Formula: `(2 x Cores) + 1`                                     |
| `GUNICORN_THREADS`    | Number of concurrent threads per worker process                | `4`             | Increase to handle more simultaneous I/O-bound requests without high memory cost             |
| `GUNICORN_TIMEOUT`    | Max time a worker can spend on a single request before restart | `120`           | Increase if long-running reports or data imports time out                                    |
| `FORWARDED_ALLOW_IPS` | Proxy IPs Gunicorn trusts for forwarded HTTPS information      | `127.0.0.1,::1` | Comma-separated IP addresses, or `*` when all callers that can reach the backend are trusted |

### Forwarded HTTPS and OAuth redirects

When TLS terminates at an upstream proxy, both Nginx and Gunicorn must recognize the
original HTTPS connection. Otherwise, request-based URLs, including the OAuth
authorization return URL saved before login, can incorrectly use HTTP.

For a self-contained Compose stack whose internal services are all trusted, set:

```dotenv
FORWARDED_ALLOW_IPS=*
```

Gunicorn reads this variable directly; no image rebuild is needed to change it.
Recreate the backend with your existing Compose files after changing the value.
The Traefik and nginx-proxy overrides enable Nginx's forwarded-protocol handling
automatically. A custom upstream proxy also requires
`TRUST_UPSTREAM_FORWARDED_PROTO=on` on the frontend.

`*` does not publish a port or grant connection access. It trusts forwarded
information from every caller that can already reach Gunicorn. Keep port `8000`
unpublished and review every network the backend joins. The multi-bench override
also connects the backend to the shared `mariadb-network`, so this trust includes
other benches on that network. Use `*` there only if those benches share the same
trust boundary. An explicit allowlist requires stable proxy IP addresses;
Gunicorn 23 does not accept DNS names or CIDR ranges for this setting.

The Nginx frontend clears `X-Forwarded-SSL` and `X-Forwarded-Protocol` so that
Gunicorn receives one consistent protocol indication in `X-Forwarded-Proto`.

---

## Frontend Nginx Configuration (inside the frontend container)

| Variable                         | Purpose                                                                              | Default                                | Allowed Values                               |
| -------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------- | -------------------------------------------- |
| `NGINX_LISTEN_PORT`              | Sets the `listen` directive                                                          | `8080`                                 | `{port}`                                     |
| `TRUST_UPSTREAM_FORWARDED_PROTO` | Preserve an upstream HTTPS indication instead of using Nginx's own connection scheme | `off`; proxy overrides default to `on` | `on` or `off`                                |
| `BACKEND`                        | Backend service address and port                                                     | `0.0.0.0:8000`                         | `{host}:{port}`                              |
| `SOCKETIO`                       | Socket.IO service address and port                                                   | `0.0.0.0:9000`                         | `{host}:{port}`                              |
| `PROXY_READ_TIMEOUT`             | Upstream request timeout                                                             | `120s`                                 | Any nginx timeout value (e.g., `300s`, `5m`) |
| `CLIENT_MAX_BODY_SIZE`           | Maximum upload file size                                                             | `50m`                                  | Any nginx size value (e.g., `100m`, `1g`)    |

With `TRUST_UPSTREAM_FORWARDED_PROTO=on`, Nginx accepts an incoming
`X-Forwarded-Proto: https` indication. Restrict frontend access to trusted proxies
or internal services, and have the public proxy replace client-supplied protocol
headers. This mode does not check the upstream's IP address.

The base configuration, `compose.noproxy.yaml`, and images used directly default
to `off`, so clients cannot override the connection scheme during direct HTTP
access. The Traefik and nginx-proxy overrides default to `on`. An explicit
environment value overrides either default.

**Compatibility:** images previously preserved incoming HTTPS indications
unconditionally. When upgrading a deployment that uses a custom TLS proxy or
uses `compose.noproxy.yaml` behind a TLS proxy, set
`TRUST_UPSTREAM_FORWARDED_PROTO=on` on the frontend. Updating these Nginx assets
requires a new image; the environment setting alone cannot update an old image.

### Real IP Configuration (Behind Proxy)

Use these variables when running behind a reverse proxy or load balancer:

| Variable                     | Purpose                                           | Default           |
| ---------------------------- | ------------------------------------------------- | ----------------- |
| `UPSTREAM_REAL_IP_ADDRESS`   | Trusted upstream IP address for real IP detection | `127.0.0.1`       |
| `UPSTREAM_REAL_IP_HEADER`    | Request header containing client IP               | `X-Forwarded-For` |
| `UPSTREAM_REAL_IP_RECURSIVE` | Enable recursive IP search                        | `off`             |

---

## Migration Service

| Variable        | Purpose                         | Default                    | Allowed Values   |
| --------------- | ------------------------------- | -------------------------- | ---------------- |
| `MIGRATE_SITES` | Switch auto migration on or off | `true` - auto migration on | `true` , `false` |
