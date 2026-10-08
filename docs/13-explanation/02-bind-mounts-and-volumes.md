---
title: Bind Mounts and Volumes
---

# Bind mounts and volumes

Frappe Docker uses mounts for production data and editable development files. Docker's [volumes](https://docs.docker.com/engine/storage/volumes/) and [bind mounts](https://docs.docker.com/engine/storage/bind-mounts/) documentation explains their general behavior and lifecycle.

## Production storage

The base `compose.yaml` shares the named `sites` volume between application services. Database overrides add `db-data`, and the Redis override adds `redis-queue-data` for the queue. These hold deployment state independently of the application image. See [What persists](01-container-immutability.md#what-persists) for the boundary between this state and immutable application contents.

By default, Docker manages these named volumes. The `compose.bind-mount-sites.yaml`, `compose.bind-mount-db-data.yaml`, and `compose.bind-mount-redis-queue.yaml` overrides retain the same volume names but use the local driver's bind options to place their contents in host directories. This changes where data is stored without changing the services' mount paths.

Choose those overrides when you need to manage data at a particular host location. Their directories must already exist and be writable by the corresponding container user. The [Compose overrides reference](../02-setup/05-overrides.md) lists the required location variables and compatible database and Redis overrides.

The production images also declare a volume for `/home/frappe/frappe-bench/logs`. Without an explicit mount, Docker creates an anonymous volume for it. The base Compose file does not configure shared named log storage; `pwd.yml`, the disposable demo, explicitly mounts a named `logs` volume.

Retaining the same mounts preserves their contents when containers are replaced. **`docker compose down -v` removes project-managed named volumes and anonymous volumes attached to the containers, and can delete their data.** With the bind-backed overrides, removing the Docker volume leaves the underlying host directory's files. See Docker's [Compose removal behavior](https://docs.docker.com/reference/cli/docker/compose/down/) and the [backup guide](../11-how-to/04-create-backups.md).

## Development source

The development Compose example bind-mounts the repository at `/workspace` and works in `/workspace/development`. A bench created there is accessible from the host, so source edits survive replacement of the development container.

This source mount supports an editable development environment. Production Compose mounts site data and uses application code and built assets from the image; a source bind mount must not be used to modify the production application layer. See the [development setup](../05-development/01-development.md) for its configuration.
