---
title: Caddy with HTTPS
---

# Caddy reverse proxy (local HTTPS)

This guide shows how to use Caddy running on the host as an external reverse proxy in front of the frontend container. It is most useful for local HTTPS or internal networks.

The usual Frappe Docker setup is assumed. [Create the Frappe sites](../04-operations/01-site-operations.md#setup-new-site) for your hostnames if they do not exist yet.

## Prerequisites

- Publish the frontend's HTTP port on localhost for Caddy (8080 in this example)
- Add a local domain to your hosts file (or use internal DNS)
- Install Caddy

## Step 1: Expose the frontend service

Set these values in the `.env` file before generating the Compose configuration:

```dotenv
HTTP_PUBLISH_PORT=127.0.0.1:8080
TRUST_UPSTREAM_FORWARDED_PROTO=on
FORWARDED_ALLOW_IPS=*
```

Caddy terminates HTTPS and forwards the original protocol to Nginx over HTTP.
The frontend must trust that indication, and Gunicorn must trust the frontend.
Publish the frontend only on localhost so remote clients cannot bypass Caddy and
submit their own protocol headers. Keep backend port 8000 unpublished.

`FORWARDED_ALLOW_IPS=*` assumes all callers on the backend's Docker networks are
trusted together. If the backend joins shared networks with untrusted callers,
use a stable frontend IP and an explicit Gunicorn allowlist instead. See
[forwarded HTTPS and OAuth redirects](../02-setup/04-env-variables.md#forwarded-https-and-oauth-redirects).

Include the no-proxy override to publish the frontend for the host proxy:

```sh
docker compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > ~/gitops/docker-compose.yml

docker compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

If you change the published port, keep the `127.0.0.1:` binding and use that port
in the Caddyfile below. These Nginx settings require an image containing the
updated entrypoint and template; rebuild a custom image when testing local changes.

## Step 2: Configure Caddy

Add a site block to your Caddyfile (usually `/etc/caddy/Caddyfile`):

```caddy
erp.localdev.net {
  tls internal
  reverse_proxy 127.0.0.1:8080
}
```

Replace `8080` with your published frontend port if you changed it.

Apply the Caddyfile changes using the start or reload method for your Caddy installation. See [Keep Caddy Running](https://caddyserver.com/docs/running).

The `custom-domain` service in `compose.custom-domain.yaml` is a different setup: it runs Caddy in a container behind Traefik, forwarding to `frontend` on its internal listen port (8080 by default). That container starts Caddy automatically; it does not use `systemctl`. See [Create custom domain to existing site](../02-setup/07-single-server-example.md#create-custom-domain-to-existing-site).

## Step 3: Trust the Caddy root certificate

When using `tls internal`, Caddy issues certificates from its internal CA. Import and trust the Caddy root certificate on any client that needs to access the site.

See also: [TLS/SSL options](../12-reference/03-tls-ssl-options.md) and [TLS/SSL deployment choices](../13-explanation/04-tls-ssl-approaches.md).
