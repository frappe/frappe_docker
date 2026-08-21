# frappe_docker fork — Restaurant POS kit

Fork of frappe/frappe_docker carrying a one-click restaurant POS deploy
(ERPNext v16 + alphabit-technology's `restaurant_management`). Everything
specific to this fork lives in `restaurant/` — start with
[restaurant/README.md](restaurant/README.md) for the user-facing story.
This file is the working knowledge for developing and debugging it.

## Layout

- `apps-restaurant.json` — apps baked into the image (erpnext pinned + restaurant app), fed to `images/layered/Containerfile` as the `apps_json` build secret.
- `patch-restaurant.dockerfile` — post-build layer applying all app fixes; `FROM custom-erpnext:<tag>` onto itself and re-tags.
- `restaurant/deploy.sh` — the one-click. Re-runnable; every step skips what exists.
- `restaurant/demo_seed.py` — bootstrap()/seed()/seed_inventory()/simulate()/sell_one()/backflush()/layout_floor(). Environment-agnostic: discovers or creates company, room, POS profile, warehouse; can complete the setup wizard headlessly.
- `restaurant/patches/` — multi-line source patches COPY'd + appended by the patch dockerfile (sed handles only one-liners).

## Iron rules (each learned the hard way)

1. **Verify fixes inside the image**, never by reading the dockerfile or a live container: `docker run --rm custom-erpnext:<tag> grep -c <fix> <file>`. Live-container seds evaporate on the next `compose up`; a sed that doesn't match exits 0 silently.
2. **Every patch step must be idempotent** — the patch dockerfile builds FROM its own output, so steps run again on every rebake. Guard appends with `grep -q` on a *distinctive* token: `grep -q restaurant_manage` once matched `restaurant_management` and silently skipped a patch.
3. **Site name must equal the public domain** (`SITE=pos.example.com`). The nginx template rewrites the `Origin` header to the site name and frappe's websocket auth requires `Host == Origin` — mismatch = "Invalid origin", dead realtime/kitchen display. For local work use `SITE=pos.localhost`.
4. Rebuilding from `apps-restaurant.json` alone produces an **unpatched** image — always follow with the patch dockerfile build. `deploy.sh` does both.
5. Commits: single-concern, author `moodykhalif23 <brian@sozuri.net>`, never add an AI co-author.

## v16 traps in the restaurant app (all patched here; details in restaurant/README.md)

- Doctype typo `Sales Taxes And Charges` + nonexistent column `amount` (→ `tax_amount`) in `table_order.py`.
- `aggregate()` crashes on `NULL` totals — None-guards added.
- Desk **page scripts run in a closure** in v16: the page's `var RM` never reaches `window`, but every class asset file reads `RM` globally → blank floor. Fixed with `window.RM = ...`.
- **v16 validates link fields before any doc hook fires** (both insert and save paths, see `frappe/model/document.py`) — `before_insert` is too late to fix up a link. Intercept by overriding the controller's `insert()`/`save()` (see `restaurant/patches/restaurant_booking_append.py`).
- `Restaurant Booking`/`Table Order` grant only `Restaurant Manager`/`Restaurant User` roles — System Manager alone gets Permission Error, which also aborts the floor/order-pad JS init. `seed()` grants the roles to staff users.
- `TableOrder.send` is a **@property** — attribute access fires kitchen dispatch; calling it throws `'dict' object is not callable` (a sync payload also lands on the instance as `.send`).
- POS Settings must be in "POS Invoice" mode (v16 defaults to Sales Invoice mode, blocking the app's billing); UOM `Nos` allows fractions for by-the-glass recipes (production: use a dedicated fractional UOM instead).

## Working on it

- Run seed functions via console (NOT `bench execute` — the module doesn't resolve there, and piped multi-line IPython mangles indentation):
  `echo 'exec(open("apps/restaurant_management/restaurant_management/demo_seed.py").read(), globals()); seed()' | docker compose exec -T backend bench --site <site> console`
  The script lives in the container only after `deploy.sh` copies it — re-copy after container recreation.
- The floor layout is data: each `Restaurant Object` carries `data_style` JSON (x/y/z/width/height). `layout_floor()` re-grids everything; origin starts at x=340 to clear v16's fixed desk sidebar.
- Inventory model: dishes are non-stock; 20 stocked ingredients + a BOM per dish; `backflush()` posts one Material Issue covering all un-flushed POS Invoices (tracked via a `RESTAURANT-BACKFLUSH:` tag in Stock Entry remarks). Run at day end or via cron.
- DB access: `docker compose exec -T backend bench --site <site> mariadb < file.sql`. MariaDB root password defaults to `123` (compose default) unless `DB_PASSWORD` is set.

## Live deployment

One production instance runs at frappe.ikobriq.com (site named exactly that) on a VPS shared with other services; Caddy fronts it → 127.0.0.1:8080. Its server-side clone of this repo tracks `origin/restaurant-pos`. Credentials are not in this repo — ask the owner.
