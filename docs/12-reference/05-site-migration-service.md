---
title: Site Migration Service
---

# Site migration service

The [`compose.migrator.yaml` override](https://github.com/frappe/frappe_docker/blob/main/overrides/compose.migrator.yaml) adds a `migrator` service to the deployment's Compose configuration. For pipeline setup and commands, see [Automate site migrations](../11-how-to/11-automate-site-migrations.md).

## Service configuration

| Setting            | Value                                                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------------------- |
| Service name       | `migrator`                                                                                            |
| Image              | `${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-$ERPNEXT_VERSION}`, matching the base Compose services |
| Platform           | `linux/amd64`                                                                                         |
| Sites volume       | `sites:/home/frappe/frappe-bench/sites`                                                               |
| Startup dependency | `configurator` with `condition: service_completed_successfully`                                       |
| Entrypoint         | `bash -c`                                                                                             |
| Migration command  | `bench --site all migrate`                                                                            |
| Restart policy     | `on-failure:5`                                                                                        |

The override does not declare networks for the migrator. Compose attaches it to the project's default network unless an additional override assigns networks to that service. It does not inherit networks assigned to the backend by another override.

## Migration switch

| Variable        | Default | Behavior                                                                                                            |
| --------------- | ------- | ------------------------------------------------------------------------------------------------------------------- |
| `MIGRATE_SITES` | `true`  | Migration is enabled only when the container's value is the literal string `true`. Any other value skips migration. |

The Compose expression `${MIGRATE_SITES:-true}` supplies the default when the interpolation variable is unset or empty.

## Execution and exit status

The container checks these conditions in order:

1. If `MIGRATE_SITES` is not `true`, it prints `[migrator] Migration disabled` and exits successfully.
2. If no `sites/<site>/site_config.json` files are found, it prints `[migrator] No sites found, skipping migration` and exits successfully.
3. Otherwise, it prints `[migrator] Migrating all sites` and runs `bench --site all migrate`. The container exits with that command's status.

A zero exit status can therefore mean migration succeeded or was skipped. The override adds only the configurator dependency; database and Redis readiness depend on the rest of the deployment's Compose configuration.

The `on-failure:5` policy applies when the service is started normally. A [one-off `docker compose run --rm` invocation](https://docs.docker.com/reference/cli/docker/compose/run/) overrides that restart policy and removes the container on exit.

## Deployment coordination

Other services in the base Compose file do not depend on the migrator. Starting the stack with this override does not hold application services until migration completes or automatically coordinate migration with incoming traffic.
