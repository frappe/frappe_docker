# Professional ERP Gap Analysis Report

**System:** Local ERPNext site `frontend`
**Audit date:** 2026-06-22
**Application versions:** ERPNext 16.23.0, Frappe 16.23.0
**Deployment:** Docker Compose demo stack (`pwd.yml`)
**Companies:** 2 leaf companies, MKD, Macedonia
**Assessment posture:** Evidence-based and conservative; a capability is not treated as implemented merely because a DocType or source module exists.

## 1. Executive Summary

The system is a functioning ERPNext demonstration with a broad standard application codebase, a healthy MariaDB database, two online workers, an active scheduler, and a responsive API. The installed source contains 637 ERPNext DocType definitions, 305 Frappe DocType definitions, 184 ERPNext report definitions, and 14 ERPNext workspace definitions. The live database exposes 193 reports, 19 public workspaces, 49 dashboard charts, and 50 number cards.

That technical breadth materially overstates the readiness of this specific implementation. The live site has no configured workflows, authorization rules, custom permissions, user restrictions, POS profiles, bank accounts, bank transactions, budgets, accounting dimensions, finance books, payment-term templates, CRM pipeline records, assets, projects, BOMs, work orders, employees, or production-grade integrations. HR/Payroll and restaurant/hospitality schemas are not installed. Two-factor authentication is disabled, password login remains enabled, session expiry is 170 hours, and the active deployment uses HTTP and documented demo credentials.

The repository is also the upstream `frappe_docker` infrastructure repository, not a product-owned ERP application repository. ERPNext source and business behavior arrive from a container image. There is no version-controlled custom Frappe app containing business-specific DocTypes, workflows, fixtures, reports, permissions, integrations, or migrations.

**Audit verdict:** suitable for demonstration and controlled discovery only. It is not ready for production, financial control reliance, scalable multi-company operation, hospitality operations, payroll, or enterprise deployment.

## 2. Scope, Method, and Evidence

### Inspected directly

- Running containers, health, versions, scheduler, workers, and HTTP API.
- ERPNext and Frappe source trees inside the running image.
- Installed applications and live site schema.
- Company structure, master-data counts, transaction counts, reports, workspaces, dashboards, roles, permissions, workflows, audit records, authentication settings, custom fields, and property setters.
- Docker Compose files, image build definitions, CI workflows, tests, security posture, persistence, and deployment documentation.
- Official product catalogs/documentation for ERPNext, Odoo, Microsoft Dynamics 365 Business Central, SAP Business One, and Oracle NetSuite where accessible.

### Important limitations

- No stakeholder interviews, process maps, statutory requirements, target operating model, SLAs, volume forecasts, or approved requirements were supplied.
- No production workload or production data was audited.
- Browser automation of the authenticated Desk UI could not be completed; UX conclusions use live workspace/dashboard metadata, standard Frappe behavior, and configuration evidence. They are not a substitute for moderated usability testing.
- Competitor positioning is directional, not a procurement-grade fit-gap study. Licensing, localization, implementation partner quality, and exact edition capabilities require separate validation.

## 3. Current-System Snapshot

| Area | Verified state |
|---|---|
| Runtime | 9 long-running services; database healthy; two workers online; scheduler active |
| Installed apps | `frappe` 16.23.0 and `erpnext` 16.23.0 only |
| Companies | 2 independent leaf companies; no parent group structure |
| Users | 2 enabled System Users and 1 enabled Website User |
| Core accounting data | 191 accounts, 4 cost centers, 42 submitted GL entries |
| Commercial data | 3 customers, 3 suppliers, 5 submitted sales invoices, 6 submitted purchase invoices |
| Inventory data | 11 items, 10 warehouses, 16 stock-ledger entries |
| Process controls | 0 workflows, 0 authorization rules, 0 custom DocPerm records, 0 user permissions |
| Banking | 0 bank accounts, 0 bank transactions |
| Planning/analysis | 0 budgets, 0 accounting dimensions, 0 finance books |
| POS | POS schema exists; 0 POS profiles |
| HR/Payroll | 0 employees; payroll schemas such as Salary Structure, Salary Slip, and Payroll Entry are missing |
| Hospitality | Restaurant, Restaurant Menu, and Restaurant Order Entry schemas are missing |
| Integrations | 0 OAuth clients, connected apps, webhooks, API keys, and integration requests |
| Security | 2FA disabled; password login enabled; email-link login enabled; 170-hour session expiry; HTTP demo endpoint |
| Customization | 12 mostly framework-level custom fields, 180 property setters, no client/server scripts, no custom app |

