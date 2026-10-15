---
title: App Build Workflow
---

# App build workflow

The reusable [app-build-image.yml](https://github.com/frappe/frappe_docker/blob/main/.github/workflows/app-build-image.yml) workflow builds an app image from existing shared `base` and `build` images.

For caller instructions, see [Build app images with GitHub Actions](../11-how-to/09-build-app-images-with-github-actions.md). For the relationships between core and downstream workflows, see [Image build and release pipeline](../13-explanation/07-github-actions-image-workflows.md).

## Inputs

Required inputs have no default. All inputs are strings except `push`, which is a boolean.

| Input                 | Required | Default                            | Meaning                                                                                                                       |
| --------------------- | -------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `app_name`            | Yes      | —                                  | App directory name used by the image contents check, for example `crm`.                                                       |
| `app_repo`            | Yes      | —                                  | Git URL or GitHub `owner/repo` slug of the app to include.                                                                    |
| `app_ref`             | Yes      | —                                  | App branch or tag. The workflow strips a leading `refs/heads/` or `refs/tags/` prefix.                                        |
| `frappe_ref`          | Yes      | —                                  | Shared `base` and `build` image tag, for example `version-16`. Also passed as the Frappe Git ref during bench initialization. |
| `frappe_image_prefix` | No       | `frappe`                           | Source prefix for shared images, for example `frappe` or `ghcr.io/frappe`.                                                    |
| `image_name`          | Yes      | —                                  | Destination image name, including its registry and namespace where applicable, for example `ghcr.io/acme/crm`.                |
| `image_tag`           | Yes      | —                                  | Destination image tag, for example `develop` or `v16.0.0`.                                                                    |
| `push`                | Yes      | —                                  | Whether to publish the final image after the smoke test.                                                                      |
| `registry`            | No       | `docker.io`                        | Registry host used for publishing authentication. Does not change `image_name`.                                               |
| `frappe_repo`         | No       | `https://github.com/frappe/frappe` | Frappe Git repository used during bench initialization.                                                                       |
| `builder_repository`  | No       | `frappe/frappe_docker`             | GitHub repository containing the Containerfile and helper scripts.                                                            |
| `builder_ref`         | No       | `main`                             | Git ref checked out from `builder_repository`.                                                                                |
| `platforms`           | No       | `linux/amd64`                      | Comma-separated target platforms for the published image.                                                                     |

`frappe_image_prefix` selects the source images; `image_name` and `image_tag` select the final image destination. `registry` must match that destination's registry for authentication.

## Secrets and permissions

The workflow declares `contents: read` and `packages: write`. The caller must allow both permissions, including when publishing to Docker Hub, because a reusable workflow cannot elevate its caller's permissions.

| Registry         | Authentication when `push` is `true`                                            |
| ---------------- | ------------------------------------------------------------------------------- |
| `ghcr.io`        | The caller's `github.actor` and `github.token`; no registry secrets are needed. |
| Other registries | The caller supplies the `REGISTRY_USERNAME` and `REGISTRY_PASSWORD` secrets.    |

With `push: false`, the workflow skips registry login and publishing.

## Build and smoke-test behavior

The workflow generates an `apps.json` file containing `app_repo` and `app_ref`, then builds `images/layered/Containerfile` from the selected builder repository. The smoke-test image is always built for `linux/amd64`. Its contents check requires both `apps/frappe` and `apps/<app_name>` to exist in the bench.

When `push` is `true`, the workflow publishes `image_name:image_tag` for the requested `platforms` after the smoke test succeeds. The `platforms` input does not change the smoke-test architecture.
