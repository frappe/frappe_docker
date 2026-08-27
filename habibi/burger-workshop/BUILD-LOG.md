# Build log — what was created on erp.habibi-erp.com

Everything below was created on the **live instance** on 2026-08-26 while
writing this pack. Frappe v16.31.0 / ERPNext v16.32.3. Nothing was forked and
no app code was written — this is all configuration a consultant can do from
the desk UI.

## Company and finance

| Thing | Value |
| --- | --- |
| Company | `Habibi Burger`, abbr `HB`, Kazakhstan, KZT, standard chart of accounts |
| Tax account | `VAT 12% - HB` under Duties and Taxes, account type Tax |
| Tax template | `KZ VAT 12% (price incl.) - HB` — On Net Total, 12%, **included in print rate** |
| Price list | `Habibi Menu`, KZT, selling |
| Modes of payment | `Kaspi Pay`, `Card Online`, `Cash on Delivery` — all mapped to `Cash - HB` |
| Currency | `KZT` enabled (it shipped disabled) |

Menu prices are VAT-inclusive, which is what a menu board shows. A ₸6,670 order
is ₸5,955.36 net + ₸714.64 VAT.

## Menu

- Item groups `Menu` → `Burgers`, `Sides`, `Drinks`, `Combos`, `Service`
- **17 items**, all `is_stock_item = 0` — no warehouse, no stock ledger,
  no reorder logic. Stock module stays entirely out of scope.
- **17 Item Prices** on `Habibi Menu`
- Item defaults per item: income account `Sales - HB`, cost centre `Main - HB`,
  default warehouse explicitly blank

## Customers

- Territory `Almaty`, customer group `Burger Guests`
- **6 demo customers**, each with a linked Contact and Address, phones in E.164
  (`+7701555xxxx`)
- 3 couriers as Employees: `HR-EMP-00001` Aidos Nurlanov, `HR-EMP-00002` Marat
  Sadykov, `HR-EMP-00003` Dana Serikova (designation `Courier`)

## Custom doctype

`Delivery Zone` (custom, module Selling, autoname by `zone_name`):
zone_name, is_active, eta_minutes, delivery_fee, free_above, notes.

Four records — Center ₸800, North ₸1,200, South ₸1,200, Suburbs ₸1,900, each
with an ETA and a free-above threshold that is not yet wired to anything.

## Sales Order custom fields

Section **Order Tracking**, inserted after `delivery_date`:

| Fieldname | Type | Notes |
| --- | --- | --- |
| `custom_order_status` | Select | New / Confirmed / In Kitchen / Ready / Out for Delivery / Delivered / Cancelled. **allow_on_submit**, read-only, in list view, standard filter. This is the workflow's state field. |
| `custom_order_source` | Select | WhatsApp / Phone / Web / Manual |
| `custom_agent_handled` | Check | read-only; set by the middleware |
| `custom_fulfilment_type` | Select | Delivery / Pickup |
| `custom_delivery_zone` | Link → Delivery Zone | shown only for Delivery |
| `custom_requested_time` | Datetime | allow_on_submit |
| `custom_whatsapp_number` | Data (Phone) | E.164 |
| `custom_courier` | Link → Employee | allow_on_submit, standard filter |
| `custom_kitchen_notes` | Small Text | allow_on_submit |

Plus one Section Break and two Column Breaks for layout.

## Workflow

`Habibi Burger Order`, active, on Sales Order, **state field
`custom_order_status`** (not the stock `workflow_state`, so the Kanban view can
group on it — Kanban needs a Select field).

| From | Action | To | Role | Condition |
| --- | --- | --- | --- | --- |
| New (draft) | Confirm | Confirmed (submitted) | Burger Order Desk | — |
| Confirmed | Send to Kitchen | In Kitchen | Burger Order Desk | `advance_paid >= grand_total` |
| In Kitchen | Mark Ready | Ready | Burger Kitchen | — |
| Ready | Dispatch | Out for Delivery | Burger Order Desk | Delivery **and** courier set |
| Ready | Handed to Customer | Delivered | Burger Order Desk | fulfilment is Pickup |
| Out for Delivery | Mark Delivered | Delivered | Burger Courier | — |
| Confirmed / In Kitchen / Ready / Out for Delivery | Cancel Order | Cancelled | Burger Order Desk | — |

`override_status` is off, so ERPNext's own delivery/billing `status` field is
left alone. There is no legal move from New to Cancelled — Frappe does not allow
a 0 → 2 docstatus transition. Delete the draft instead.

The pre-existing inactive workflow `qwe` on Sales Order was left untouched.

## Roles and permissions

Three roles: `Burger Order Desk`, `Burger Kitchen`, `Burger Courier`. They are
**workflow-transition roles** — ordinary doctype access still comes from the
standard ERPNext roles.

| Doctype | Order Desk | Kitchen | Courier |
| --- | --- | --- | --- |
| Sales Order | rwc + submit/cancel/amend | rw | rw |
| Item | (standard) | r + print | r + print |
| Customer | (standard) | — | r + print |
| Delivery Zone | rwc + report | — | r |

