# nginx-proxy + acme-companion (HTTPS)

This guide explains how to use nginx-proxy with acme-companion to provide HTTPS for a Frappe Docker stack.

## When to choose this

- You want a simple, host-based reverse proxy
- You run a single bench or only a few hostnames
- You prefer environment-variable based configuration

If you need advanced routing or complex multi-site setups, **Traefik** is usually the better choice.

## Prerequisites

- Public DNS points your domain(s) to the server
- Ports 80 and 443 are reachable (HTTP-01 challenge)
- Docker and Docker Compose v2 installed

## Required environment variables

Set these in `.env`:

```bash
NGINX_PROXY_HOSTS=erp.your-domain.com
LETSENCRYPT_EMAIL=admin@your-domain.com
```

Multiple hostnames (comma-separated, no spaces):

```bash
NGINX_PROXY_HOSTS=erp.your-domain.com,erp2.your-domain.com
LETSENCRYPT_EMAIL=admin@example.com
```

Optional (non-default ports):

```bash
HTTP_PUBLISH_PORT=80
HTTPS_PUBLISH_PORT=443
```

## Compose setup (HTTPS)

For HTTPS you must include both overrides:

- `overrides/compose.nginxproxy.yaml` (nginx-proxy, VIRTUAL_HOST)
- `overrides/compose.nginxproxy-ssl.yaml` (acme-companion, LETSENCRYPT_HOST)

Example:

```sh
docker compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.nginxproxy.yaml \
  -f overrides/compose.nginxproxy-ssl.yaml \
  config > ~/gitops/docker-compose.yml

docker compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

> If you use external MariaDB/Redis, replace the database and Redis overrides accordingly.

## How hostnames are applied

`NGINX_PROXY_HOSTS` is a comma-separated list of hostnames. The overrides apply it as:

- `VIRTUAL_HOST` for nginx-proxy routing
- `LETSENCRYPT_HOST` for certificate issuance

## Verify

Check logs for certificate issuance and proxy status:

```sh
docker compose --project-name <project-name> -f ~/gitops/docker-compose.yml logs -f nginx-proxy
docker compose --project-name <project-name> -f ~/gitops/docker-compose.yml logs -f acme-companion
```

> Depending on the registrar, the assignment may take some time, whereby it must also be ensured that A and AAAA records are correctly directed to the server for the issuance of the certificate, if necessary.

See also: [Environment Variables](../02-setup/04-env-variables.md) and [TLS/SSL Setup Overview](01-tls-ssl-setup.md).
