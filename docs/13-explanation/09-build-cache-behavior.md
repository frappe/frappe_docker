---
title: Build Cache Behavior
---

# Build Cache Behavior

Automated image builds balance reusing expensive work against fetching current application sources. A successful cached build can still contain older app code: cache reuse establishes that the build inputs match, not that remote repositories have stayed unchanged.

For commands that control app-layer refreshes and automate site migration, see [Automated Builds and Deployment](../11-how-to/06-automated-builds-and-deployment.md). The [build setup guide](../02-setup/02-build-setup.md#build-args-secrets-and-flags) describes the build arguments and secret interface.

## Cache invalidation

Both `images/layered/Containerfile` and `images/custom/Containerfile` mount `apps.json` as the `apps_json` build secret during `bench init`. [Docker excludes secret contents from cache keys](https://docs.docker.com/build/cache/invalidation/#build-secrets), so editing the file can leave the cached application layer reusable. Likewise, a new commit on a remote Frappe or app branch does not change the cached `RUN` instruction.

The Containerfiles consume `CACHE_BUST` in the same `RUN` instruction as `bench init`. Changing that argument invalidates the application build step while allowing earlier dependency layers to remain cached. Changes to `FRAPPE_BRANCH`, `FRAPPE_PATH`, or an earlier layer can also invalidate the step. In the layered build, a different builder image digest changes its parent layer; an upstream image tag moving only matters once the builder resolves the updated image.

Broadly disabling cache with `--no-cache` repeats work that may have no connection to an app update. Selective invalidation retains the benefits of reusing dependency layers and can reduce build time and repeated transfers. It does not guarantee lower local disk use: retaining more cached results also consumes storage.

## What a refresh value represents

The choice of `CACHE_BUST` defines which changes the pipeline treats as a reason to fetch sources again:

- **No override:** normal layer caching can reuse application sources until another input invalidates the step. This is unsuitable when every build is expected to fetch changes from moving branches.
- **Timestamp:** a changing value refreshes sources on each invocation, including rebuilds of the same commit.
- **Pipeline run ID:** separate runs refresh sources, while builds within one run can reuse the application layer. In [GitHub's run variables](https://docs.github.com/en/actions/reference/workflows-and-actions/variables#default-environment-variables), reruns retain `GITHUB_RUN_ID`; `GITHUB_RUN_ATTEMPT` distinguishes those attempts.
- **Commit SHA:** builds of the same triggering commit can reuse the layer. A new commit in an independently maintained app or Frappe repository does not change that triggering SHA.
- **`apps.json` hash:** changes to the app definition trigger a refresh, but updates to branches named in the file do not. This fits versioned app definitions that pin release tags, assuming those tags remain unchanged. An unchanged hash also does not detect updates to a moving `FRAPPE_BRANCH`.

Refreshing a layer controls when remote sources are fetched; it does not make a moving branch reproducible. If two builds fetch the same branch at different times, their contents can differ even with the same app definition. The [cache recipes](../11-how-to/06-automated-builds-and-deployment.md#build-cache) show how to pass each refresh value.

## Cache storage and cache freshness

Cache availability is separate from invalidation. An ephemeral CI runner needs an imported cache to reuse work from an earlier run. Exporting cache makes that work available later; it does not cause changed secret contents or remote branch updates to participate in cache keys.

The repository's [reusable app image workflow](https://github.com/frappe/frappe_docker/blob/main/.github/workflows/app-build-image.yml) imports and exports GitHub Actions cache for both its smoke-test build and its optional image push. Its scope is `app-image-<app_name>-<frappe_ref>` and it does not pass `CACHE_BUST`. Consequently, changing only `app_ref` or the generated `apps.json` can reuse older application sources when a matching cache is available. A new output image tag does not force `bench init` to run again.

A [GitHub Actions cache scope](https://docs.docker.com/build/cache/backends/gha/#scope) selects the cache object to import or export. It is not a source revision or an application-layer refresh policy. These are separate choices: where to store reusable work, and when that work is still suitable for the image being built.
