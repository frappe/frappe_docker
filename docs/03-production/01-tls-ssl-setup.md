# TLS/SSL Setup Overview

Frappe Docker supports multiple TLS/SSL approaches. Choose the one that matches your routing needs and where you want the proxy to run.

## Options

### Traefik (built-in HTTPS)

- Use `overrides/compose.https.yaml`
- Best for multi-site setups and advanced routing rules
- Requires `SITES_RULE` and `LETSENCRYPT_EMAIL`
- See [Environment Variables](../02-setup/04-env-variables.md) and [Setup Examples](../02-setup/06-setup-examples.md#example-3-production-setup-with-https)

#### Traefik deployment models

- **Single stack (Traefik inside the stack):**
  - Use `compose.proxy.yaml` (HTTP) or `compose.https.yaml` (HTTPS)
  - Traefik runs as `proxy` in the same stack
- **Central Traefik for multiple stacks:**
  - Run a dedicated Traefik stack with `compose.traefik.yaml` (and optional `compose.traefik-ssl.yaml` for the dashboard)
  - Each Frappe stack uses `compose.multi-bench.yaml` (and optional `compose.multi-bench-ssl.yaml`)
  - This connects stacks to the shared `traefik-public` network

### nginx-proxy + acme-companion

- Use `overrides/compose.nginxproxy.yaml` plus `overrides/compose.nginxproxy-ssl.yaml`
- Simple host-based routing for single-bench or small setups
- Requires `NGINX_PROXY_HOSTS` and `LETSENCRYPT_EMAIL`
- See [nginx-proxy + acme-companion](04-nginx-proxy-acme-companion.md)

## Traefik vs nginx-proxy + acme-companion

| Topic               | Traefik (compose.https.yaml)                  | nginx-proxy + acme-companion                                                   |
| ------------------- | --------------------------------------------- | ------------------------------------------------------------------------------ |
| Configuration       | Labels with `SITES_RULE` expression           | Environment variables (`NGINX_PROXY_HOSTS`)                                    |
| Routing             | Flexible (rules, headers, paths)              | Host-based only                                                                |
| Multi-site          | Strong                                        | Works for simple host lists                                                    |
| TLS/ACME            | Built-in                                      | Separate companion container                                                   |
| Certificate storage | `cert-data` volume (`/letsencrypt/acme.json`) | `nginx-proxy-certs` + `acme-data` volumes (`/etc/nginx/certs`, `/etc/acme.sh`) |
| Complexity          | Moderate                                      | Low                                                                            |
| Observability       | Optional dashboard (not enabled here)         | No built-in dashboard                                                          |

### Caddy (external reverse proxy)

- Run Caddy on the host and proxy to the frontend container
- Useful for local HTTPS or when you already use Caddy
- See [Caddy reverse proxy](05-caddy-https.md)

## Common requirements

- DNS must point to the server for public TLS certificates
- Ports 80 and 443 must be reachable for HTTP-01 challenges
- Use `HTTP_PUBLISH_PORT` and `HTTPS_PUBLISH_PORT` if you need non-default ports
