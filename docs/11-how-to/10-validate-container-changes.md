---
title: Validate Container Changes
---

# Validate container changes

See [Container validation](../12-reference/02-container-validation.md) for check policies and CI behavior.

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

## Register a Compose override

1. Add `overrides/compose.<name>.yaml`.
2. Add the override to at least one realistic entry in
   `tests/compose-configs.json`.
3. Add harmless placeholder values to the entry's `environment` object if the
   override introduces required variables that are not in `example.env`.
4. Run `python .github/scripts/validate_compose.py`.