## 4. Final Scoring

Scores assess this implementation, not ERPNext as a product.

| Dimension | Score / 100 | Rationale |
|---|---:|---|
| Product Readiness | 28 | Working demo, but no approved requirements, product ownership, custom app, release model, or production controls |
| Functional Completeness | 46 | Broad standard schemas and reports; major configured gaps in POS, banking, HR/payroll, hospitality, approvals, integrations, and planning |
| Accounting Maturity | 43 | Core ledger and statements exist; no budgets, dimensions, finance books, bank setup, reconciliation data, group hierarchy, or close controls |
| Security | 18 | 2FA off, long sessions, demo credentials, HTTP, no user restrictions, no SSO, no custom SoD controls |
| Scalability | 24 | Single-host demo, local named volumes, no HA, resource limits, autoscaling, load evidence, or observability stack |
| UX | 42 | Standard workspaces and dashboards exist; no role-specific tailoring, onboarding design, accessibility evidence, mobile validation, or POS UX configuration |
| Enterprise Readiness | 17 | Missing governance, consolidation design, segregation of duties, DR, monitoring, integration architecture, and controlled SDLC |
| **Overall ERP Score** | **31** | **Functional demo with credible platform potential, but not an operationally governed ERP implementation** |

## 5. Functional Coverage

| Domain | Standard capability in code/schema | Live implementation evidence | Gap and risk | Assessment |
|---|---|---|---|---|
| Sales | Quotations, orders, delivery, invoicing, pricing, returns | 3 customers; 5 submitted sales invoices | No workflow, authorization rule, pricing rule, payment terms, CRM linkage, or tested order-to-cash controls | Partial |
| POS | POS Invoice and POS Profile schemas | 0 POS profiles | No store/register configuration, cashier roles, shifts, payment modes, offline/recovery testing, or hardware integration | Not implemented |
| Purchasing | Supplier quotation, purchase order, receipt, invoice | 3 suppliers; 6 submitted purchase invoices | No procure-to-pay approval, supplier governance, payment terms, three-way-match validation, or exception management | Partial |
| Inventory/Warehousing | Warehouses, stock ledger, transfers, reconciliation, serial/batch and quality schemas | 11 items; 10 warehouses; 16 stock-ledger entries | No reorder rules, serials, batches, quality inspections, cycle-count policy, barcode process, WMS routing, or capacity controls | Early/basic |
| Accounting/Finance | GL, AR/AP, tax templates, financial statements | 191 accounts; 4 cost centers; 42 GL entries; standard statements present | No budgets, accounting dimensions, finance books, close calendar, period-close evidence, cash forecast, or management-accounting design | Core only |
| Banking/Reconciliation | Bank Transaction, reconciliation, Payment Entry schemas and reports | 0 bank accounts; 0 bank transactions | No bank import/feed, matching rules, payment file, statement process, approval, fraud control, or integration | Not implemented |
| Accounts Receivable | AR report, sales invoices, payment/reconciliation schemas | 5 submitted sales invoices | No credit policy, collections workflow, dunning, aging ownership, dispute process, or automated matching | Partial |
| Accounts Payable | AP report, purchase invoices, payments | 6 submitted purchase invoices | No invoice approval, duplicate control evidence, payment proposal, bank authorization, vendor master approval, or three-way match evidence | Partial |
| HR/Payroll | Employee core schema only | 0 employees | HRMS/payroll application schemas are missing; no employee lifecycle, time, leave, payroll, benefits, statutory reporting, or SoD | Missing |
| CRM | Lead, opportunity and customer schemas/workspace | 0 leads; 0 opportunities | No pipeline, lead routing, activities, forecast, campaign attribution, SLAs, or sales governance | Not implemented |
| Fixed Assets | Asset module and reporting schemas | 0 assets | No asset register, capitalization, depreciation books, impairment, transfer, disposal, or reconciliation process | Not implemented |
| Projects | Project, task, timesheet, costing schemas | 0 projects | No templates, resource/cost control, billing rules, stage gates, margin reporting, or portfolio governance | Not implemented |
| Manufacturing | BOM, routing, work order, planning and quality schemas | 0 BOMs; 0 work orders | No product structures, routings, work centers, capacity, MRP validation, costing, traceability, or shop-floor process | Not implemented |
| Hospitality/Restaurant | None in installed schema | Restaurant-related schemas missing | Requires a maintained hospitality/POS application or custom domain solution; table service, kitchen display, modifiers, tips, reservations, and shift controls absent | Missing |
| Reporting/BI | 193 live reports, 49 charts, 50 number cards, Financial Reports workspace | Standard content only; no external BI/integration activity | No governed KPI catalog, semantic model, custom executive dashboards, row-level analytics security, data warehouse, or scheduled distribution design | Standard only |
| Audit/Compliance | Version, Activity Log, Access Log, Audit Trail schemas | 32 versions; 2 activity logs; 0 access logs | No control framework, review ownership, retention, alerting, SoD matrix, evidence packs, or compliance mapping | Weak |

