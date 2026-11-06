---
title: TLS/SSL Deployment Choices
---

# TLS/SSL Deployment Choices

The reverse proxy sits between clients and the Frappe frontend. It terminates TLS and routes requests to the frontend, which still serves HTTP inside the deployment. Choosing a proxy therefore involves both routing needs and where responsibility for certificates and public ports belongs.

For supported overrides, required variables, certificate storage, and challenge requirements, see [TLS/SSL options](../12-reference/03-tls-ssl-options.md).

## Routing across sites and benches

Multiple sites do not by themselves require complex routing: several hostnames can all lead to the same bench. nginx-proxy suits this arrangement because a list of hostnames describes the desired route directly. Its separate ACME companion handles certificates for those hosts.

Traefik's rule expressions can combine conditions on hosts, paths, or headers. This gives more flexibility as routing requirements grow, at the cost of maintaining those rules. Its certificate resolver runs in the proxy itself, so routing and certificate issuance share one service.

These routing choices determine which frontend receives a request. They do not create Frappe sites or replace the application's site selection. See [site operations](../04-operations/01-site-operations.md#setup-new-site) for creating the sites behind the proxy.

## A proxy per stack or a shared proxy

Keeping Traefik inside a Frappe stack ties the proxy's deployment and certificate storage to that stack. This keeps one stack self-contained, but separate stacks cannot each bind the same public ports on the same host address.

A central Traefik instance lets several benches share those ports. Each bench joins a shared proxy network and supplies its own routing labels. The proxy can be maintained separately from the benches, but its availability and routing configuration now affect every bench that depends on it. The [single server example](../02-setup/07-single-server-example.md) demonstrates this arrangement with shared infrastructure.

## A proxy managed outside Compose

An existing host proxy can keep certificate management outside the Frappe stack. The stack exposes its frontend on a host port, and the external proxy forwards requests there. This fits environments where a proxy already serves other applications, while making its lifecycle and configuration a separate operational responsibility.

The [Caddy local HTTPS guide](../11-how-to/03-caddy-https.md) uses this model with an internal certificate authority. It is useful for local or internal access because public certificate issuance is unnecessary, but clients must trust that authority. For public deployments, the certificate authority's domain validation requirements still apply; changing a published container port does not change those requirements.
