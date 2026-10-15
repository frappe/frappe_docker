---
title: Repository Versioning
---

# Repository versioning policy

Repository release versions help users understand the impact of changes to this repository's deployment recipes, build definitions, and supporting workflows.

## Compatibility scope

Compatibility is assessed against documented supported configurations and interfaces, runtime and persistent-data requirements, and build and deployment workflows, including platform support. This is a project-specific use of `MAJOR.MINOR.PATCH`; it does not promise strict SemVer compatibility across every previously usable toolchain or environment.

## Release classification

Maintainers decide release versions using the highest-impact category among all changes in a release.

| Release | Effect                                                                                                                                                                  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Major   | Incompatible changes to supported configurations or interfaces, runtime or persistent-data requirements, deployment or build workflows, or platform/capability support. |
| Minor   | Compatible features and support additions; routine build-tool prerequisite updates that preserve supported capabilities and workflows.                                  |
| Patch   | Compatible fixes and dependency maintenance that preserve supported interfaces, requirements, and workflows.                                                            |

Routine build-tool minimum increases can be minor when updating the stated prerequisites lets users continue the supported workflow. Losing a supported build capability or platform, or introducing a substantive workflow incompatibility, requires a major release.

Classify dependency updates by their effect on supported users and workflows. An upstream dependency's major version does not automatically require a repository major release.

A deprecation can be announced in a minor release while existing supported use remains available. Removing that supported use requires a major release.

## Release communication

Release notes for impactful changes must explain affected users, compatibility implications, and required upgrade or migration steps. State changed prerequisites precisely and update the relevant setup, build, or migration documentation, including the [build prerequisites](../02-setup/02-build-setup.md) when applicable. Announce deprecations and clearly identify removals.

## Independent version streams

Repository recipe releases are separate from Frappe/ERPNext application versions and image tags, and from Helm chart versions. Each stream has its own compatibility and upgrade requirements; do not infer one version number from another. Scheduled image rebuilds refresh image contents and do not, by themselves, constitute a repository recipe release.
