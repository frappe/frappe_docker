---
title: Container Immutability
---

# Container immutability and persistence

Production Frappe deployments use an immutable application layer. Application source, Python and Node dependencies, and built assets are supplied by the image and must not be modified at runtime. Site data and deployment configuration have a separate lifecycle in persistent storage.

## The application layer

The base [Compose configuration](https://github.com/frappe/frappe_docker/blob/main/compose.yaml) uses the same image for the backend, frontend, websocket, workers, scheduler, and configurator. It mounts the `sites` volume into these services, but does not mount application source over the image's `apps` directory.

Changes to application code, dependencies, or assets require building a replacement image and recreating the application services with that image. Do not fetch or edit code, install packages, or rebuild assets inside production containers. Runtime changes do not update the image and can leave services running different application contents.

Environment settings and the site configuration written by the configurator configure that application; they do not change its code. Keeping all application services on the same image makes the deployed version reproducible.

## What persists

The shared `sites` volume is mounted at `/home/frappe/frappe-bench/sites`. It holds `common_site_config.json`, each site's configuration, and uploaded files. The configurator writes connection settings there and regenerates `sites/apps.txt` from the apps included in the image. This file is an inventory of available app code, not storage for that code.

Site database contents live separately: the MariaDB and PostgreSQL overrides mount `db-data` into their database containers. The Redis override mounts `redis-queue-data` for the queue service; it does not configure a named volume for the cache service. These mounts preserve stored files independently of application container replacement; they are not a substitute for [backups](../03-production/02-backup-strategy.md).

Built assets are not persistent site content. The images store them at `/home/frappe/frappe-bench/assets`, outside the `sites` mount. At startup, the entrypoint replaces `sites/assets` with a symlink to that image-supplied directory. Keeping the same `sites` volume therefore preserves site data while newly deployed images supply matching code and assets. See [How assets are handled](03-asset-handling.md).

Recreating containers with the same storage retains their data. Removing volumes or selecting different storage can lose or detach it. Log storage is separate from `sites`: the images declare `/home/frappe/frappe-bench/logs` as a volume, but the base Compose file does not give it a shared named mount. See [Bind mounts and volumes](02-bind-mounts-and-volumes.md) for how the repository's storage choices affect persistence.

## Apps in production and development

There are two distinct app states: the code available in the image and the apps installed on an individual site. The default ERPNext image supplies Frappe and ERPNext; the custom and layered image builds can include additional apps through `apps.json`. Every application service needs the image containing the code its sites use. See the [image build guide](../02-setup/02-build-setup.md#define-custom-apps).

Installing an app already included in the image onto a site initializes that site's app data and schema. Creating a site with `--install-app`, or migrating a site using the deployed code, changes site state without changing the immutable application layer. Image replacement preserves existing site state; it does not automatically install every available app on every site. See [Site operations](../04-operations/01-site-operations.md).

Adding or updating app code in production belongs to the image build and redeployment process. Commands such as `bench get-app`, `bench update`, package installation, and `bench build` must not be used to change the running production application layer.

The [development setup](../05-development/01-development.md) uses the Bench image and bind-mounts the repository at `/workspace`, with benches under `/workspace/development`. Developers edit source, fetch apps, install dependencies, and build assets in that working tree. This editable environment is for development; production consumes the resulting application through a built image.
