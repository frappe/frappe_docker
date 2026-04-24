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

Assets are moved out of the `sites` volume during the Docker build and replaced with a **symlink**. This means assets always come from the image layer, while the rest of `sites` remains persistent.

### How it works

During the image build (`Containerfile`), the following is done:

```dockerfile
RUN cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets && \
    rm -rf /home/frappe/frappe-bench/sites/assets && \
    ln -s /home/frappe/frappe-bench/assets /home/frappe/frappe-bench/sites/assets
```

This runs **before** the `VOLUME` declaration, so the symlink is baked into
the image layer.

At runtime:

```
/home/frappe/frappe-bench/
├── assets/          ← image layer (ephemeral, always matches the image)
├── sites/
│   ├── assets -> /home/frappe/frappe-bench/assets   ← symlink
│   ├── common_site_config.json                       ← persisted in volume
│   └── <site>/                                       ← persisted in volume
└── logs/            ← persisted in volume
```

### Volume behavior

| Path                       | Persistent              | Source                 |
| -------------------------- | ----------------------- | ---------------------- |
| `sites/` (except assets)   | ✅ Yes                  | Named volume           |
| `sites/assets` (symlink)   | ✅ Yes (symlink itself) | Named volume (`sites`) |
| `assets/` (symlink target) | ❌ No                   | Image layer            |
| `logs/`                    | ✅ Yes                  | Unnamed volume         |

The symlink itself is persisted in the volume, but it always points to
`assets/` which lives in the image layer and is discarded on container
recreation.

## Important: `bench build` at runtime

Running `bench build` inside a running container will write new assets and eventually cause a mismatch between `assets.json` and the actual assets, breaking the UI. This can be recovered by recreating the containers

> Note: restarting the containers is not sufficient — they need to be recreated to discard the writable layer.
