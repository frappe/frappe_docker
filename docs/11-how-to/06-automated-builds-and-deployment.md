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

Keep normal Docker caching enabled and choose one of the refresh values below for `CACHE_BUST`. Selective invalidation can reduce build time and repeated transfers while preserving reusable dependency layers. Retaining cached results also consumes local disk space.

For ephemeral runners, configure cache import and export in your CI build step so later runs can reuse earlier work.

Changing `apps.json` or updating a remote branch alone does not force a rebuild. See the [build cache reference](../12-reference/04-build-cache.md) for invalidation rules and the reusable workflow's cache behavior. The examples use `images/layered/Containerfile`; `images/custom/Containerfile` also supports `CACHE_BUST`.

Choose a refresh value according to which changes your pipeline needs to pick up. Refreshing a layer controls when sources are fetched; it does not make a moving branch reproducible. Two builds can fetch different source revisions from the same branch even with an unchanged app definition.

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

Use a changing timestamp when each build should fetch current sources, including builds of the same triggering commit.

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

Use the run ID to refresh once per workflow run while allowing builds within that run to reuse the layer. [GitHub reruns retain `GITHUB_RUN_ID`](https://docs.github.com/en/actions/reference/workflows-and-actions/variables#default-environment-variables). To refresh on a rerun as well, use `CACHE_BUST="${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"` in place of `CACHE_BUST="$GITHUB_RUN_ID"` below.

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

Use this when changes to the app definition should trigger a refresh. Pin release tags in `apps.json` and keep those tags unchanged. The hash does not detect updates to moving app or Frappe branches; use a timestamp or pipeline run ID to fetch those updates. The command requires `sha256sum` and `awk` on the runner.

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
