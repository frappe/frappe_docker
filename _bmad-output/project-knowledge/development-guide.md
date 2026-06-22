# Development Guide

## Prerequisites

- Docker Desktop and Docker Compose v2.
- Git and Go Task v3.50 or newer for local shortcuts.
- Node.js 20.12+, Python 3.10+, and `uv` for BMAD tooling.

## Local Commands

```powershell
task up
task ps
task logs
task site-logs
task shell
task exec -- list-sites
task down
```

## Correct Customization Path

1. Do not develop custom applications inside the disposable `pwd.yml` environment.
2. Create a dedicated custom Frappe app using the development/devcontainer setup.
3. Store DocTypes, fixtures, workflows, permissions, reports, patches, and tests in Git.
4. Include the custom app through `apps.json` and build an immutable custom image.
5. Promote the same tested artifact through development, test, staging, and production.
6. Run controlled migrations and retain a tested rollback/recovery path.

## Testing Strategy

The repository currently provides infrastructure integration tests. The product repository must add unit, integration, permission, migration, and E2E tests for critical processes. Financial tests must assert resulting GL entries, stock tests must assert stock-ledger outcomes, and access tests must verify both allowed and denied actions.

Use [Professional ERP Gap Analysis](./erp-readiness-gap-analysis.md) as input to the Product Brief and PRD.
