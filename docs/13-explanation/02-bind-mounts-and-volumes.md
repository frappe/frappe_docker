---
title: Bind Mounts and Volumes
---

# Bind mounts and volumes

Bind mounts connect a host directory or file to a path inside a container. Changes are visible in both places, making them useful for editing source code during development. Volumes also store data outside a container's writable layer, but Docker manages their names and lifecycle.

Frappe production deployments separate image contents from persistent site and database data. See [Container immutability and persistence](01-container-immutability.md) for why this matters.

## Storage choices

| Type                      | Compose mount syntax                             | Typical use                                                               | Persistence                                                                                                    |
| ------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Bind mount                | `./local/path:/container/path`                   | Editable source or host configuration                                     | Files remain on the host when containers are removed                                                           |
| Named volume              | `volume_name:/container/path`                    | Site data and databases                                                   | Retained independently of containers; `docker compose down -v` removes project-managed volumes and their data  |
| Named bind-mounted volume | `volume_name:/container/path` with `driver_opts` | Data on a chosen host filesystem, such as an NFS/SAN/ZFS-backed directory | Removing the volume definition leaves the underlying host directory's files                                    |
| Anonymous volume          | `/container/path`                                | Storage without a stable, explicit volume name                            | Not automatically deleted with every container removal; cleanup and reuse depend on how containers are managed |

Anonymous volumes persist unless explicitly removed, for example by `docker compose down -v` or when an associated `docker run --rm` container exits. They are not automatically reused by a subsequent `docker compose up` after `down`. Named volumes make storage easier to identify and reuse. External volumes are not removed by `docker compose down -v`.

**Removing Docker-managed volumes can delete site or database data.** Persistence is not a backup; see [Backup strategy](../03-production/02-backup-strategy.md).

## How mounts appear in Compose

These excerpts illustrate mount types, rather than a complete deployment. App source mounts are for development; production apps belong in the image. A read-only configuration mount also prevents Frappe or the configurator from updating that file.

```yaml
services:
  backend:
    volumes:
      # Development: edit source on the host
      - ./my_custom_app:/home/frappe/frappe-bench/apps/my_custom_app
      # Configuration: :ro means read-only
      - ./custom-config.json:/home/frappe/frappe-bench/sites/common_site_config.json:ro
      # Logs accessible from the host
      - ./logs:/home/frappe/frappe-bench/logs

  db:
    volumes:
      # Docker-managed database storage
      - db_data:/var/lib/mysql

  db_bind_mounted:
    volumes:
      # Alternative: database storage in a chosen host directory
      - db_data_bind_mounted:/var/lib/mysql

volumes:
  db_data:
  db_data_bind_mounted:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/db # Absolute host path; must already exist
```

A direct database bind mount such as `./data/mysql:/var/lib/mysql` also puts files on the host. Docker-managed named volumes are the usual choice; selecting host storage requires managing its paths, permissions, and backups yourself.

This repository supplies named bind-mounted volume overrides for sites, database data, and the Redis queue. They retain the volume names used by the services while changing the storage location. The [Compose overrides reference](../02-setup/05-overrides.md) lists the files and required environment variables. Host directories must exist and be writable by the container user.

## Bind mounts on macOS and Windows

Docker Desktop runs Linux containers in a VM, so access to host files crosses that boundary. Bind mount performance depends on the host and file-sharing implementation.

Compose supports consistency options where the platform implements them:

```yaml
volumes:
  - ./development:/home/frappe/frappe-bench:cached
  - ./development:/home/frappe/frappe-bench:delegated
  - ./development:/home/frappe/frappe-bench:consistent
```

These are alternatives for the same mount: `cached` favors the host's view, `delegated` favors the container's view, and `consistent` requests a consistent view. They are platform-dependent and are not a universal performance fix for macOS or Windows. See Docker's [Compose volume options](https://docs.docker.com/reference/compose-file/services/#volumes), [bind mount documentation](https://docs.docker.com/engine/storage/bind-mounts/), and [volume lifecycle documentation](https://docs.docker.com/engine/storage/volumes/) for details.
