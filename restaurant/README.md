# Restaurant POS on frappe_docker (ERPNext v16)

One-click deployment of [ERPNext](https://github.com/frappe/erpnext) v16 with the
[restaurant_management](https://github.com/alphabit-technology/erpnext-restaurant) app
(floor plan, table orders, kitchen display, POS billing) plus recipe/ingredient
inventory — everything a restaurant client demo needs, reproducibly.

Proven in production style on `frappe.ikobriq.com`: a simulated 10-order lunch
service (6 paid via Cash/M-Pesa, 4 live in the kitchen) with ingredient stock
burning down through BOM recipes.

## Quick start

```bash
cp example.env .env                     # then set FRAPPE_SITE_NAME_HEADER etc.
SITE=pos.example.com ADMIN_PASSWORD=change-me SEED_DEMO=1 ./restaurant/deploy.sh
```

`deploy.sh` is re-runnable; every step skips what already exists. Flags:

| Env | Default | Meaning |
|---|---|---|
| `SITE` | `frontend` | **name the site after its public domain** (e.g. `pos.example.com`) |
| `ADMIN_PASSWORD` | `admin` | Administrator password for a new site |
| `DB_ROOT_PASSWORD` | `123` | MariaDB root (frappe_docker compose default) |
| `ERPNEXT_VERSION` | `v16.6.0` | erpnext tag baked into the image |
| `SEED_DEMO=1` | off | menu, tables, kitchen+bar, customers, ingredients, BOMs |
| `SIMULATE=1` | off | additionally runs a 10-order service + stock back-flush |

Then put a reverse proxy in front of port 8080, e.g. Caddy:

```
restaurant.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

## Files added to this repo

| File | Purpose |
|---|---|
| `apps-restaurant.json` | apps baked into the image: erpnext (pinned) + restaurant_management |
| `patch-restaurant.dockerfile` | post-build layer fixing four upstream app bugs (below) |
| `restaurant/deploy.sh` | the one-click deploy |
| `restaurant/demo_seed.py` | bootstrap + demo data + service simulation + inventory back-flush |
| `restaurant/README.md` | this document |

The image is built with frappe_docker's own `images/layered/Containerfile`
(`apps-restaurant.json` goes in as the `apps_json` build secret), then the patch
layer is applied **on top and re-tagged**. If you ever rebuild from the layered
Containerfile, re-run the patch build — step 1 of `deploy.sh` always does both.

## Upstream app bugs patched (v16 compatibility)

`restaurant_management` advertises ERPNext v13–v15. It installs and migrates
cleanly on v16, but four real defects surface at runtime — all patched in
`patch-restaurant.dockerfile` (sed on `table_order.py`):

1. **Doctype typo**: queries `Sales Taxes And Charges` (capital *And*); the table
   is `Sales Taxes and Charges`. Case-sensitive MariaDB (any Linux default)
   → 500 on any taxed order.
2. **Nonexistent column**: the same lookup selects `amount`; the field is
   `tax_amount`. Fixed in the query and the row that reads it.
3. **Global lost to v16 page-script scoping**: desk page scripts now run in a
   closure, so the page's `var RM` never reaches `window` — every class file
   (rooms, tables, kitchen) reads `RM` globally and the floor renders blank
   with `RM is not defined`. Patched to `window.RM`.
4. **None crash in `aggregate()`**: `tax += item.tax_amount` and
   `amount += item.amount` blow up when v16 leaves totals as `NULL` on
   tax-free items. Both now `or 0`.

Two **site settings** the app needs on v16 (applied by `deploy.sh` and by
`seed()`):

- **POS Settings → invoice_type = "POS Invoice"** — v16 defaults to *Sales
  Invoice mode*, which hard-blocks the app's hardcoded POS Invoice billing.
- **Site name must equal the public domain.** frappe_docker's nginx rewrites the
  `Origin` header to the site name, and frappe's websocket auth requires
  `Host == Origin` — a site named differently (e.g. `frontend` behind
  `pos.example.com`) gets *Invalid origin* and a dead kitchen display.
- **`host_name` site config** must be the public URL (deploy.sh sets it from
  `SITE_URL`) or socket.io rejects browsers with *Invalid origin* and realtime
  kitchen updates die.
- **UOM `Nos` → allow fractions** — wine by the glass consumes 0.2 bottle. For a
  long-lived production site, prefer a dedicated fractional UOM (e.g. `Bottle`)
  for by-the-glass items instead of loosening `Nos` globally.

One API quirk to know when scripting the app: `TableOrder.send` is a
`@property` — *reading* the attribute fires the kitchen dispatch; calling it
throws. `demo_seed.py` handles this.

## What the demo seed builds

`seed()` — a working restaurant:
- Room **Main Hall** with 6 tables, and two production centers — **Kitchen**
  (Starters, Main Course, Desserts) and **Bar** (Bar & Beverages) — each with the
  status chain `Sent → Processing → Completed → Delivered`.
- 15-dish menu (KES prices) on the Restaurant Menu, price-listed on every
  enabled price list.
- 9 named customers + walk-in, Cash + M-Pesa modes of payment,
  POS Profile, and an **open POS register** (Opening Entry, 5,000 float).

`seed_inventory()` — the stock layer:
- 20 stocked ingredients (Kg/Litre/Nos) with opening stock received into
  `Stores - <abbr>` at real valuation rates.
- A **BOM recipe per dish** (e.g. 1 glass of house red = 0.2 bottle;
  1 tilapia dish = 1 whole fish + oil + salad).

`simulate()` — a 10-order lunch service through the app's real API:
seat → order (with notes like *"medium rare"*) → send (items split to
Kitchen/Bar by item group) → kitchen advances statuses → deliver → pay →
POS Invoice submits. Six orders complete; four are left mid-flight so the floor
and kitchen display show live activity. Two future reservations are booked.

`backflush()` — the inventory burn:
- Finds every submitted POS Invoice not yet consumed (tracked via a tag in
  Stock Entry remarks), expands sold dishes through `RECIPES`, and posts **one
  Material Issue** from Stores. Run it at end of day, or after each service.
- `sell_one()` sells one full order on a free table — handy for demoing the
  loop live: sell, then back-flush, and watch the ingredient balances drop.

Day close: create a **POS Closing Entry** in ERPNext to reconcile the drawer
against the float + takings, then a new Opening Entry next morning.

## Deliberate scope limits

- **VAT** posts as 0 until you add a rate row to your Sales Taxes and Charges
  Template (the profile is wired for it; the template ships empty).
- Dishes are **non-stock items**; only ingredients are stocked. That is the
  standard restaurant pattern (you don't hold "Beef Burger" stock), with
  consumption via back-flush rather than per-sale manufacture entries.
- `backflush()` is manual/cron, not hooked to invoice submit — deliberate, so a
  busy service never blocks on stock validation. Cron example (host):

```bash
# nightly at 23:30 — consume the day's ingredients
30 23 * * * cd /path/to/frappe_docker && echo 'exec(open("apps/restaurant_management/restaurant_management/demo_seed.py").read(), globals()); backflush()' | docker compose exec -T backend bench --site pos.example.com console
```
