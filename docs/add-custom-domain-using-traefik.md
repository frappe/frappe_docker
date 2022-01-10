Add following labels to *-nginx service

```yaml
  - "traefik.http.routers.custom-domain.rule=Host(`custom.localhost`)"
  # Comment the entrypoints label if traefik already has default entrypoint set
  - "traefik.http.routers.custom-domain.entrypoints=web"
  - "traefik.http.middlewares.custom-domain.headers.customrequestheaders.Host=mysite.localhost"
  - "traefik.http.routers.custom-domain.middlewares=custom-domain"
  # Add following header only if TLS is needed in case of live server, use one of below
  - "traefik.http.routers.custom-domain.tls.certresolver=myresolver" # For Single Bench
  - "traefik.http.routers.custom-domain.tls.certresolver=le" # For Docker Swarm
```

Example:

```yaml
frontend:
  image: frappe/erpnext-nginx:${ERPNEXT_VERSION}
  restart: on-failure
  environment:
    - FRAPPE_PY=erpnext-python
    - FRAPPE_PY_PORT=8000
    - FRAPPE_SOCKETIO=frappe-socketio
    - SOCKETIO_PORT=9000
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.frontend.rule=Host(${SITES})"
    - "traefik.http.routers.custom-domain.rule=Host(`custom.localhost`)"
    - "traefik.http.routers.custom-domain.entrypoints=web"
    - "traefik.http.middlewares.custom-domain.headers.customrequestheaders.Host=mysite.localhost"
    - "traefik.http.routers.custom-domain.middlewares=custom-domain"
    # Add following header only if TLS is needed in case of live server
    - "traefik.http.routers.custom-domain.tls.certresolver=myresolver"
    - "${ENTRYPOINT_LABEL}"
    - "${CERT_RESOLVER_LABEL}"
    - "traefik.http.services.frontend.loadbalancer.server.port=80"
  volumes:
    - sites-vol:/var/www/html/sites:rw
    - assets-vol:/assets:rw
```

This will add `custom.localhost` as custom domain for `mysite.localhost`
