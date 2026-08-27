# Habibi Burger — Online Order Tracking System

## PoC / Workshop Input Document

**Platform:** ERPNext (vanilla, no forks) **Instance:** erp.habibi-erp.com **Purpose:** Order tracking for online food delivery, WhatsApp-integrated **Document status:** Draft for client workshop — open questions marked ❓


## 1. Scope

### In scope

- Customer master (~1,000 records to be imported from client)

- Menu as non-stock items

- Order intake → kitchen → courier → delivered → paid

- WhatsApp as the primary customer channel

- Kitchen ticket + courier delivery note (printed/digital)

- Campaigns and repeat-sales (custom-built, not CRM module)

- Owner dashboard and basic analytics

### Explicitly out of scope

| Excluded | Reason |
| - | - |
| **Stock module** | No inventory tracking. Menu items are non-stock. No warehouses, no stock ledger. |
| **POS module** | Online delivery only. No counter/walk-in flow. |
| **CRM module** | Campaign functionality built as custom doctypes instead (Section 6). |
| **Manufacturing / BOM** | No food-cost calculation in this phase. |
| **Restaurant/Hospitality forks** | Archived, dine-in oriented, carry unused table/room logic. |


### Deferred to later phases

Food cost & ingredient tracking (would require Stock + BOM), dine-in/counter sales, multi-branch, driver mobile app.


## 2. Business Flow — Stage 1 (Manual intake, core tracking)

**Goal: a working order pipeline with humans taking WhatsApp orders.**

```
Customer writes on WhatsApp  
        ↓  
Staff reads message in shared inbox  
        ↓  
Staff creates Sales Order in ERPNext  
   (customer, items, address, delivery time, payment method)  
        ↓  
Order Status: New → Confirmed  
        ↓  
KITCHEN receives ticket  ──────────►  Kitchen prepares  
   (Kanban board / printed ticket)  
        ↓  
Order Status: In Kitchen → Ready  
        ↓  
COURIER assigned + Delivery Note printed  
        ↓  
Order Status: Out for Delivery  
        ↓  
Delivered → Sales Invoice → Payment Entry  
        ↓  
Order Status: Delivered
```

**Why this stage matters:** it proves the operational backbone works before any AI is introduced. If the kitchen and couriers are not using the system reliably, adding an AI agent on top only multiplies the problem.

### Stage 1 deliverables

- [ ] Customer base imported and deduplicated

- [ ] Menu built as non-stock items with prices

- [ ] Sales Order workflow with kitchen-meaningful statuses

- [ ] Kitchen ticket format ❓

- [ ] Courier delivery note format ❓

- [ ] WhatsApp inbound → Sales Order draft (semi-automated)

- [ ] Staff trained, running live orders


## 3. Business Flow — Stage 2 (AI agent intake)

**Goal: the agent handles the conversation; staff only supervise.**

```
Customer message arrives via WhatsApp API webhook  
        ↓  
INTENT DETECTION  
   ├─ New order          → order-taking dialogue  
   ├─ Order status query → lookup by phone → reply with status  
   ├─ Menu question      → answer from menu data  
   ├─ Complaint          → escalate to human immediately  
   └─ Unclear            → clarify, then route (or escalate after 2 tries)  
        ↓  
ORDER-TAKING DIALOGUE (slot filling)  
   • items + quantities      • delivery or pickup  
   • delivery address        • requested time  
   • payment method          • confirm total  
        ↓  
Agent reads back full order → customer confirms  
        ↓  
Sales Order created via ERPNext REST API (status: New)  
        ↓  
\[Optional gate\] Staff confirms → Confirmed  
        ↓  
... continues into Stage 1 pipeline unchanged ...  
        ↓  
Automated status updates pushed back to customer on WhatsApp
```

### Guardrails (non-negotiable)

- Hand off to a human after 2 failed clarification attempts

- Never invent menu items or prices — read from ERPNext only

- Always read back the order and require explicit confirmation

- Cap order value; above threshold requires human confirmation

- If ERPNext or the model is unreachable → tell the customer a human will reply, never go silent

- Complaints and refunds always go to a human


## 4. Module Map

### ERPNext modules used

| Module | What we use it for |
| - | - |
| **Selling** | Core. Customer, Item, Price List, Sales Order, Pricing Rule, Coupon Code, sales reports. |
| **Accounts** | Sales Invoice, Payment Entry, Mode of Payment, KSA VAT / ZATCA e-invoicing. |
| **Frappe framework** | Workflow, Custom Fields, Print Formats, Notifications, Assignment Rules, Server Scripts, REST API, custom doctypes. Campaigns and promotions (custom module or used from CRM module) |


### Document chain

```
Customer  →  Sales Order  →  Sales Invoice  →  Payment Entry  
                  │  
                  ├──►  Kitchen Ticket   (print format / kanban view)  
                  └──►  Delivery Note    (print format for courier)
```

