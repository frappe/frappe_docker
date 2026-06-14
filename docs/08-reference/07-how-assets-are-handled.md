---
title: How Assets are handled
---

# Assets Reference

## Problem

The `sites` directory contains both persistent data (site config, uploaded files, etc.) and build-time artifacts (`sites/assets`). Mounting the entire `sites` directory as a Docker volume causes assets to be persisted alongside config, which leads to:

- Stale assets surviving image updates
- Asset/manifest mismatches after rebuilds
- Assets being tied to the volume lifecycle rather than the image lifecycle

## Solution

Assets are moved out of the `sites` volume during the build process and replaced with a **symlink** later on. This means assets are always served from the image layer, while the rest of `sites` remains persistent.

### How it works

During the image build (`Containerfile`), the following is done:

```dockerfile
RUN cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets && \
  rm -rf /home/frappe/frappe-bench/sites/assets
```

This runs **before** the `VOLUME` declaration, so the **`sites` volume does not contain any assets at all**.

Additionally an `ENTRYPOINT` is added to the images which adds a **symlink** from `assets` to `site\assets`.

> This is implemented in the entrypoint instead of baking the symlink directly into the image so it also works with pre-existing or already-initialized `sites` volumes.
> Since mounting a volume over `/home/frappe/frappe-bench/sites` hides the image contents at that path, any symlink created during the image build would not be visible inside the mounted volume. The entrypoint recreates the symlink at container startup, ensuring it always exists and automatically repairing older volumes that may not already contain it.

At runtime:

```
/home/frappe/frappe-bench/
├── assets/          ← image layer (ephemeral, always matches the image)
├── sites/
│   ├── assets -> /home/frappe/frappe-bench/assets    ← symlink
│   ├── common_site_config.json                       ← persisted in volume
│   └── <site>/                                       ← persisted in volume
└── logs/            ← persisted in volume
```

### Volume behavior

| Path                       | Persistent              | Source                 |
| -------------------------- | ----------------------- | ---------------------- |
| `sites/` (except assets)   | ✅ Yes                  | Named volume (`sites`) |
| `sites/assets` (symlink)   | ✅ Yes (symlink itself) | Named volume (`sites`) |
| `assets/` (symlink target) | ❌ No                   | Image layer            |
| `logs/`                    | ✅ Yes                  | Unnamed volume         |

The `sites/assets` symlink is stored inside the persistent `sites` volume, but its target (`/home/frappe/frappe-bench/assets`) comes from the container image. When the container is recreated or upgraded, the assets directory is recreated from the new image, ensuring assets always stay in sync with the running version.

## Important: `bench build` at runtime

Running `bench build` inside a running container will write new assets and eventually cause a mismatch between `assets.json` and the actual assets, breaking the UI. This can be recovered by recreating the containers

> Note: restarting the containers is not sufficient — they need to be recreated to discard the writable layer.
