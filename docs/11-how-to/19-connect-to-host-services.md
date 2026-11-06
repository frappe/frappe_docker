---
title: Connect to Host Services
---

# Connect the development container to host services

Use this with an existing [development container](../05-development/01-development.md) when it needs to reach services on the Docker host by a local domain name.

Add following to frappe container from the `.devcontainer/docker-compose.yml`:

```yaml
...
  frappe:
    ...
    extra_hosts:
      app1.localhost: 172.17.0.1
      app2.localhost: 172.17.0.1
...
```

Recreate the development container after changing the Compose configuration. The domain names `app1.localhost` and `app2.localhost` will then resolve to `172.17.0.1` inside the container. Replace this address if your Docker host uses a different gateway address. Host services must listen on an address reachable from the container.
