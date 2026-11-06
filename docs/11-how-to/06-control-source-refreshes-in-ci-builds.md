---
title: Control Source Refreshes in CI Builds
---

# Control application-source refreshes in CI builds

Configure your CI build step to fetch Frappe and app sources when your pipeline needs them, while allowing Docker to reuse cached dependency layers.

## Requirements

- Basic knowledge of Docker and build pipelines.
- A repository checkout and a [compatible builder](../02-setup/02-build-setup.md#builder-compatibility).
- An [`apps.json` file](../02-setup/02-build-setup.md#define-custom-apps) in the repository root.
- A workflow file for your CI platform. The examples use GitHub Actions steps and run from the repository root; the run ID and commit SHA examples use GitHub-provided environment variables.

## Choose and apply one refresh policy

Choose one recipe below and use it as your pipeline's build step. Keep Docker caching enabled by omitting `--no-cache`. For ephemeral runners, configure [cache import and export](../12-reference/04-build-cache.md#cache-import-and-export) in your CI build configuration to reuse cache between runs.

For moving Frappe or app branches, choose a timestamp or pipeline run ID when you need to fetch current sources. An unchanged app definition or triggering commit does not guarantee unchanged remote sources. See the [build cache reference](../12-reference/04-build-cache.md#cache-invalidation) for the invalidation rules.

The recipes use `images/layered/Containerfile`; use `--file=images/custom/Containerfile` instead if you build with the custom Containerfile.

### No override - not recommended for moving branches

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

### Timestamp

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

### Pipeline run ID from GitHub

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

### Commit SHA from GitHub

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

### apps.json hash

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
