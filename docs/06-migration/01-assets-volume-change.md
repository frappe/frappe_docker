---
title: Assets Volume Change
---

# Migration Guide: Assets Volume Change

## Background

The way `sites/assets` is handled has changed. Previously, assets were stored inside the a volume and persisted across container recreations. This could caused stale or mismatched assets after image updates. See [Assets Reference](../08-reference/07-how-assets-are-handeled.md) for details on the new approach.

## Who needs to migrate?

Anyone running an existing setup where the `sites` volume was created with **`frappe_docker` version `v3.1.0` or lower**.

**New setups are unaffected.**

## Migration Steps

1. **Pull an updated Image**

2. **Recreate all containers (`docker compose up --force-recreate`)**

3. **Enter the backend container**

   ```bash
   docker compose -p frappe exec -it backend bash
   ```

4. **Run commands in container**
   ```bash
   rm -rf /home/frappe/frappe-bench/sites/assets && \
   ln -s /home/frappe/frappe-bench/assets /home/frappe/frappe-bench/sites/assets && \
   exit
   ```

## What this does

Replaces `sites/assets` directory with a symlink pointing to `/home/frappe/frappe-bench/assets`, which lives in the image layer. This ensures assets always match the running image version.

After this manual migration is made once no further steps are needed on further deployments.
