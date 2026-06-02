---
title: Docker Bind Mounts
---

# Docker Bind Mounts

## What Are Bind Mounts?

Bind mounts create a direct connection between a directory on your host machine and a directory inside a container. Changes in either location are immediately reflected in the other - perfect for development where you want to edit code on your host and see changes in the container.

## Bind Mount vs Named Volume vs Anonymous Volume

| Type                 | Syntax                         | Use Case                   | Persistence                  |
| -------------------- | ------------------------------ | -------------------------- | ---------------------------- |
| **Bind Mount**       | `./local/path:/container/path` | Development, config files  | On host filesystem           |
| **Named Volume**     | `volume_name:/container/path`  | Production data, databases | Docker-managed               |
| **Anonymous Volume** | `/container/path`              | Temporary/cache data       | Docker-managed, auto-deleted |

## Bind Mount Examples

```yaml
services:
  backend:
    volumes:
      # Development: Edit code on host, run in container
      - ./my_custom_app:/home/frappe/frappe-bench/apps/my_custom_app

      # Configuration: Override container config with host file
      - ./custom-config.json:/home/frappe/frappe-bench/sites/common_site_config.json:ro # :ro = read-only

      # Logs: Access container logs on host for debugging
      - ./logs:/home/frappe/frappe-bench/logs

      # Database (not recommended for production)
      - ./data/mysql:/var/lib/mysql

  # Named volume for production database
  db:
    volumes:
      - db_data:/var/lib/mysql # Managed by Docker, survives container deletion

volumes:
  db_data: # Define named volume
```

## Performance Optimization (macOS/Windows)

Docker on macOS/Windows uses a VM, making bind mounts slower. Use these flags:

```yaml
volumes:
  # :cached - Host writes are buffered (good for general development)
  - ./development:/home/frappe/frappe-bench:cached

  # :delegated - Container writes are buffered (best when container writes heavily)
  - ./development:/home/frappe/frappe-bench:delegated

  # :consistent - Full synchronization (slowest but safest)
  - ./development:/home/frappe/frappe-bench:consistent
```

**Recommendation:** Use `:cached` for most development work on macOS/Windows.
