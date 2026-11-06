---
title: Automate Site Migrations
---

# Automate site migrations

Run site migration as a required CI/CD stage when deploying updated Frappe or app versions. Migration changes the existing sites' database schema and app state.

## Requirements

- An existing Compose deployment with sites to migrate and its database and Redis services available.
- The target image available to the deployment runner, including all apps installed on those sites. Select that image in your deployment environment file using `CUSTOM_IMAGE` and `CUSTOM_TAG`, or `ERPNEXT_VERSION` for the default image.
- The existing deployment's project name, environment file, and complete Compose file list. Keep the same sites volume and database connections.

## Match the deployment configuration

Run the following commands from the repository root. Replace the placeholders with your existing deployment settings. The examples use one deployment Compose file; if you normally combine several files, retain every `-f` argument in its usual order and append `-f overrides/compose.migrator.yaml`.

If the backend uses custom networks, attach the migrator to the same database and Redis networks in an additional override. For a deployment using `compose.multi-bench.yaml`, save this as `compose.migrator-networks.yaml`:

```yaml
services:
  migrator:
    networks:
      - bench-network
      - mariadb-network
```

Append `-f compose.migrator-networks.yaml` after the migrator override in both commands below. For other custom network layouts, use the network names from your deployment. Check the merged configuration with `docker compose` and the same arguments followed by `config`; verify the migrator's target image, sites volume, and database and Redis networks.

## Prepare the deployment

Before running migration, [back up the sites](04-create-backups.md) and pause traffic and background processing using your deployment's maintenance procedure. Keep the database and Redis services available.

Pull the target images for the configurator and migrator. Configure the CI stage to fail if this command fails.

```sh
docker compose \
  --project-name "<existing-project>" \
  --env-file "<deployment-env-file>" \
  -f "<deployment-compose-file>" \
  -f overrides/compose.migrator.yaml \
  pull configurator migrator
```

## Run the migration stage

Run the migrator as a one-off container and wait for it to finish:

```sh
docker compose \
  --project-name "<existing-project>" \
  --env-file "<deployment-env-file>" \
  -f "<deployment-compose-file>" \
  -f overrides/compose.migrator.yaml \
  run --rm -T -e MIGRATE_SITES=true migrator
```

Configure the CI stage to fail on a nonzero exit status and block subsequent deployment stages. Check the output for `[migrator] Migrating all sites` and successful migration of the intended sites. If it reports no sites when you expect existing sites, fail the deployment check and verify the project name and sites volume before continuing.

## Complete deployment after migration succeeds

Start or recreate the application services with your normal deployment command, using the same target image. Include the migrator override only in the migration stage's commands so a later `up` does not start another migration container.

Resume traffic and background processing after migration and your deployment checks succeed. Keep this ordering explicit in the pipeline; adding the override alone does not make other application services wait for migration.

For defaults, skip conditions, and startup and restart behavior, see the [site migration service reference](../12-reference/05-site-migration-service.md).
