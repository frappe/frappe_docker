---
title: Container Immutability
---

# Container immutability and persistence

Production Frappe deployments keep application code and built assets in the Docker image, while site data and database storage live outside the container's writable layer. This separates the application version from the data it serves.

## Images and containers

An image supplies the application code, dependencies, and assets. A container adds a writable layer, so it is technically possible to modify files inside it. Those changes do not update the image and are lost when the container is removed and recreated.

Treat production application code as immutable: change the image through a build and redeploy it, rather than changing code inside a running container. Environment variables and mounted configuration or data can vary between deployments without rebuilding the application.

This makes deployments reproducible: backend, frontend, workers, and websocket services can use the same application version from the same image.

## What persists

In the base [Compose configuration](https://github.com/frappe/frappe_docker/blob/main/compose.yaml), the `sites` volume is mounted at `/home/frappe/frappe-bench/sites`. It contains shared and site-specific configuration, uploaded files, and other site data. Database overrides provide separate database storage. Log persistence depends on the chosen mounts; the demo, for example, uses a named `logs` volume.

Built assets are an exception within `sites`: `sites/assets` links to files supplied by the image. See [How assets are handled](03-asset-handling.md) for the build and startup behavior.

Persistent storage allows sites to be created, migrated, backed up, and restored independently of container replacement. Recreating containers with the same mounts retains their data; deleting volumes can delete that data. See [Bind mounts and volumes](02-bind-mounts-and-volumes.md) for storage lifecycles and [Site operations](../04-operations/01-site-operations.md) for the procedures.

## Apps in production and development

Fetching app code with `bench get-app` or rebuilding assets with `bench build` inside a production container is unsupported: code and assets belong to the image, and runtime changes can disappear or leave services inconsistent.

Include additional apps in the image build configuration, build the image, and redeploy the stack with it. The [image build guide](../02-setup/02-build-setup.md#define-custom-apps) describes `apps.json` and deployment settings.

Installing an app already included in the image onto a site is a separate operation: it updates that site's database and configuration. See [Site operations](../04-operations/01-site-operations.md#setup-new-site).

The [development environment](../05-development/01-development.md) deliberately supports editable source code and asset rebuilding. Its bind-mounted working tree serves a different purpose from an immutable production image.
