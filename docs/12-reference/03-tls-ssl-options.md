---
title: TLS/SSL Options
---

# TLS/SSL Options

This page lists the proxy overrides and TLS settings supplied by Frappe Docker. For the reasons to choose a routing or deployment model, see [TLS/SSL deployment choices](../13-explanation/04-tls-ssl-approaches.md).

All override paths below are relative to `overrides/` in the repository root. Add Frappe stack overrides to `compose.yaml`; the central Traefik stack runs separately.

## Traefik inside a Frappe stack

- **HTTP:** `compose.proxy.yaml` supplies the `proxy` service and a catch-all frontend router. It does not require `SITES_RULE`.
- **HTTPS:** `compose.https.yaml` supplies the `proxy` service, redirects HTTP to HTTPS, and enables its built-in ACME resolver. Use it instead of the HTTP override.
- **Required for HTTPS:** `SITES_RULE` (a Traefik rule expression) and `LETSENCRYPT_EMAIL`.
- **Certificate storage:** `cert-data` volume, with ACME data at `/letsencrypt/acme.json`.
- **Dashboard:** not enabled by these overrides.

See [environment variables](../02-setup/04-env-variables.md#reverse-proxy-and-ssl-https-configuration) for rule syntax and [the HTTPS setup example](../02-setup/06-setup-examples.md#example-3-production-setup-with-https) for deployment commands.

## Central Traefik for multiple stacks

- **Proxy stack:** `compose.traefik.yaml`; add `compose.traefik-ssl.yaml` to enable HTTPS and the ACME resolver for both the dashboard and connected benches.
- **Each Frappe stack:** `compose.multi-bench.yaml`; add `compose.multi-bench-ssl.yaml` for HTTPS routes and HTTP-to-HTTPS redirection through the central proxy.
- **Required in the proxy stack:** `TRAEFIK_DOMAIN` and `HASHED_PASSWORD` for the dashboard; `EMAIL` when enabling HTTPS. This setup uses `EMAIL`, not `LETSENCRYPT_EMAIL`.
- **Required in each Frappe stack:** `ROUTER` (a distinct router/service name for the bench) and `SITES_RULE`.
- **Networks:** the proxy creates `traefik-public`, which each Frappe stack joins as an external network. The multi-bench override also expects the external `mariadb-network` from the shared database setup.
- **Certificate storage:** `cert-data` volume in the proxy stack, with ACME data at `/certificates/acme.json`.
- **Dashboard:** enabled with HTTP Basic authentication; adding the SSL override serves it over HTTPS.

See [the single server example](../02-setup/07-single-server-example.md) for proxy, database, and bench configuration.

## nginx-proxy with acme-companion

- **HTTP:** `compose.nginxproxy.yaml` supplies `nginx-proxy` and sets the frontend's `VIRTUAL_HOST` and `VIRTUAL_PORT`.
- **HTTPS:** also include `compose.nginxproxy-ssl.yaml`, which supplies `acme-companion` and sets the frontend's `LETSENCRYPT_HOST`.
- **Required:** `NGINX_PROXY_HOSTS` (comma-separated hostnames); `LETSENCRYPT_EMAIL` when enabling HTTPS.
- **Certificate storage:** shared `nginx-proxy-certs` volume at `/etc/nginx/certs`, plus `acme-data` at `/etc/acme.sh` in the companion. The overrides also share the `nginx-proxy-html` and `nginx-proxy-vhost` volumes.
- **Dashboard:** none supplied.

See [nginx-proxy + acme-companion](../11-how-to/02-nginx-proxy-acme-companion.md) for deployment commands.

## Caddy on the host

- **Frontend access:** `compose.noproxy.yaml` publishes the frontend's HTTP port for the external proxy.
- **Proxy configuration:** managed on the host, outside the Compose stack.
- **Local certificates:** the documented `tls internal` configuration uses Caddy's internal CA; clients must trust its root certificate. Public DNS and public ACME validation are not required for this local configuration.

See [Caddy reverse proxy](../11-how-to/03-caddy-https.md) for the local HTTPS recipe. The `compose.custom-domain.yaml` override is a separate arrangement that runs Caddy in a container behind central Traefik; see [custom domains for an existing site](../02-setup/07-single-server-example.md#create-custom-domain-to-existing-site).

## Routing and certificate comparison

| Property                                 | Traefik inside a stack                          | Central Traefik                                 | nginx-proxy + acme-companion            |
| ---------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | --------------------------------------- |
| Route configuration                      | Labels with a `SITES_RULE` expression for HTTPS | Labels with a `SITES_RULE` expression per bench | Host list in `NGINX_PROXY_HOSTS`        |
| Multiple sites                           | Hostnames can be combined in a rule             | Separate bench routes share one proxy           | Multiple hostnames can share a frontend |
| Certificate management                   | Built-in ACME resolver                          | Built-in ACME resolver shared by benches        | Separate ACME companion container       |
| ACME challenge in the supplied overrides | HTTP-01                                         | TLS-ALPN-01                                     | HTTP-01                                 |

## DNS and published ports

Public certificates require DNS for the requested hostnames to resolve to the proxy's publicly reachable address. The HTTP-01 configurations require public port 80 to reach the proxy for validation; central Traefik's TLS-ALPN-01 configuration requires public port 443. HTTPS clients normally connect on port 443. Central Traefik also publishes port 80 for HTTP routes and redirects. See [Let's Encrypt challenge types](https://letsencrypt.org/docs/challenge-types/) for validation details.

`HTTP_PUBLISH_PORT` and `HTTPS_PUBLISH_PORT` change the host ports published by the Traefik and nginx-proxy overrides; their defaults are `80` and `443`. If you change them, public traffic must still reach the ports required by the configured challenge, for example through upstream port forwarding.

With `compose.noproxy.yaml`, `HTTP_PUBLISH_PORT` defaults to `8080` and publishes the frontend directly. A host Caddy configuration must target that published port. See [published ports](../02-setup/04-env-variables.md#published-ports-traefik-and-nginx-proxy) for the variable lookup.
