---
title: Asset Handling
---

# How assets are handled

Frappe's `sites` directory contains both persistent data (configuration and uploaded files) and build-time artifacts (`sites/assets`). Persisting built assets alongside site data can leave stale files after an image update, causing mismatches between asset files and their manifests.

Production images keep built assets outside the `sites` volume and link them into it at startup. Application code and assets then follow the same image lifecycle, while site data remains persistent. This is part of the [container immutability model](01-container-immutability.md).

## At build time

The [production](https://github.com/frappe/frappe_docker/blob/main/images/production/Containerfile), [custom](https://github.com/frappe/frappe_docker/blob/main/images/custom/Containerfile), and [layered](https://github.com/frappe/frappe_docker/blob/main/images/layered/Containerfile) image definitions copy assets out of `sites` and remove the original directory before declaring volumes:

```dockerfile
RUN cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets && \
  rm -rf /home/frappe/frappe-bench/sites/assets
```

Built asset files are therefore supplied by the image at `/home/frappe/frappe-bench/assets`, rather than copied into a new `sites` volume.

## At container startup

The [main entrypoint](https://github.com/frappe/frappe_docker/blob/main/resources/core/main-entrypoint.sh) removes the existing `sites/assets` path and creates a symlink to `/home/frappe/frappe-bench/assets` before executing the container command.

This happens at startup so it also works with pre-existing `sites` volumes. Mounting an existing volume over `sites` hides image contents at that path; a symlink baked into the image there would be hidden too. Replacing the path at startup repairs older volumes and ensures the link points to the image's assets.

Any previous files stored directly under `sites/assets` are removed by this entrypoint. Uploaded site files belong under the site's file directories, rather than in the generated assets directory.

At runtime, the layout is:

```text
/home/frappe/frappe-bench/
|-- assets/          # Built files from the image
|-- sites/
|   |-- assets -> /home/frappe/frappe-bench/assets
|   |-- common_site_config.json
|   `-- <site>/      # Site configuration and uploaded files
`-- logs/           # Persistence depends on the mounted volume
```

## Volume behavior

| Path                     | Storage                                                                                     | Lifecycle                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `sites/` except assets   | Mounted `sites` volume                                                                      | Retained when containers are recreated with the same volume |
| `sites/assets` symlink   | Inside the `sites` volume                                                                   | Replaced by the entrypoint at startup                       |
| `assets/` symlink target | Supplied by the image                                                                       | Matches the deployed image on container recreation          |
| `logs/`                  | A named volume when explicitly mounted, otherwise an anonymous volume declared by the image | Depends on the deployment's volume management               |

The symlink is inside persistent storage, but its target is outside that storage. Recreating containers from an updated image changes the assets they serve without replacing site data. See [Bind mounts and volumes](02-bind-mounts-and-volumes.md) for the differences between named and anonymous volumes.

## Why runtime asset builds cause problems

Running `bench build` inside a production container changes its local writable layer. Asset files and manifests can become inconsistent, and other services still use their own copies of the image's assets, potentially breaking the UI.

Recreating the affected containers from the intended image discards those local changes and restores the image's built assets. Restarting a container retains its writable layer and is insufficient. For intentional app changes, [build and deploy a new image](../02-setup/02-build-setup.md) so all application services use matching code and assets. Asset builds remain part of the normal [development workflow](../05-development/01-development.md).