> **Important clarification:** ERPNext's built-in *Delivery Note* doctype belongs to the Stock module and creates stock ledger entries. Since we exclude Stock, our "delivery note" is a **Print Format on the Sales Order**, not that doctype. Same paper for the courier, none of the inventory machinery. Selling Settings on the instance is already set to *"Is Delivery Note required to create Sales Invoice = No"*, which is exactly right.

### Setting to change

Selling Settings currently has *"Is Sales Order required to create Sales Invoice = No"*. **Change to Yes** — the Sales Order is the single source of truth for the whole pipeline and nothing should bypass it.


## 5. Core Customizations

### 5.1 Sales Order — custom fields

| Field | Type | Notes |
| - | - | - |
| `order\_source` | Select | WhatsApp / Phone / Web / Manual |
| `fulfilment\_type` | Select | Delivery / Pickup |
| `delivery\_zone` | Link | → custom Delivery Zone doctype |
| `requested\_time` | Datetime | When customer wants it |
| `courier` | Link | → Employee |
| `whatsapp\_number` | Data | Channel identifier |
| `kitchen\_notes` | Small Text | "no onions", allergies |
| `order\_status` | Select | Operational status — see 5.2 |
| `agent\_handled` | Check | Stage 2: was this AI-created |


Delivery fee: a non-stock item line ("Delivery Charge") or a Shipping Rule per zone. ❓ decide at workshop.

### 5.2 Order Workflow

```
New → Confirmed → In Kitchen → Ready → Out for Delivery → Delivered  
  │        │           │          │            │  
  └────────┴───────────┴──────────┴────────────┴──► Cancelled
```

Built with Frappe **Workflow** (states, transitions, role permissions). Note ERPNext's native `status` field is delivery/billing-driven and will not reflect kitchen reality — we use our own field alongside it. That is normal and expected.

Role gates: kitchen staff can move In Kitchen → Ready only. Couriers can move Out for Delivery → Delivered only. Managers can do anything including Cancelled.

### 5.3 Views for operations

- **Kitchen board** — Kanban on Sales Order grouped by `order\_status`, filtered to today, auto-refresh, on a tablet

- **Dispatch list** — list view filtered to Ready, with courier assignment

- **Courier view** — filtered to own assigned orders

### 5.4 Print formats ❓

- **Kitchen ticket** — items, quantities, modifiers, order number, time. No prices. Format/paper size to confirm.

- **Delivery note** — customer name, phone, address, order total, payment method (critical for cash-on-delivery), order number.

### 5.5 Notifications

On each workflow transition, fire a WhatsApp template message to the customer (Confirmed, Out for Delivery, Delivered). Built on Frappe Notification + the WhatsApp gateway.


## 6. Campaigns — Custom Build (replacing CRM module)

Rationale: ERPNext CRM is lead/email-oriented and heavier than needed. We build a thin WhatsApp-native version.

### 6.1 Custom doctypes

**`Customer Segment`** | Field | Purpose | |---|---| | segment\_name | e.g. "Lapsed 30+ days" | | filter\_type | Select: Lapsed / New / High Value / Birthday / Manual | | parameters | JSON or fields (days, min spend, etc.) | | member\_count | Computed |

Segment membership resolved by a server script query against Sales Orders — not a stored static list, so it stays current.

**`WhatsApp Campaign`** | Field | Purpose | |---|---| | campaign\_name | | | segment | Link → Customer Segment | | message\_template | Link → approved Meta template | | coupon\_code | Link → Coupon Code | | scheduled\_time | | | status | Draft / Scheduled / Sending / Sent / Cancelled | | sent\_count / delivered / redeemed | Results |

**`Campaign Log`** — one row per recipient: customer, campaign, sent time, delivery status, whether they ordered within N days. This is what makes ROI measurable.

**`Customer Consent`** — opt-in status, timestamp, source, opt-out timestamp. **Mandatory.** Marketing without opt-in risks the WhatsApp number being banned, which would take down order intake too.

### 6.2 Campaign flow

```
Define Segment → Preview member count → Create Campaign  
   → Attach approved template + coupon → Schedule  
   → Server script sends in batches (respecting rate limits + consent)  
   → Campaign Log rows written  
   → Redemption tracked via coupon usage on Sales Orders
```

### 6.3 Charts / dashboard

- Orders per day (Sales Order count)

- Revenue per day

- Average order value

- Repeat rate — customers with \>1 order / total active

- Delivery vs pickup split

- Campaign redemption rate

- Order status distribution (live operational view)

Built with Frappe Dashboard Charts + 2–3 custom Query Reports.


## 7. Integrations

