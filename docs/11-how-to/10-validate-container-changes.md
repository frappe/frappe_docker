---
title: Validate Container Changes
---

# Validate container changes

See [Container validation approach](../13-explanation/08-container-validation.md) for the coverage and design choices behind these checks.

## Local checks

The lint workflow runs the repository's pre-commit hooks on every pull request.
Run the same checks locally before committing:

```shell
pre-commit run --all-files
```

To run only the container-related checks:

```shell
pre-commit run hadolint --all-files
pre-commit run validate-compose --all-files
```

The Hadolint hook uses a pinned container image, so it requires a working Docker
daemon. The Compose validator requires Docker Compose, but it only renders the
configuration and does not start containers.

Address error-level Hadolint findings before submitting. The [Hadolint policy](https://github.com/frappe/frappe_docker/blob/main/.hadolint.yaml) also makes these rules blocking:

- `DL3002`: the final container user must not be root
- `DL3006`: base images must have an explicit tag
- `DL3007`: base images must not use the `latest` tag

Warnings remain visible without failing the check.

## Register a Compose override

1. Add `overrides/compose.<name>.yaml`.
2. Add the override to at least one realistic entry in
   `tests/compose-configs.json`.
3. Add harmless placeholder values to the registry's top-level `environment` object if the
   override introduces required variables that are not in `example.env`.
4. Run `python .github/scripts/validate_compose.py`.
