---
title: Build Cache
---

# Build cache

This page describes cache inputs and invalidation rules for `images/layered/Containerfile`, `images/custom/Containerfile`, and the reusable app image workflow. For refresh strategy selection and build commands, see [Control application-source refreshes in CI builds](../11-how-to/06-control-source-refreshes-in-ci-builds.md). The [build setup guide](../02-setup/02-build-setup.md#build-args-secrets-and-flags) lists the other build arguments and secrets.

## Cache invalidation

Both Containerfiles mount `apps.json` as the `apps_json` build secret during `bench init`. [Docker excludes secret contents from cache keys](https://docs.docker.com/build/cache/invalidation/#build-secrets), so editing the file does not invalidate the cached application build step.

`CACHE_BUST` is a build argument, defaults to an empty string, and accepts an arbitrary string. The Containerfiles consume it in the same `RUN` instruction as `bench init`. Changing its value invalidates that step while earlier dependency layers remain eligible for reuse. The value is not interpreted as a timestamp, run ID, commit SHA, or hash; those are values computed by the caller's CI configuration.

| Change                                                   | Effect on the cached application build step                                                                         |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Change `CACHE_BUST`                                      | Invalidates the `bench init` step.                                                                                  |
| Change `FRAPPE_BRANCH` or `FRAPPE_PATH`                  | Can invalidate the step because both arguments are used during bench initialization.                                |
| Change an earlier layer or the builder image digest      | Invalidates dependent layers. A moving builder image tag matters once the builder resolves its updated digest.      |
| Change `apps.json` secret contents                       | Does not invalidate the step.                                                                                       |
| Push commits to an unchanged remote Frappe or app branch | Does not invalidate the step. Remote repository contents are not checked when reusing the cached `RUN` instruction. |
| Change the output image tag                              | Does not invalidate the step.                                                                                       |

These rules apply when a matching cache is available. `--no-cache` disables layer-cache reuse for the build.

## Cache import and export

An ephemeral CI runner needs an imported cache to reuse work from an earlier run. Exporting cache makes that work available to later builds. Neither import nor export adds secret contents or remote branch updates to cache keys.

A [GitHub Actions cache scope](https://docs.docker.com/build/cache/backends/gha/#scope) selects the cache object to import or export. It does not define when application sources should be refreshed.

## Reusable app image workflow

The repository's [app image workflow](https://github.com/frappe/frappe_docker/blob/main/.github/workflows/app-build-image.yml) imports and exports GitHub Actions cache for both its smoke-test build and its optional image push.

- Cache scope: `app-image-<app_name>-<frappe_ref>`.
- `CACHE_BUST`: not passed to either build.
- `app_ref`: used to generate the `apps.json` secret; it is not part of the cache scope.

Changing only `app_ref` or the generated `apps.json` can therefore reuse older application sources when a matching cache is available. A new output image tag does not force `bench init` to run again.
