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

## Check runtime permissions

With the lint workflow's Python version (3.14) in a virtual environment, install
the permission guard's dependencies and run it from the repository root:

```sh
python -m pip install -r .github/scripts/requirements-image-checks.txt
python .github/scripts/image_sizes.py guard
python -m unittest discover -s .github/scripts -p 'test_image_sizes.py'
```

The guard checks production, custom, and layered Dockerfiles without building
images or executing their commands. A successful check exits with zero; a failure
identifies a recursive permission change or syntax that cannot be analysed.
Apply bench permission changes in the builder before the runtime copy. See the
[image size check reference](../12-reference/06-image-size-checks.md#permission-layer-guard)
for supported forms and coverage.

## Register a Compose override

1. Add `overrides/compose.<name>.yaml`.
2. Add the override to at least one realistic entry in
   `tests/compose-configs.json`.
3. Add harmless placeholder values to the registry's top-level `environment` object if the
   override introduces required variables that are not in `example.env`.
4. Run `python .github/scripts/validate_compose.py`.
