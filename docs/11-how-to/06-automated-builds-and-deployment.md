---
title: Automated Builds and Deployment
---

# Automated Builds and Deployment

This is a brief guide to automated builds and deployment for custom Frappe images.
Depending on your specific setup, environment and security rules, the information below may need to be adapted to your needs.

## Requirements

### Knowledge

Basic knowledge of Docker and build pipelines is expected.

Please refer to the Setup chapter first, especially [Build Setup](../02-setup/02-build-setup.md), for basic understanding.

### Additional Files

#### Apps

At build time an `apps.json` file can be provided. This specifies additional Frappe framework compatible apps to include in custom images.

#### Build

A workflow file for your CI platform and environment is required.

## Build Cache

Unlike manual builds, automated build commands should generally not use `--no-cache`.

Reusing cached layers can greatly reduce build times, disk usage, and bandwidth usage when pushing to image registries.

Instead, `CACHE_BUST` can be used to control cache invalidation of the Frappe layer when rebuilding is desired.

This is especially relevant because `apps.json` is provided as a secret. Secret contents are not part of [Docker layer cache keys](https://docs.docker.com/build/cache/invalidation/#build-secrets) and therefore cannot trigger cache invalidation automatically.

As a result, Docker may reuse an older cached layer even when the custom app definition has changed.

Changing `FRAPPE_BRANCH` or using an updated builder image can also invalidate this layer. Updates to an upstream branch alone do not invalidate a cached `RUN` instruction.

### Possible techniques for cache invalidation using `CACHE_BUST`:

1. No override: normal Docker layer caching is used - not recommended in this use case
2. Timestamp: force a rebuild on every pipeline run - since the value will change every run
3. Pipeline run ID: rebuild once per CI run
4. Commit SHA: rebuild once per commit
5. apps.json hash: rebuild only when the custom app definition changes - additional requirements, see below example

### Examples:

#### 1. No override - not recommended

Docker can reuse the cached `bench init` layer while its inputs and builder image remain unchanged. Updates to an upstream app or Frappe branch alone do not force a rebuild. Frappe is fetched again when this layer is rebuilt, for example after changing `FRAPPE_BRANCH` or the builder image.

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

#### 2. Timestamp

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

#### 3. Pipeline run ID from GitHub

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

#### 4. Commit SHA from GitHub

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

#### 5. apps.json hash

Note: When using branch references in `apps.json`, the hash only changes when the file content changes, not when an upstream app branch receives updates. This method works best when pinning release tags in `apps.json`. To pick up changes to moving branches, use a timestamp or pipeline run ID instead.

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