## 6. Missing Features and Capabilities

### Critical missing features

1. Production deployment architecture with TLS, secure secrets, immutable custom images, tested backups, restore drills, monitoring, alerting, staging, rollback, RPO, and RTO.
2. Product-owned custom Frappe app and repository for versioned business configuration.
3. Approval workflows for sales discounts, purchasing, supplier invoices, payments, journals, stock adjustments, master-data changes, and high-risk administrative actions.
4. Segregation-of-duties matrix and enforced permissions for request, approval, posting, payment, reconciliation, and administration.
5. Banking setup, statement ingestion, reconciliation rules, payment controls, and bank integration.
6. HRMS/payroll solution if employees and payroll are in scope.
7. Hospitality/restaurant application if restaurant operations are in scope.
8. Data migration, reconciliation, retention, privacy, and master-data governance.

### Modern ERP expectations not evidenced

- Embedded document capture/OCR with validation and approval.
- Governed self-service analytics and drill-through KPIs.
- Mobile-optimized approval and operational journeys.
- Event-driven integrations, idempotency, retries, dead-letter handling, and integration observability.
- Automated close checklist and financial-control attestations.
- Anomaly detection for duplicates, unusual payments, margin leakage, and stock variance.
- Guided onboarding, contextual help, role-based home pages, and task-based navigation.
- Automated testing of critical financial and operational processes.

### SMB requirements

- Fast configuration templates, simple permissions, bank import, tax/localization validation, cash visibility, inventory replenishment, basic payroll integration, reliable backups, and simple operational dashboards.

### Enterprise and multi-company requirements

- Parent/group company hierarchy, consolidation/elimination design, intercompany transactions, shared-service workflows, multi-book accounting, advanced dimensions, approval limits, SoD, audit evidence, SSO/identity lifecycle, high availability, integration governance, performance testing, and formal change/release management.

The current two companies are independent leaf companies with no parent company. The Consolidated Financial Statement report exists, but the organization structure and elimination process required for controlled consolidation are not configured.

## 7. Business Process Analysis

No custom workflows or authorization rules exist, so the system relies on standard draft/submit/cancel behavior and role permissions. This is inadequate for controlled finance and scaled operations.

