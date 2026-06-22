# BMAD Project Knowledge Index

## Quick Reference

- **Project type:** Infrastructure monolith
- **Stack:** Docker Compose, Frappe/ERPNext 16.23.0, MariaDB 11.8, Redis 6.2
- **Architecture:** Containerized multi-service runtime
- **Readiness:** Functional demonstration; not a production or product-owned ERP implementation

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Component Inventory](./component-inventory.md)
- [Development Guide](./development-guide.md)
- [Deployment Guide](./deployment-guide.md)
- [Professional ERP Gap Analysis](./erp-readiness-gap-analysis.md)

## Existing Repository Documentation

- [Repository README](../../README.md)
- [Upstream Documentation](../../docs/index.md)
- [Choosing a Deployment Method](../../docs/01-getting-started/01-choosing-a-deployment-method.md)
- [Production Documentation](../../docs/03-production/)
- [Contribution Guide](../../CONTRIBUTING.md)

## Recommended BMAD Sequence

1. Run `[CB] Create Brief` with `bmad-product-brief` using the ERP gap analysis as evidence.
2. Run `[PRD] Create/Edit/Review PRD` with `bmad-prd`.
3. Define architecture, epics, stories, test strategy, and implementation readiness only after stakeholders approve the PRD.
