# Component Inventory

| Component | Present | Version-controlled here | Observation |
|---|---:|---:|---|
| Frappe Framework | Yes | No | Delivered by the application image |
| ERPNext | Yes | No | Delivered by the application image |
| Product-owned Frappe app | No | No | Critical product-delivery gap |
| MariaDB | Yes | Configuration only | Healthy local demo database |
| Redis cache/queue | Yes | Configuration only | No authentication in demo |
| Nginx frontend | Yes | Template/configuration | HTTP local entry point |
| Background workers | Yes | Configuration only | Two workers online |
| Scheduler | Yes | Configuration only | Active |
| TLS proxy | Available upstream | Compose override | Not active in `pwd.yml` |
| Backup job | Available upstream | Example/override | Not active in the running stack |
| Monitoring and alerting | No | No | Critical production gap |
| HRMS/Payroll | No | No | Payroll schemas are missing |
| Hospitality/Restaurant | No | No | Restaurant schemas are missing |
| Business-process tests | No | No | Requires an approved PRD and custom app |

For live feature and configuration evidence, see [Professional ERP Gap Analysis](./erp-readiness-gap-analysis.md).
