---
title: Repository Versioning
---

# Repository versioning policy

Repository releases version the deployment recipes in this repository: Compose configurations, Dockerfiles/Containerfiles, and supporting scripts and documentation. Maintainers decide repository release versions. Use `MAJOR.MINOR.PATCH` according to the effect on supported deployments:

| Release | Changes                                                                                                                                                                                                                                                        |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Major   | Incompatible deployment-facing changes that require adjustments to supported Compose configurations, persistent data or volumes, runtime permissions, or upgrade procedures. Runtime minimum increases that invalidate supported deployments also belong here. |
| Minor   | Backward-compatible capabilities, and increases to build-tool minimum requirements that are prominently announced as described below.                                                                                                                          |
| Patch   | Compatible fixes and routine dependency updates that preserve the deployment interface and minimum requirements.                                                                                                                                               |

Choose the highest-impact category among the changes in a release. An upstream dependency's major version does not automatically require a repository major release; assess its actual deployment impact, including configuration, data migration, permissions, and runtime requirements.

This is a project-specific compatibility boundary focused on supported deployments. Build-tool minimum increases are an explicit minor-release exception: the policy does not promise strict SemVer compatibility with every previously supported build environment. Do not classify a runtime minimum increase as a builder-only change.

## Build-tool minimum changes

When raising builder requirements, prominently announce the change in release notes and update the [build prerequisites](../02-setup/02-build-setup.md):

- State precise minimum versions or required features for the relevant builders (Docker Engine/Desktop, Buildx, BuildKit, or Podman/Buildah) and Dockerfile syntax frontend, including any requirement to fetch that frontend. Provide setup and verification steps.
- Explain who is affected, such as users building custom images locally or in CI, and how to update their builders.
- State whether the runtime interface and runtime prerequisites remain unchanged. Pulling and running prebuilt images alone does not require newer build tooling; any changed runtime requirements must be documented and assessed separately.

For example, a permissions-layer size optimization requiring newer BuildKit or Dockerfile syntax is a minor change when the deployment interface, volume ownership, and runtime requirements remain unchanged. A change requiring operators to adjust runtime permissions or migrate volumes is a major change.

## Independent version streams

Repository recipe releases are separate from Frappe/ERPNext application versions and image tags, and from Helm chart versions. Each stream has its own compatibility and upgrade requirements; do not infer one version number from another. Scheduled image rebuilds refresh image contents and do not, by themselves, constitute a repository recipe release.