No users were created — that is step 0.2 of the playbook, left for whoever runs
the demo.

> **Care needed here.** Adding a Custom DocPerm row to a doctype makes Frappe
> use custom permissions *exclusively* for it, silently dropping the shipped
> ones. That happened to `Item` and `Customer` during this build and was
> repaired by re-adding the standard roles through
> `permission_manager.add/update`, which copies them properly. Always add
> permissions through **Role Permissions Manager**, never by inserting
> Custom DocPerm directly.

## Views

- **Kanban board `Kitchen Board`** on Sales Order, columns from
  `custom_order_status`, public. Filtered to `company = Habibi Burger` and
  `transaction_date` timespan `today`. Cards show name, requested time,
  fulfilment, zone, total qty, kitchen notes. Cancelled column archived.
  Column colours: New yellow, Confirmed blue, In Kitchen orange, Ready green,
  Out for Delivery cyan, Delivered light blue.
- **Saved list filters** on Sales Order: `Dispatch — Ready to go`,
  `Courier — Out for Delivery`, `Kitchen — Active today`, `Awaiting payment`.

## Print formats

- `Habibi Kitchen Ticket` — 80 mm, Jinja, no prices, Service group filtered out,
  notes in a heavy box.
- `Habibi Courier Delivery Note` — 80 mm, Jinja, name/phone/address, line items
  with prices, and a large **PAID IN FULL** / **COLLECT ON DELIVERY** banner
  driven by `grand_total - advance_paid`.

Both render at
`/printview?doctype=Sales Order&name=<id>&format=<format>&no_letterhead=1`.

## Analytics

- **5 Number Cards**: Orders Today, Revenue Today, Average Order Value (this
  month), Orders Delivered Today, Open Orders in Kitchen
- **7 Dashboard Charts**: Orders per Day, Revenue per Day, Order Status
  Distribution, Delivery vs Pickup, Revenue by Delivery Zone, Orders by Source,
  Top Selling Items
- **Dashboard** `Habibi Burger Ops` at `/desk/dashboard-view/Habibi Burger Ops`

Top Selling Items is filtered by item group rather than company, because
`Sales Order Item` carries no company field.

## Settings changed (site-wide — note these)

- `Selling Settings.so_required` → **Yes** (was No). Per scope section 4: the
  Sales Order is the single source of truth and nothing may bypass it.
  **This affects every company on the instance**, including Test (Demo).
- `Selling Settings.dn_required` stays **No** — correct, since Stock is out of
  scope and the courier note is a print format, not a Delivery Note document.
- Currency `KZT` enabled.

## Demo data left on the instance

| Order | Status | Total | Purpose |
| --- | --- | --- | --- |
| SAL-ORD-2026-00007 | Delivered | ₸6,670 | The worked example. Invoiced `ACC-SINV-2026-00006`, paid, outstanding ₸0. |
| SAL-ORD-2026-00008 | New | ₸9,160 | Draft awaiting confirmation |
| SAL-ORD-2026-00009 | New | ₸3,580 | The only **Pickup** order |
| SAL-ORD-2026-00010 | Confirmed | ₸10,550 | **Deliberately unpaid** — demonstrates the payment gate |
| SAL-ORD-2026-00011 | Cancelled | ₸9,580 | Cancelled with its payment reversed |
| SAL-ORD-2026-00012 | Ready | ₸12,030 | Moved to Ready by a real Kanban drag |
| SAL-ORD-2026-00013 | Ready | ₸5,980 | Waiting on a courier |
| SAL-ORD-2026-00014 | Out for Delivery | ₸11,780 | Courier Aidos Nurlanov assigned |
| SAL-ORD-2026-00015 | In Kitchen | ₸9,580 | Carries the sesame-allergy note |

Do not delete 00010 — the whole payment-gate demonstration depends on it being
confirmed and unpaid.

## Bug found

Creating a `WhatsApp Templates` record with no WhatsApp Account configured fails
with a raw `NameError: name 'throw' is not defined` from `habibi_whatsapp`
instead of a readable message. The guard that should say "configure an account
first" is itself broken. Worth fixing before a client sees it.

## To undo this build

Delete in this order: the demo Sales Orders (cancel first where submitted, and
note that ledger-linked documents cannot be deleted at all), Payment Entries,
Sales Invoice, then Kanban Board `Kitchen Board`, the saved List Filters,
the two Print Formats, the 7 Dashboard Charts, 5 Number Cards and the Dashboard,
the Workflow `Habibi Burger Order`, the 12 Custom Fields on Sales Order, the
`Delivery Zone` doctype and its 4 records, the 3 roles, 3 Employees, 6
Customers with their Contacts and Addresses, 17 Items and Item Prices, the price
list, tax template, tax account, and finally the company `Habibi Burger`.

Also revert `Selling Settings.so_required` to **No** if the other companies on
the instance need the old behaviour.
