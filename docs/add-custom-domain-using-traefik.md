Add following labels to `frontend` service

```yaml
traefik.http.routers.custom-domain.rule: Host(`custom.localhost`)
# Comment the entrypoints label if traefik already has default entrypoint set
traefik.http.routers.custom-domain.entrypoints: web
traefik.http.middlewares.custom-domain.headers.customrequestheaders.Host: mysite.localhost
traefik.http.routers.custom-domain.middlewares: custom-domain
# Add following header only if TLS is needed in case of live server
traefik.http.routers.custom-domain.tls.certresolver: main-resolver
```

Example:

```yaml
frontend:
  ...
  labels:
    ...
    traefik.http.routers.custom-domain.rule: Host(`custom.localhost`)
    traefik.http.routers.custom-domain.entrypoints: web
    traefik.http.middlewares.custom-domain.headers.customrequestheaders.Host: mysite.localhost
    traefik.http.routers.custom-domain.middlewares: custom-domain
    traefik.http.routers.custom-domain.tls.certresolver: main-resolver
    ...
```

This will add `custom.localhost` as custom domain for `mysite.localhost`
