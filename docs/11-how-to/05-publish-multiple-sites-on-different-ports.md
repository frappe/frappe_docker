---
title: Publish Multiple Sites on Different Ports
---

# Publish multiple sites on different ports

Publish multiple Frappe sites (tenants) from the same bench on separate host ports, using one frontend service for each site.

WARNING: Do not use this in production if the site is going to be served over plain http.

Use an existing Compose setup with `backend`, `websocket`, and the `sites` volume. [Create each Frappe site](../04-operations/01-site-operations.md#setup-new-site) before serving it. Use the same environment file as the bench so that the additional frontend services use the same image and tag.

## Step 1

The additional frontend services below publish each site's port directly on the host, so this setup does not require a reverse proxy. When generating a Compose file for this example, omit reverse-proxy overrides such as `compose.proxy.yaml`, `compose.https.yaml`, `compose.nginxproxy.yaml`, and `compose.nginxproxy-ssl.yaml`.

An existing reverse proxy can remain for other routes if its published ports do not overlap with those below. Do not include `compose.noproxy.yaml` with its default settings: it already publishes port `8080`, which conflicts with `port-site-1`.

## Step 2

Add service for each port that needs to be exposed.

e.g. `port-site-1`, `port-site-2`, `port-site-3`.

```yaml
# ... removed for brevity
services:
  # ... removed for brevity
  port-site-1:
    image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-$ERPNEXT_VERSION}
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - nginx-entrypoint.sh
    environment:
      BACKEND: backend:8000
      FRAPPE_SITE_NAME_HEADER: site1.local
      SOCKETIO: websocket:9000
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    ports:
      - "8080:8080"
  port-site-2:
    image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-$ERPNEXT_VERSION}
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - nginx-entrypoint.sh
    environment:
      BACKEND: backend:8000
      FRAPPE_SITE_NAME_HEADER: site2.local
      SOCKETIO: websocket:9000
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    ports:
      - "8081:8080"
  port-site-3:
    image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-$ERPNEXT_VERSION}
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - nginx-entrypoint.sh
    environment:
      BACKEND: backend:8000
      FRAPPE_SITE_NAME_HEADER: site3.local
      SOCKETIO: websocket:9000
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    ports:
      - "8082:8080"
```

Notes:

- Above setup will expose `site1.local`, `site2.local`, `site3.local` on port `8080`, `8081`, `8082` respectively.
- Change `site1.local` to site name to serve from bench.
- Change the `BACKEND` and `SOCKETIO` environment variables as per your service names.
- Make sure `sites:` volume is available as part of yaml.