| Integration | Direction | Stage | Notes |
| - | - | - | - |
| **WhatsApp Business API** | Both | 1 & 2 | Via BSP (Meta Cloud API / 360dialog / Twilio). Requires Meta Business Verification — **start immediately, long lead time.** |
| **Middleware service** | — | 1 & 2 | Webhook receiver, session state, ERPNext REST calls. Own service, not inside ERPNext. |
| **LLM (Stage 2)** | — | 2 | Behind an OpenAI-compatible interface so cloud/local is a config change. |
| **Payment gateway** | Both | ❓ | Mada / STC Pay / Tap / HyperPay. Needed only if online prepayment required — confirm at workshop. |
| **ZATCA e-invoicing** | Outbound | 1 | Legal requirement in KSA. Confirm client's ZATCA onboarding status. ❓ |


### Middleware responsibilities

1. Receive WhatsApp webhooks

2. Identify customer by phone → find or create in ERPNext

3. Maintain conversation session state

4. Log every message as a Communication linked to the Customer

5. Create/update Sales Order via REST API

6. Send outbound template messages on status changes

7. Escalate to human inbox when needed


## 8. Customer Data Import (~1,000 records)

### Expected fields

Name, phone (primary key), address(es), notes/preferences, order history if available.

### Process

1. Client submits export (CSV/Excel) ❓ format to be confirmed

2. **Profile the data first** — check phone format consistency, duplicates, missing names, address quality

3. Normalize phone numbers to E.164 (`+9665XXXXXXXX`) — this is the join key with WhatsApp, so it must be exact

4. Deduplicate on phone

5. Map to: Customer + Contact + Address (three linked doctypes in ERPNext)

6. Import 20 records first as a test batch, verify, then full load

7. Set `customer\_group` and consent status defaults

### Watch out

- Phone numbers stored with local formats (05XXXXXXXX) or spaces/dashes — all need normalizing

- One customer with multiple addresses (home/work) is normal — model as multiple Address records

- Historic order data, if provided, may be worth importing as closed Sales Orders to seed the "repeat customer" segments — decide based on quality ❓

- Consent status for existing customers is likely unknown — assume **not opted in** for marketing until they message you


## 9. Workshop Agenda

**Session 1 — Menu and pricing (2h)** Walk the full menu, decide combo handling, modifiers, sizes, delivery fee model, VAT treatment.

**Session 2 — Operations (2h)** Current order process end to end. Kitchen ticket format. Courier process. Who does what. Which statuses actually matter to staff.

**Session 3 — Data and channels (1.5h)** Review the customer file. WhatsApp number and Meta verification status. ZATCA status. Payment methods.

**Session 4 — Demo and validation (1.5h)** Show a live order flowing through the PoC. Collect corrections.

### Open questions for the client ❓

1. Kitchen ticket — printed, tablet screen, or both? Paper size? Arabic or English?

\<default: table screen, english only\>

2. Delivery note for courier — printed, or view on courier's phone?

\<default: text with all descriptions, address link\> 

3. Delivery fee — flat, by zone, or free above a threshold?

4. Payment — cash on delivery only, or online prepayment too?

\<online payment, before the delivery\>

5. How are couriers assigned today — manually by a dispatcher, or first-available?

6. Operating hours, and what happens to messages outside them?

7. Meta Business Verification — started? Legal entity name on the Commercial Registration?

\<not started yet, anyway his should not stop whatsapp integration\>

8. ZATCA e-invoicing — already onboarded?

\<customer is outside KSA, no ZATCA needed\>

9. Customer data — what format, and does it include order history?

\<ERPNext suggested format with order history\>

10. Which languages must the system handle — Arabic, English, Arabizi?

\<English\>


## 10. PoC Success Criteria

The PoC is successful if, by the end:

- [ ] 1,000 customers imported cleanly, phones normalized, no duplicates

- [ ] Full menu live with correct prices and VAT

- [ ] An order can be created, move through all statuses, and be invoiced and paid

- [ ] Kitchen sees new orders on screen without anyone telling them

- [ ] Courier gets a delivery note with address and payment method

- [ ] A WhatsApp message from a customer results in a Sales Order in ERPNext

- [ ] Status updates reach the customer on WhatsApp automatically

- [ ] Owner can see today's orders and revenue on one dashboard

- [ ] One test campaign sent to a small segment, redemption visible

**Not required for PoC success:** AI agent, payment gateway, food costing, multi-branch.


## 11. Phasing Summary

| Phase | Focus | Outcome |
| - | - | - |
| **0 — Setup** | Clean demo data, menu, customer import, VAT | System reflects the real business |
| **1 — Order tracking** | Workflow, kitchen board, courier notes, dashboards | Staff run real orders in ERPNext |
| **2 — WhatsApp channel** | Webhooks, middleware, status messages | Orders arrive from WhatsApp, humans confirm |
| **3 — AI agent** | Intent detection, order dialogue, guardrails | Agent takes orders, humans supervise |
| **4 — Campaigns** | Segments, campaigns, consent, redemption tracking | Repeat sales loop closed |


Each phase leaves a working system. If a later phase stalls, the client still has value from the earlier ones.

