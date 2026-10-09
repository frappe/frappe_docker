---
title: Build App Images with GitHub Actions
---

# Build app images with GitHub Actions

Use the reusable `app-build-image.yml` workflow from a downstream repository to build and publish an app image. See [GitHub Actions image workflows](../12-reference/01-github-actions-image-workflows.md) for workflow roles, naming conventions, and inputs.

## Example: caller repository publishes to GHCR

This example assumes:

- shared base images exist in `ghcr.io/frappe/base` and `ghcr.io/frappe/build`
- the caller repository wants to publish its own app image to `ghcr.io/acme/crm`

```yaml
name: App / Build CRM Image

on:
  workflow_dispatch:
  push:
    branches:
      - develop

permissions:
  contents: read
  packages: write

jobs:
  build-image:
    uses: frappe/frappe_docker/.github/workflows/app-build-image.yml@main
    with:
      app_name: crm
      app_repo: acme/crm
      app_ref: develop
      frappe_ref: version-16
      frappe_image_prefix: ghcr.io/frappe
      image_name: ghcr.io/acme/crm
      image_tag: develop
      registry: ghcr.io
      push: true
      platforms: linux/amd64
```

What happens:

```text
1. app-build-image.yml is called
2. apps.json is generated from acme/crm + develop
3. the workflow builds images/layered/Containerfile
4. layered uses:
   - ghcr.io/frappe/build:version-16
   - ghcr.io/frappe/base:version-16
5. CRM is installed
6. the final image is pushed to ghcr.io/acme/crm:develop
```

For GHCR, the caller workflow should grant:

- `permissions: packages: write`

The reusable workflow then logs in with the workflow token.

## Example: caller repository publishes to Docker Hub

This example assumes:

- shared base images come from Docker Hub under `frappe`
- the caller repository wants to publish its app image to Docker Hub as `acme/crm`

The reusable workflow declares `contents: read` and `packages: write`, so the caller grants both permissions even when publishing to Docker Hub. See [Reusable workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations#supported-keywords-for-jobs-that-call-a-reusable-workflow).

```yaml
name: App / Build CRM Image

on:
  workflow_dispatch:
  push:
    branches:
      - develop

permissions:
  contents: read
  packages: write

jobs:
  build-image:
    uses: frappe/frappe_docker/.github/workflows/app-build-image.yml@main
    with:
      app_name: crm
      app_repo: acme/crm
      app_ref: develop
      frappe_ref: version-16
      frappe_image_prefix: frappe
      image_name: acme/crm
      image_tag: develop
      registry: docker.io
      push: true
      platforms: linux/amd64
    secrets:
      REGISTRY_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
      REGISTRY_PASSWORD: ${{ secrets.DOCKERHUB_TOKEN }}
```

In this case:

- shared images are pulled from `frappe/base:version-16` and `frappe/build:version-16`
- the final image is pushed to Docker Hub as `acme/crm:develop`
