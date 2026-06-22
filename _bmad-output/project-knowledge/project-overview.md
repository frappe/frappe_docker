# Project Overview

## Purpose

This repository is a checkout of `frappe/frappe_docker`. It provides Docker images, Compose configurations, and operational documentation for running Frappe applications such as ERPNext. It is an infrastructure repository, not the source repository of the business ERP product.

## BMAD Classification

| Field | Result |
|---|---|
| Project type | Infrastructure / container orchestration |
| Repository structure | Monolith with one logical infrastructure part |
| Runtime | Docker Compose v2 |
| Installed applications | Frappe 16.23.0 and ERPNext 16.23.0 |
| Demo database | MariaDB 11.8 |
| Cache and queue | Redis 6.2 |
| Local entry point | HTTP on port 8080 |

## Verified State

- The active site is `frontend`.
- `/api/method/ping` returns HTTP 200 with `pong`.
- MariaDB reports healthy, two workers are online, and the scheduler is active.
- The live site contains two Macedonian companies, limited sample transactions, and broad standard ERPNext metadata.
- `pwd.yml` is an explicitly disposable demo environment and is not suitable for production or custom-app development.

## Audit Boundary

ERPNext functionality is delivered by the `frappe/erpnext:v16.23.0` image. There is no version-controlled custom Frappe application containing business-specific DocTypes, workflows, permissions, reports, integrations, fixtures, or migrations.

See [Professional ERP Gap Analysis](./erp-readiness-gap-analysis.md) for the detailed implementation assessment.
