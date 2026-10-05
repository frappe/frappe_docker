---
title: Caddy with HTTPS
---

# Caddy reverse proxy (local HTTPS)

This guide shows how to use Caddy as an external reverse proxy in front of the frontend container. It is most useful for local HTTPS or internal networks.

## Prerequisites

- Cloned `frappe_docker` repository, with commands run from its root
- An `.env` file copied from `example.env` (`cp example.env .env`), with `ERPNEXT_VERSION` and `DB_PASSWORD` set for your deployment
- A directory for the generated Compose file (`mkdir -p ~/gitops`)
- A Frappe site matching the configured hostname; [create the site](../04-operations/01-site-operations.md#setup-new-site) after the stack starts if it does not exist yet
- Expose the frontend container on a host port (default 8080)
- Add a local domain to your hosts file (or use internal DNS)
- Install Caddy

## Step 1: Expose the frontend service

Include the no-proxy override so the frontend is reachable on the host:

```sh
docker compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > ~/gitops/docker-compose.yml

docker compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

If you changed the HTTP port, note the value of `HTTP_PUBLISH_PORT` for the next step.

## Step 2: Configure Caddy

Add a site block to your Caddyfile (usually `/etc/caddy/Caddyfile`):

```caddy
erp.localdev.net {
  tls internal
  reverse_proxy localhost:8080
}
```

Replace `8080` with your published frontend port if you changed it.

Start Caddy using your installation's service manager. On Linux with the official `caddy` systemd service:

```sh
sudo systemctl start caddy
```

If Caddy is already running, apply the Caddyfile changes with `sudo systemctl reload caddy`. For other installations, see [Keep Caddy Running](https://caddyserver.com/docs/running).

## Step 3: Trust the Caddy root certificate

When using `tls internal`, Caddy issues certificates from its internal CA. Import and trust the Caddy root certificate on any client that needs to access the site.

See also: [TLS/SSL Setup Overview](../13-explanation/04-tls-ssl-approaches.md).
