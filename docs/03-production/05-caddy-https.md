# Caddy reverse proxy (local HTTPS)

This guide shows how to use Caddy as an external reverse proxy in front of the frontend container. It is most useful for local HTTPS or internal networks.

## Prerequisites

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

## Step 3: Trust the Caddy root certificate

When using `tls internal`, Caddy issues certificates from its internal CA. Import and trust the Caddy root certificate on any client that needs to access the site.

See also: [TLS/SSL Setup Overview](01-tls-ssl-setup.md).