| Process | Likely bottleneck/control gap | Required improvement |
|---|---|---|
| Order-to-cash | Manual discount, credit, delivery, and invoice decisions; no collections workflow | Credit limits, discount approval, delivery/invoice controls, dunning, dispute ownership, automated aging actions |
| Procure-to-pay | No requisition/PO/invoice/payment approval chain evidenced | Requisition policy, vendor onboarding approval, three-way match, exception routing, payment proposal and dual approval |
| Record-to-report | Statements exist but no close workflow, budgets, dimensions, or finance books | Close calendar, reconciliations, journal approval, lock dates, variance review, management dimensions, evidence retention |
| Inventory | No replenishment, traceability, quality, or cycle-count configuration | Reorder policies, barcode flows, serial/batch where required, quality gates, cycle counts, variance approval |
| Banking | No bank master or transactions | Statement ingestion, auto-matching, unmatched-item queue, maker-checker payment controls, daily reconciliation SLA |
| CRM-to-sales | No leads/opportunities | Lead capture, qualification, assignment, pipeline stages, conversion controls, forecast and activity SLAs |
| Manufacturing | Schemas exist but no master data or transactions | BOM/routing governance, MRP parameters, capacity, work-order control, costing, scrap/rework and traceability |
| Master data | No user restrictions or approval workflows | Data-owner roles, duplicate detection, approval, effective dating, change audit and periodic review |

## 8. User Experience Review

### Verified strengths

- Nineteen public workspaces expose core areas such as Selling, Buying, Stock, Accounts, Manufacturing, Projects, CRM, Assets, Quality, Support, and Integrations.
- Forty-nine dashboard charts and fifty number cards provide a standard analytics foundation.
- Frappe provides consistent list/form/report interaction patterns and role-based visibility mechanisms.

### Gaps and risks

- All identified workspaces are public; there is no evidence of tailored role-specific landing experiences for cashier, buyer, warehouse operator, accountant, controller, manager, or executive.
- Navigation exposes many modules before business scope and role journeys are defined, increasing cognitive load and training cost.
- No configured POS profile exists, so the cashier journey is not operational.
- No onboarding workflow, guided setup, process help, training content, or adoption telemetry was found.
- No authenticated mobile usability or accessibility test was completed. Mobile responsiveness must be proven with task-based tests, not assumed from framework CSS.
- Dashboard quantity does not prove dashboard effectiveness. KPI ownership, definitions, thresholds, drill paths, data freshness, and actionability are undefined.
- Form usability needs field-level review after process design; current property setters alone do not demonstrate a coherent form strategy.

### UX recommendation

Design and test eight priority journeys: quote-to-cash, purchase-to-pay, receiving/put-away, picking/delivery, bank reconciliation, month-end close, manager approvals, and mobile exception handling. Measure completion time, errors, navigation steps, and training dependency.

## 9. Security and Financial-Control Review

| Control area | Finding | Risk | Required action |
|---|---|---|---|
| Authentication | 2FA disabled; password login enabled; 170-hour sessions | Account compromise and persistent unauthorized access | Enforce MFA/SSO, shorten sessions, define password and lockout standards, review email-link login |
| Transport | Active demo is HTTP on port 8080 | Credential/session exposure | TLS-only production endpoint with secure proxy configuration |
| Secrets | Demo passwords are stored in `pwd.yml` | Credential leakage and reuse | External secrets, rotation, environment separation, no defaults |
| Authorization | 48 roles and 718 assignments exist, but 0 custom permissions and 0 user restrictions | Default roles may overexpose cross-company or sensitive data | Role design, least privilege, company/user restrictions, quarterly access review |
| Segregation of duties | 0 workflows and 0 authorization rules | One user may create, approve, post, pay, and reconcile | Formal SoD matrix and maker-checker workflows |
| Audit | Audit Trail and Version exist; evidence volume is minimal | Incomplete traceability and no review process | Enable appropriate tracking, centralize logs, retain evidence, alert on privileged changes |
| Integrations | No OAuth clients, webhooks, API keys, or integration requests | Low current exposure, but no integration security architecture | OAuth/service identities, scoped access, secret rotation, audit, rate limits, idempotency |
| Data isolation | Two companies; no user permissions | Cross-company data leakage | Company-based permissions and validation tests |
| Financial controls | No budgets, bank setup, approval workflows, or close control | Misstatement, fraud, uncontrolled spend | Approval limits, reconciliations, close checklist, exception reporting, independent review |

## 10. Technical Architecture Review

### Strengths

- Clear separation of frontend, backend, websocket, scheduler, short/long workers, database, and Redis services.
- Healthy database, active scheduler, and two online workers.
- Standard Frappe metadata architecture supports rapid extension.
- Existing upstream CI and infrastructure tests cover connectivity, endpoints, assets, file headers, HTTPS overrides, backup mechanics, and PostgreSQL site creation.

