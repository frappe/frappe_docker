---
title: Forwarded HTTPS
---

# Configure forwarded HTTPS behind a proxy

Use this guide when a proxy terminates HTTPS before forwarding requests to the
Frappe frontend over HTTP. It also covers upgrades of existing proxy deployments.

## Prerequisites

- Use an image containing the current frontend entrypoint and Nginx template.
- Keep Gunicorn's port `8000` unpublished.
- Identify the callers that can reach the frontend and backend. Review
  [proxy trust boundaries](../13-explanation/04-tls-ssl-approaches.md#forwarded-protocol-and-trust-boundaries)
  before trusting forwarded headers on shared networks.

## Choose Gunicorn's trusted proxies

For a controlled stack where every caller that can reach the backend is trusted,
set this value in the deployment's environment file:

```dotenv
FORWARDED_ALLOW_IPS=*
```

To limit forwarded-header trust to a particular frontend, reserve a stable IP for
that frontend on the network it uses to reach the backend, and list it
explicitly. Replace the example address below with that reserved address:

```dotenv
FORWARDED_ALLOW_IPS=127.0.0.1,::1,172.23.0.4
```

This limits trust on the final hop to Gunicorn. Restrict access to the frontend
separately when callers on its networks must not be trusted together.

## Select the frontend mode

The supplied Traefik and nginx-proxy overrides enable forwarded-protocol handling
automatically. For a custom TLS proxy, including a host proxy in front of
`compose.noproxy.yaml`, set:

```dotenv
TRUST_UPSTREAM_FORWARDED_PROTO=on
```

Restrict frontend access to trusted proxies or internal services. The public
proxy must replace client-supplied protocol claims with the actual connection
protocol. The supplied public nginx-proxy recipe does this with
`TRUST_DOWNSTREAM_PROXY=false`.

For direct HTTP access without an upstream TLS proxy, leave the frontend mode
at `off`.

**Upgrading:** previous images accepted incoming HTTPS indications
unconditionally. Set `TRUST_UPSTREAM_FORWARDED_PROTO=on` for custom TLS proxies
before upgrading the frontend image. Changing Gunicorn's environment setting
does not require rebuilding the image; updating the Nginx assets does.

## Apply and verify the configuration

If you deploy a generated Compose YAML file, regenerate it with the updated
environment first. Reuse your deployment's normal `docker compose` invocation,
including its project name, environment file and Compose files, with the arguments
`up -d --force-recreate backend frontend`. This recreates both services. A restart
alone does not apply changed environment values.

Start an OAuth authorization flow through the public HTTPS address while logged
out of Frappe. The login redirect's nested `redirect-to` URL should use HTTPS and
retain the original authorization parameters. After login, authorization should
continue and return to the client application.

For defaults and accepted values, see the
[Gunicorn settings](../02-setup/04-env-variables.md#backend-gunicorn-configuration)
and [frontend settings](../02-setup/04-env-variables.md#frontend-nginx-configuration-inside-the-frontend-container).
