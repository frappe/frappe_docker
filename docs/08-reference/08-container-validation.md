---
title: Container Validation
---

This repository validates its Dockerfiles, supported Compose configurations, and
built container images at different stages of development.

# Local checks

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

# Dockerfile linting

Hadolint checks every Dockerfile and Containerfile through pre-commit and the
existing lint workflow. The policy is defined in `.hadolint.yaml`.

The initial policy keeps existing warnings visible while only errors fail the
check. It also promotes these high-confidence rules to errors:

- `DL3002`: the final container user must not be root
- `DL3006`: base images must have an explicit tag
- `DL3007`: base images must not use the `latest` tag

This allows warnings to be fixed incrementally without making unrelated pull
requests fail immediately. The failure threshold can be tightened after the
existing findings have been addressed.

# Compose configuration registry

`tests/compose-configs.json` is the registry of supported Compose combinations.
`.github/scripts/validate_compose.py` renders every entry with `docker compose
config --quiet` and fails if Docker Compose cannot merge the files.

The validator also checks that every `overrides/compose.*.yaml` file is included
in at least one registered configuration. This keeps adding a new override
simple and makes it difficult to forget its validation case.

When adding an override:

1. Add `overrides/compose.<name>.yaml`.
2. Add the override to at least one realistic entry in
   `tests/compose-configs.json`.
3. Add harmless placeholder values to the entry's `environment` object if the
   override introduces required variables that are not in `example.env`.
4. Run `python .github/scripts/validate_compose.py`.

Configurations are kept in one declarative registry and are evaluated in a
single lint job. This avoids creating a separate GitHub Actions matrix job for
every small Compose combination while preserving matrix-like coverage.

# Container image scanning

The core build workflow scans the locally built `base`, `build`, and `erpnext`
images with Trivy for each supported architecture. Reports contain fixed
`HIGH` and `CRITICAL` operating-system and application dependency
vulnerabilities.

During the initial rollout, Trivy is report-only:

- findings do not fail the build
- SARIF reports are retained as workflow artifacts for 30 days
- pull requests show a capped findings list in the workflow summary and retain
  the complete SARIF reports as artifacts
- only the version 16 AMD64 `build` image report is uploaded to GitHub Code
  Scanning, and only on pushes to `main`; complete reports for every image and
  architecture remain available as workflow artifacts

This provides visibility before deciding which vulnerability classes should
become blocking.

# Proxy image updates

Dependabot checks the Compose files in `overrides` each week and groups updates
for these externally managed proxy images:

- `nginxproxy/nginx-proxy`
- `nginxproxy/acme-companion`
- `traefik`

Database and Redis image versions are intentionally excluded because their
supported versions are defined by the Frappe framework.
