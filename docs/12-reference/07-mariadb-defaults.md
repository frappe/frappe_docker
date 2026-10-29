---
title: MariaDB Defaults
---

# MariaDB defaults

The bundled MariaDB 11.8 configurations explicitly set `innodb_snapshot_isolation=OFF`:

- `overrides/compose.mariadb.yaml`
- `overrides/compose.mariadb-shared.yaml`
- `pwd.yml`
- `devcontainer-example/docker-compose.yml`
- The [ARM64 example](../01-getting-started/03-arm64.md)

MariaDB 11.8 enables this setting by default. Disabling it restores the earlier conflict-handling behavior as a compatibility workaround for Frappe concurrency errors, including Contact background jobs that fail with error 1020. This follows the defaults used by [Frappe Press](https://github.com/frappe/press/pull/6877) and [Pilot](https://github.com/frappe/pilot/commit/d7a363ef1e9e09b26e4685b2fea4379bd922dbb6).

Transactions and row locking remain enabled, but the additional snapshot write-conflict protection is disabled. This setting does not resolve the underlying application races. See [issue #2043](https://github.com/frappe/frappe_docker/issues/2043).

For existing deployments, regenerate any rendered Compose configuration and recreate the database container to apply the changed startup command. Recreating the container interrupts database connections; retain the existing database volume. External database servers are unaffected by these Compose defaults.
