# Source Tree Analysis

```text
frappe_docker/
|-- compose.yaml              # Base Compose model for production-oriented assembly
|-- pwd.yml                   # Disposable local demo currently in use
|-- Taskfile.yml              # Local operational shortcuts; unrelated to BMAD commit scope
|-- example.env               # Environment-variable example, not production secrets
|-- docker-bake.hcl           # Frappe/ERPNext image build matrix
|-- images/                   # Dockerfiles and Containerfiles
|-- overrides/                # Database, Redis, proxy, TLS, backup, and migrator options
|-- resources/                # Runtime entrypoints and Nginx configuration
|-- tests/                    # Infrastructure integration tests
|-- .github/workflows/        # Image build, publish, lint, and documentation CI
|-- docs/                     # Upstream VitePress documentation
|-- development/              # Development and devcontainer setup
|-- _bmad/                    # BMAD v6.9.0 core and BMM module
`-- _bmad-output/             # Generated project knowledge and ERP audit artifacts
```

## Entry Points

- Demo: `docker compose -f pwd.yml up -d` or `task up`.
- Production-oriented assembly: `compose.yaml` plus selected overrides.
- Image build: `docker-bake.hcl` and files under `images/`.
- Custom application development: the development/devcontainer workflow, not `pwd.yml`.

## Important Boundary

The ERPNext and Frappe application source inspected during the audit resides inside the running container image. It is not checked into this repository. A dedicated custom-app repository is required for controlled product development.