### Critical weaknesses

- `pwd.yml` is explicitly disposable and not a migration path to production.
- Single-host architecture with local named volumes; no database HA, Redis HA, shared file-store design, or failover.
- No resource requests/limits, autoscaling, workload sizing, queue-depth thresholds, or load-test evidence.
- No metrics, tracing, centralized logs, SLOs, uptime checks, business-process monitoring, or alert routing.
- Only database health is explicitly checked in the demo compose definition; application dependency readiness is weak.
- Container tag is versioned but not digest-pinned. No custom immutable image contains product-owned code.
- No controlled application migration pipeline or verified rollback strategy.
- No product-specific automated tests despite 369 ERPNext source tests and infrastructure tests upstream.
- Generic Frappe APIs and approximately 194 ERPNext source files with whitelisted methods provide extensibility, but no API catalog, versioning policy, service-account model, rate-limit policy, or integration contracts exist for this implementation.

### Database and maintainability

The Frappe DocType model provides a mature relational metadata layer, but this site has no product-owned schema package. Direct in-database customizations and property setters are not a sufficient source of truth. Business configuration must be exported into a custom app as fixtures, patches, and tested migrations.

## 11. Accounting and Finance Assessment

### Present and verified

- Standard General Ledger, Trial Balance, Balance Sheet, Profit and Loss Statement, Cash Flow, AR, AP, Budget Variance, Bank Reconciliation, Gross Profit, Stock Balance, and Consolidated Financial Statement reports.
- Submitted sales invoices, purchase invoices, and GL entries demonstrate basic posting.
- Sales and purchase tax templates exist for both companies.
- Cost centers and a chart of accounts exist.

### Missing or unproven

- Budgets, accounting dimensions, finance books, payment-term templates, currency-exchange rates, bank accounts, bank transactions, and bank reconciliation activity.
- Group-company hierarchy, eliminations, intercompany policy, consolidation calendar, and ownership of consolidated statements.
- Cash forecasting, treasury positioning, payment proposal controls, bank connectivity, and fraud controls.
- Period-close checklist, balance-sheet reconciliations, journal approval, lock-date governance, accrual policy, and audit sign-off.
- Tax localization validation for Macedonia, including statutory reporting, e-invoicing/fiscalization, retention, and change management. This requires a qualified local accountant/legal specialist.
- AP invoice approval and three-way-match evidence; AR credit and collections policy.
- Payroll accounting because HRMS/payroll is not installed.

**Finance verdict:** credible core ledger capability, but low control maturity and insufficient configuration for reliance on financial reporting.

## 12. Competitive Benchmark

| Product | Relative strength versus this implementation | Current implementation advantage | Key gap to close |
|---|---|---|---|
| ERPNext standard | Same core product; broad open-source modules and customization model | Full control of deployment and source ecosystem | This site uses only a thin standard configuration and no product-owned app |
| Odoo | Broader immediately visible application catalog, including Accounting, CRM, POS Shop, POS Restaurant, Inventory, Manufacturing, PLM, HR, Projects, Field Service, and Spreadsheet BI | More transparent metadata and self-hosting control; potentially lower customization barrier | Install/configure domain apps, govern extensions, and deliver comparable end-to-end role journeys |
| SAP Business One | Strong SMB implementation governance, finance/operations controls, and partner ecosystem | Greater openness and lower platform lock-in | Add disciplined controls, localization, support model, and implementation governance |
| Microsoft Dynamics 365 Business Central | Strong Microsoft ecosystem integration and documented finance, sales, purchasing, inventory, warehouse, manufacturing, project, service, HR, analytics, and job-queue capabilities | Open-source extensibility and self-hosting flexibility | Match identity, analytics, workflow, service management, and governed extension lifecycle |
| Oracle NetSuite | Mature cloud multi-entity finance, consolidation, controls, and enterprise operating model | Deployment control and lower dependence on a single SaaS vendor | Build multi-company hierarchy, consolidation, audit controls, integrations, availability, and operational governance |

This comparison should not drive product selection without a formal requirements matrix, scripted demos, localization validation, total-cost analysis, reference checks, and implementation-partner assessment.

