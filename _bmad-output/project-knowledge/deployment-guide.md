# Deployment Guide

## Current State

`pwd.yml` is a disposable demonstration. It uses default credentials, publishes HTTP on port 8080, and stores data in local named volumes. It must not be promoted to production.

## Production Baseline

- Use `compose.yaml` with the required database, Redis, proxy/TLS, migrator, and backup components.
- Build a custom immutable image and pin releases or commit SHAs; consider digest pinning for deployment.
- Store secrets outside Git and apply rotation, environment separation, and least privilege.
- Enforce a domain and TLS; never expose database or Redis services publicly.
- Run application/database migrations automatically with explicit failure handling.
- Create encrypted off-site backups and perform scheduled restore drills.
- Add centralized logs, metrics, traces where appropriate, uptime checks, queue monitoring, and alerts.
- Define staging, rollback, RPO, RTO, and a disaster-recovery runbook.
- Set resource limits, produce a capacity model, and execute representative load tests.
- Add security scanning and controlled release approvals.

## Minimum Release Verification

```powershell
docker compose -f <production-compose.yml> config --quiet
```

Then verify migrations, application health, permissions, critical workflows, accounting outcomes, backups/restores, monitoring, rollback, and load/security gates before approval.
