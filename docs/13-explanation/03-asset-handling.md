---
title: Asset Handling
---

# How assets are handled

Frappe's `sites` directory contains both persistent data (configuration and uploaded files) and build-time artifacts (`sites/assets`). Persisting built assets alongside site data can leave stale files after an image update, causing mismatches between asset files and their manifests.

Production images keep built assets outside the `sites` volume and link them into it at startup. Application code and assets then follow the same image lifecycle, while site data remains persistent. This is part of the [container immutability model](01-container-immutability.md).

## At build time

To keep built assets tied to the deployed image, the [production](https://github.com/frappe/frappe_docker/blob/main/images/production/Containerfile), [custom](https://github.com/frappe/frappe_docker/blob/main/images/custom/Containerfile), and [layered](https://github.com/frappe/frappe_docker/blob/main/images/layered/Containerfile) image definitions copy the asset tree out of `sites` and remove the original directory before declaring volumes:

```dockerfile
RUN cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets && \
  rm -rf /home/frappe/frappe-bench/sites/assets
```

The final image supplies the asset tree at `/home/frappe/frappe-bench/assets`, outside the persistent `sites` volume.

This tree contains asset manifests such as `assets.json` and per-app symlinks. By default, [Frappe's asset builder](https://github.com/frappe/frappe/blob/version-16/frappe/build.py) links `sites/assets/frappe` to `/home/frappe/frappe-bench/apps/frappe/frappe/public`, and similarly for other apps with a `public` directory. The recursive copy preserves these links under `assets/`. The app's public directory, including its built `dist/` bundles, is also supplied by the image. These per-app links are separate from the `sites/assets` link created at container startup.

## At container startup

During container startup, the [main entrypoint](https://github.com/frappe/frappe_docker/blob/main/resources/core/main-entrypoint.sh) removes the existing `sites/assets` path, then creates a symlink from `/home/frappe/frappe-bench/sites/assets` to `/home/frappe/frappe-bench/assets` before executing the container command. A directory at `sites/assets` is removed with its contents; an existing symlink is unlinked without removing its target.

This happens at startup so it also works with pre-existing `sites` volumes. Mounting an existing volume over `sites` hides image contents at that path; a `sites/assets -> /home/frappe/frappe-bench/assets` symlink baked into the image would be hidden too. The per-app links inside this asset tree, such as `assets/frappe` pointing to the app's `public` directory, are a separate relationship. Replacing the path at startup repairs older volumes and ensures the link points to the image's assets.

If `sites/assets` is a directory, the entrypoint removes it and its contents. If it is already a symlink, only the link is removed; its target and the per-app links inside that target are left untouched. Uploaded site files belong under the site's file directories, rather than in the generated assets directory.

At runtime, the layout is as follows, with Frappe shown as an example of the per-app links:

```text
/home/frappe/frappe-bench/
|-- assets/              # Asset tree supplied by the image
|-- sites/               # Persistent sites volume
|   |-- assets -> /home/frappe/frappe-bench/assets  # Link in volume; replaced at startup
|   |-- common_site_config.json
|   `-- <site>/           # Site configuration and uploaded files
`-- logs/                # Persistence depends on the mounted volume
```

## Volume behavior

| Path                     | Storage                                                                                     | Lifecycle                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `sites/`                 | Mounted `sites` volume                                                                      | Retained when containers are recreated with the same volume |
| `sites/assets` symlink   | Inside the `sites` volume                                                                   | Replaced by the entrypoint at startup                       |
| `assets/` symlink target | Supplied by the image                                                                       | Matches the deployed image on container recreation          |
| `logs/`                  | A named volume when explicitly mounted, otherwise an anonymous volume declared by the image | Depends on the deployment's volume management               |

Deploying an updated image by recreating the application containers has two results: the containers use the assets built into that image, and manual changes made to assets through `sites/assets` in the old containers are discarded. Site configuration and uploaded files remain in the reused `sites` volume. Building an image alone leaves running containers unchanged, and restarting the same container retains its local asset changes. See [Bind mounts and volumes](02-bind-mounts-and-volumes.md) for the repository's storage choices.

## Why runtime asset builds cause problems

Built assets are part of the immutable production application layer and must not be rebuilt at runtime. Running `bench build` inside a production container changes its local writable layer. Asset files and manifests can become inconsistent, and other services still use their own copies of the image's assets, potentially breaking the UI.

Recreating the affected containers from the intended image discards those local changes and restores the image's built assets. Restarting a container retains its writable layer and is insufficient. For intentional app changes, [build and deploy a new image](../02-setup/02-build-setup.md) so all application services use matching code and assets. Asset builds remain part of the normal [development workflow](../05-development/01-development.md).