## 13. Prioritized Roadmap

### Critical — Must Have

1. Approve Product Brief, PRD, process scope, jurisdictions, user roles, volumes, SLAs, KPIs, and acceptance criteria.
2. Create a dedicated custom Frappe app/repository; export all approved fields, workflows, permissions, reports, fixtures, and migrations.
3. Replace `pwd.yml` with separate dev/test/staging/production environments and a custom immutable image.
4. Implement TLS, external secrets, MFA/SSO, session hardening, least privilege, company isolation, and SoD.
5. Define approval workflows for purchasing, payments, journals, sales exceptions, stock adjustments, and master data.
6. Implement encrypted off-site backups, automated verification, restore drills, monitoring, alerts, RPO/RTO, and disaster recovery.
7. Complete finance design: chart governance, periods, dimensions, budgets, bank setup, tax/localization, close, reconciliations, and audit evidence.
8. Decide and install HRMS/payroll and hospitality applications only if approved in scope.

### High Priority

1. Configure and test order-to-cash, procure-to-pay, inventory, banking, and record-to-report end to end.
2. Establish data migration, cleansing, deduplication, reconciliation, retention, and master-data ownership.
3. Add bank integration, automated reconciliation, payment controls, and cash dashboards.
4. Implement POS profiles, cashier controls, shifts, payments, returns, offline/recovery, and hardware integration if retail is in scope.
5. Build CI/CD with automated migrations, rollback controls, dependency scanning, unit tests, integration tests, and E2E financial assertions.
6. Define integration architecture with OAuth service identities, contracts, idempotency, retries, failure queues, and monitoring.
7. Design role-specific workspaces and training/onboarding.

### Medium Priority

1. CRM pipeline, lead routing, forecasting, campaign attribution, and customer-service SLAs.
2. Fixed assets, projects, manufacturing, quality, and maintenance based on validated business scope.
3. Governed KPI catalog, executive dashboards, scheduled reporting, and a BI/data-platform strategy.
4. Performance baselines, realistic load testing, queue tuning, database tuning, capacity model, and HA design.
5. Accessibility and mobile task validation.

### Low Priority

1. AI assistance, anomaly detection, predictive replenishment, and forecasting after controls and data quality stabilize.
2. Advanced workflow mining and continuous process optimization.
3. Nonessential visual customization and experimental integrations.

## 14. Release Gates

Production approval should be blocked until all of the following are evidenced:

- Signed PRD and process/control design.
- No default credentials; TLS and managed secrets active.
- MFA/SSO, company isolation, least privilege, and SoD tests pass.
- Critical workflows and approval limits pass E2E tests.
- Opening balances and migrated data reconcile to signed source totals.
- Bank reconciliation and month-end close complete successfully in staging.
- Backup restore and disaster-recovery drills meet approved RPO/RTO.
- Load, security, migration, rollback, and monitoring tests pass.
- Local statutory/tax requirements receive expert sign-off.
- Operational ownership, support SLAs, runbooks, and escalation paths are accepted.

## 15. Evidence and Official Benchmark Sources

### Local evidence

- `docker compose -f pwd.yml ps`
- `bench version`, `bench --site frontend list-apps`, and `bench --site frontend doctor`
- Read-only MariaDB metadata and aggregate-count queries against the local site
- `pwd.yml`, `compose.yaml`, overrides, Docker build definitions, CI workflows, and tests

### Official product sources

- ERPNext documentation: https://docs.frappe.io/erpnext/user/manual/en/introduction
- Odoo application catalog: https://www.odoo.com/page/all-apps
- SAP Business One product/help portal: https://help.sap.com/docs/SAP_BUSINESS_ONE
- Microsoft Dynamics 365 Business Central documentation: https://learn.microsoft.com/en-us/dynamics365/business-central/
- Oracle NetSuite Help Center: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/index.html

## 16. Recommended Next Decision

Start a BMAD Product Brief and PRD using this report as evidence. The first workshop must decide the target industry, legal jurisdictions, company structure, required modules, user personas, transaction volumes, integrations, and the minimum controlled processes for the first production release.
