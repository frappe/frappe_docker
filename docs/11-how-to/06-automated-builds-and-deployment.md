---
title: Automated Builds and Deployment
---

# Automated Builds and Deployment

Build custom Frappe images in CI with controlled cache refreshes, then migrate existing sites after deploying the updated image. Adapt the workflow to your CI platform, environment, and security rules.

## Requirements

- Basic knowledge of Docker and build pipelines.
- A repository checkout and a [compatible builder](../02-setup/02-build-setup.md#builder-compatibility).
- An [`apps.json` file](../02-setup/02-build-setup.md#define-custom-apps) in the repository root for the examples below.
- A workflow file for your CI platform. The examples use GitHub Actions steps and run from the repository root; the run ID and commit SHA examples use GitHub-provided environment variables.

## Build Cache

Keep normal Docker caching enabled and choose one of the refresh values below for `CACHE_BUST`. For ephemeral runners, configure cache import and export in your CI build step so later runs can reuse earlier work.

Changing `apps.json` or updating a remote branch alone does not force a rebuild. See [Build Cache Behavior](../13-explanation/09-build-cache-behavior.md) for why this happens and how to choose a refresh strategy. The examples use `images/layered/Containerfile`; `images/custom/Containerfile` also supports `CACHE_BUST`.

### 1. No override - not recommended for moving branches

Use this only when reusing cached application sources is acceptable. To fetch moving branch updates on each run, use a timestamp or pipeline run ID instead.

```yaml
- name: Build Docker image
  shell: sh
  run: |
    docker build \
      --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
      --build-arg=FRAPPE_BRANCH=version-16 \
      --secret=id=apps_json,src=apps.json \
      --tag=custom:16 \
      --file=images/layered/Containerfile .
```

### 2. Timestamp

```yaml
- name: Build Docker image
  shell: sh
  run: |
    docker build \
      --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
      --build-arg=FRAPPE_BRANCH=version-16 \
      --build-arg=CACHE_BUST="$(date +%s)" \
      --secret=id=apps_json,src=apps.json \
      --tag=custom:16 \
      --file=images/layered/Containerfile .
```

### 3. Pipeline run ID from GitHub

To refresh on a workflow rerun as well, use `CACHE_BUST="${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"` in place of `CACHE_BUST="$GITHUB_RUN_ID"` below.

```yaml
- name: Build Docker image
  shell: sh
  run: |
    docker build \
      --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
      --build-arg=FRAPPE_BRANCH=version-16 \
      --build-arg=CACHE_BUST="$GITHUB_RUN_ID" \
      --secret=id=apps_json,src=apps.json \
      --tag=custom:16 \
      --file=images/layered/Containerfile .
```

### 4. Commit SHA from GitHub

Use this when the triggering commit should determine the refresh. Rebuilding that commit will not pick up independent updates to remote app or Frappe branches.

```yaml
- name: Build Docker image
  shell: sh
  run: |
    docker build \
      --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
      --build-arg=FRAPPE_BRANCH=version-16 \
      --build-arg=CACHE_BUST="$GITHUB_SHA" \
      --secret=id=apps_json,src=apps.json \
      --tag=custom:16 \
      --file=images/layered/Containerfile .
```

### 5. apps.json hash

Pin release tags in `apps.json` for this approach. The hash does not detect updates to moving app or Frappe branches; use a timestamp or pipeline run ID to fetch those updates. The command requires `sha256sum` and `awk` on the runner.

```yaml
- name: Build Docker image
  shell: sh
  run: |
    docker build \
      --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
      --build-arg=FRAPPE_BRANCH=version-16 \
      --build-arg=CACHE_BUST="$(sha256sum apps.json | awk '{print $1}')" \
      --secret=id=apps_json,src=apps.json \
      --tag=custom:16 \
      --file=images/layered/Containerfile .
```

## Automated deployment

### Automate site migration

After updating a custom image or deploying new app versions, a database migration
must be executed using `bench migrate`.

Without running migrations, the site may become inconsistent or fail to start properly.

For automated deployments, this step should not be performed manually.

Consider using the dedicated `migrator` service provided as a Compose override.
It runs `bench --site all migrate` when the migrator container starts, after the
`configurator` completes successfully. `MIGRATE_SITES` defaults to `true`; set it
to `false` to skip migration. It also skips migration when no sites exist.

Other services do not wait for the migrator to finish. Coordinate migrations with
traffic in your deployment process and check the migrator's exit status before
considering the deployment complete.

This approach is especially useful in CI/CD pipelines where no interactive access
to the backend container is available.

See [Compose override](https://github.com/frappe/frappe_docker/blob/main/overrides/compose.migrator.yaml)
