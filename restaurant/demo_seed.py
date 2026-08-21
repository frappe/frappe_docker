"""Restaurant POS bootstrap + demo seeder for restaurant_management on ERPNext v16.

Everything discovers or creates what it needs — safe to run on a virgin site.
Run inside `bench --site <site> console`:

    exec(open(".../demo_seed.py").read(), globals())
    bootstrap()        # completes the setup wizard headlessly if needed
    seed()             # menu, tables, kitchen+bar, customers, payments, register float
    seed_inventory()   # stocked ingredients + BOM recipe per dish
    simulate()         # a 10-order lunch service (6 paid, 4 live in the kitchen)
    backflush()        # consume ingredients for every un-flushed paid invoice
    sell_one()         # one full order: seat -> order -> kitchen -> delivered -> paid

Tunables via environment: COMPANY_NAME, COMPANY_ABBR, COUNTRY, CURRENCY, TIMEZONE.
"""
import json
import os
import uuid

import frappe

USER = "Administrator"

GROUPS = {
    "Starters": "Kitchen",
    "Main Course": "Kitchen",
    "Desserts": "Kitchen",
    "Bar & Beverages": "Bar",
}

MENU = [
    ("Samosa Platter", "Starters", 450),
    ("Chicken Wings", "Starters", 550),
    ("Soup of the Day", "Starters", 350),
    ("Nyama Choma Platter", "Main Course", 1200),
    ("Grilled Tilapia", "Main Course", 950),
    ("Chicken Biryani", "Main Course", 850),
    ("Beef Burger & Fries", "Main Course", 750),
    ("Veg Curry & Rice", "Main Course", 650),
    ("Chocolate Lava Cake", "Desserts", 500),
    ("Fruit Salad", "Desserts", 300),
    ("House Red Wine (Glass)", "Bar & Beverages", 600),
    ("House White Wine (Glass)", "Bar & Beverages", 600),
    ("Tusker Lager", "Bar & Beverages", 350),
    ("Fresh Passion Juice", "Bar & Beverages", 250),
    ("Bottled Water", "Bar & Beverages", 100),
]

RATES = {name: rate for name, _, rate in MENU}

CUSTOMERS = [
    "Walk-in Guest", "Amina Hassan", "John Kamau", "Grace Wanjiru",
    "David Ochieng", "Sarah Njeri", "Peter Otieno", "Mary Akinyi",
    "Hotel Sunrise Ltd",
]

STATUS_CHAIN = [("Sent", "Processing"), ("Processing", "Completed"), ("Completed", "Delivered")]

# ingredient -> (uom, opening qty, valuation rate)
INGREDIENTS = {
    "Chicken": ("Kg", 50, 350), "Beef Mince": ("Kg", 40, 450),
    "Goat Meat": ("Kg", 60, 550), "Tilapia Whole": ("Nos", 40, 400),
    "Rice": ("Kg", 100, 160), "Potatoes": ("Kg", 80, 90),
    "Flour": ("Kg", 50, 120), "Cooking Oil": ("Litre", 60, 300),
    "Burger Bun": ("Nos", 100, 30), "Salad Veg": ("Kg", 40, 150),
    "Fruit Mix": ("Kg", 30, 200), "Chocolate": ("Kg", 15, 800),
    "Cream": ("Litre", 20, 400), "Soup Base": ("Litre", 30, 250),
    "Spices": ("Kg", 10, 1200), "Red Wine Bottle": ("Nos", 48, 900),
    "White Wine Bottle": ("Nos", 48, 900), "Tusker Bottle": ("Nos", 120, 180),
    "Passion Concentrate": ("Litre", 25, 350), "Water Bottle": ("Nos", 200, 40),
}

# dish -> [(ingredient, qty consumed per unit sold)]
RECIPES = {
    "Samosa Platter": [("Flour", 0.2), ("Beef Mince", 0.15), ("Cooking Oil", 0.1), ("Spices", 0.02)],
    "Chicken Wings": [("Chicken", 0.4), ("Cooking Oil", 0.05), ("Spices", 0.02)],
    "Soup of the Day": [("Soup Base", 0.3), ("Salad Veg", 0.1)],
    "Nyama Choma Platter": [("Goat Meat", 0.5), ("Salad Veg", 0.1), ("Spices", 0.02)],
    "Grilled Tilapia": [("Tilapia Whole", 1), ("Cooking Oil", 0.05), ("Salad Veg", 0.1)],
    "Chicken Biryani": [("Chicken", 0.3), ("Rice", 0.25), ("Spices", 0.03), ("Cooking Oil", 0.05)],
    "Beef Burger & Fries": [("Beef Mince", 0.2), ("Burger Bun", 1), ("Potatoes", 0.3), ("Cooking Oil", 0.1)],
    "Veg Curry & Rice": [("Salad Veg", 0.3), ("Rice", 0.25), ("Spices", 0.03)],
    "Chocolate Lava Cake": [("Chocolate", 0.15), ("Flour", 0.1), ("Cream", 0.1)],
    "Fruit Salad": [("Fruit Mix", 0.3)],
    "House Red Wine (Glass)": [("Red Wine Bottle", 0.2)],
    "House White Wine (Glass)": [("White Wine Bottle", 0.2)],
    "Tusker Lager": [("Tusker Bottle", 1)],
    "Fresh Passion Juice": [("Passion Concentrate", 0.1)],
    "Bottled Water": [("Water Bottle", 1)],
}

BACKFLUSH_TAG = "RESTAURANT-BACKFLUSH:"


# ---------------- context discovery ----------------

def company():
    c = (os.environ.get("COMPANY_NAME")
         or frappe.defaults.get_global_default("company")
         or frappe.db.get_value("Company", {}, "name"))
    if not c:
        frappe.throw("No Company found — run bootstrap() first")
    return c


def currency():
    return frappe.db.get_value("Company", company(), "default_currency")


def warehouse():
    abbr = frappe.db.get_value("Company", company(), "abbr")
    return f"Stores - {abbr}"


def pos_profile():
    name = frappe.db.get_value("POS Profile", {"company": company(), "disabled": 0})
    if name:
        return name
    prof = frappe.get_doc({
        "doctype": "POS Profile", "name": "Restaurant",
        "company": company(), "warehouse": warehouse(),
        "currency": currency(), "update_stock": 1,
        "customer": _ensure_customer("Walk-in Guest"),
        "selling_price_list": frappe.db.get_value("Price List", {"enabled": 1, "selling": 1}),
        "payments": [{"mode_of_payment": "Cash", "default": 1}],
        "applicable_for_users": [],
    })
    prof.insert(ignore_permissions=True)
    frappe.db.commit()
    return prof.name


def room():
    r = frappe.db.get_value("Restaurant Object", {"type": "Room"}, "name")
    if r:
        return r
    doc = frappe.new_doc("Restaurant Object")
    doc.type = "Room"
    doc.description = "Main Hall"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return doc.name


def bootstrap():
    """Complete the ERPNext setup wizard headlessly if this is a virgin site."""
    frappe.set_user(USER)
    if frappe.db.get_value("Company", {}, "name"):
        print("BOOTSTRAP: company exists, nothing to do")
        return
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
    setup_complete({
        "language": "English",
        "country": os.environ.get("COUNTRY", "Kenya"),
        "timezone": os.environ.get("TIMEZONE", "Africa/Nairobi"),
        "currency": os.environ.get("CURRENCY", "KES"),
        "full_name": "Administrator",
        "email": "admin@example.com",
        "company_name": os.environ.get("COMPANY_NAME", "Demo Restaurant"),
        "company_abbr": os.environ.get("COMPANY_ABBR", "DR"),
        "chart_of_accounts": "Standard",
        "fy_start_date": frappe.utils.get_year_start(frappe.utils.today()),
        "fy_end_date": frappe.utils.get_year_ending(frappe.utils.today()),
        "setup_demo": 0,
    })
    frappe.db.commit()
    print("BOOTSTRAP OK —", company())


# ---------------- masters ----------------

def _ensure_item_group(name):
    if not frappe.db.exists("Item Group", name):
        frappe.get_doc({
            "doctype": "Item Group", "item_group_name": name,
            "parent_item_group": "All Item Groups",
        }).insert(ignore_permissions=True)


def _ensure_item(name, group, rate=None, stock=False, uom="Nos"):
    if not frappe.db.exists("Item", name):
        frappe.get_doc({
            "doctype": "Item", "item_code": name, "item_name": name,
            "item_group": group, "stock_uom": uom,
            "is_stock_item": 1 if stock else 0,
            "is_sales_item": 0 if stock else 1,
        }).insert(ignore_permissions=True)
    if rate is None:
        return
    for pl in frappe.get_all("Price List", filters={"enabled": 1}, pluck="name"):
        if not frappe.db.exists("Item Price", {"item_code": name, "price_list": pl}):
            frappe.get_doc({
                "doctype": "Item Price", "item_code": name, "price_list": pl,
                "price_list_rate": rate, "currency": currency(), "selling": 1,
            }).insert(ignore_permissions=True)


def _ensure_customer(name):
    if not frappe.db.exists("Customer", {"customer_name": name}):
        frappe.get_doc({
            "doctype": "Customer", "customer_name": name,
            "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}),
            "territory": frappe.db.get_value("Territory", {"is_group": 0}),
        }).insert(ignore_permissions=True)
    return frappe.db.get_value("Customer", {"customer_name": name})


def _configure_pc(pc_name, groups):
    pc = frappe.get_doc("Restaurant Object", pc_name)
    pc.production_center_group = []
    for g in groups:
        pc.append("production_center_group", {"item_group": g})
    pc.status_managed = []
    for cur, nxt in STATUS_CHAIN:
        pc.append("status_managed", {"status_managed": cur, "next_status": nxt})
    pc.save(ignore_permissions=True)


def _ensure_pc(label, groups):
    name = frappe.db.get_value("Restaurant Object",
                               {"type": "Production Center", "description": label}, "name")
    if not name:
        r = frappe.get_doc("Restaurant Object", room())
        r.add_object("Production Center")
        name = frappe.get_all("Restaurant Object", filters={"type": "Production Center"},
                              order_by="creation desc", pluck="name")[0]
        frappe.db.set_value("Restaurant Object", name, "description", label)
    _configure_pc(name, groups)


def seed():
    frappe.set_user(USER)

    frappe.db.set_value("POS Settings", None, "invoice_type", "POS Invoice")
    frappe.db.set_value("UOM", "Nos", "must_be_whole_number", 0)

    for g in GROUPS:
        _ensure_item_group(g)
    for name, group, rate in MENU:
        _ensure_item(name, group, rate)

    menu_name = frappe.db.get_value("Restaurant Menu", {}, "name")
    if not menu_name:
        m = frappe.new_doc("Restaurant Menu")
        m.company = company()
        m.save(ignore_permissions=True)
        menu_name = m.name
    menu = frappe.get_doc("Restaurant Menu", menu_name)
    child_field = next(f.fieldname for f in frappe.get_meta("Restaurant Menu").get_table_fields()
                       if f.options == "Restaurant Menu Item")
    existing = {r.item for r in menu.get(child_field)}
    for name, group, rate in MENU:
        if name not in existing:
            menu.append(child_field, {"item": name, "item_group": group, "status": 1})
    menu.save(ignore_permissions=True)

    _ensure_pc("Kitchen", [g for g, pc in GROUPS.items() if pc == "Kitchen"])
    _ensure_pc("Bar", [g for g, pc in GROUPS.items() if pc == "Bar"])

    r = frappe.get_doc("Restaurant Object", room())
    while frappe.db.count("Restaurant Object", {"room": r.name, "type": "Table"}) < 6:
        r.add_object("Table")

    for c in CUSTOMERS:
        _ensure_customer(c)

    prof_name = pos_profile()
    if not frappe.db.exists("Mode of Payment", "M-Pesa"):
        cash_acc = frappe.db.get_value(
            "Mode of Payment Account", {"parent": "Cash", "company": company()}, "default_account")
        frappe.get_doc({
            "doctype": "Mode of Payment", "mode_of_payment": "M-Pesa", "type": "Bank",
            "accounts": [{"company": company(), "default_account": cash_acc}],
        }).insert(ignore_permissions=True)
    prof = frappe.get_doc("POS Profile", prof_name)
    if "M-Pesa" not in [p.mode_of_payment for p in prof.payments]:
        prof.append("payments", {"mode_of_payment": "M-Pesa"})
        prof.save(ignore_permissions=True)

    if not frappe.db.exists("POS Opening Entry", {"pos_profile": prof_name, "status": "Open"}):
        op = frappe.get_doc({
            "doctype": "POS Opening Entry", "company": company(),
            "pos_profile": prof_name, "user": frappe.session.user,
            "period_start_date": frappe.utils.now_datetime(),
            "posting_date": frappe.utils.today(),
            "balance_details": [{"mode_of_payment": "Cash", "opening_amount": 5000}],
        })
        op.insert(ignore_permissions=True)
        op.submit()

    frappe.db.commit()
    layout_floor()
    print("SEED OK — tables:", frappe.db.count("Restaurant Object", {"type": "Table"}),
          "| menu rows:", frappe.db.count("Restaurant Menu Item"),
          "| customers:", frappe.db.count("Customer"))


# ---------------- service simulation ----------------

def _entry(item_code, qty, rate, notes=""):
    return {
        "identifier": str(uuid.uuid4()),
        "item_code": item_code, "qty": qty,
        "rate": rate, "price_list_rate": rate,
        "discount_percentage": 0, "status": "",
        "notes": notes, "ordered_time": None,
        "has_batch_no": 0, "batch_no": "",
        "has_serial_no": 0, "serial_no": "",
        "sub_items": "[]", "is_customizable": 0,
    }


# (customer, table_idx, items[(name, qty, note)], final per-item status, payment mode or None)
SERVICE = [
    ("Amina Hassan", 0, [("Samosa Platter", 1, ""), ("Nyama Choma Platter", 1, "medium rare"), ("House Red Wine (Glass)", 2, "")], "Delivered", "M-Pesa"),
    ("John Kamau", 1, [("Chicken Wings", 1, ""), ("Chicken Biryani", 2, ""), ("Grilled Tilapia", 1, ""), ("Fresh Passion Juice", 2, ""), ("House White Wine (Glass)", 1, "")], "Delivered", "Cash"),
    ("Grace Wanjiru", 2, [("Soup of the Day", 1, ""), ("Veg Curry & Rice", 1, "extra spicy"), ("Bottled Water", 1, "")], "Delivered", "M-Pesa"),
    ("Hotel Sunrise Ltd", 3, [("Samosa Platter", 2, ""), ("Grilled Tilapia", 2, ""), ("Beef Burger & Fries", 1, "no onions"), ("Chocolate Lava Cake", 2, ""), ("House Red Wine (Glass)", 3, "")], "Delivered", "M-Pesa"),
    ("David Ochieng", 0, [("Beef Burger & Fries", 1, ""), ("Tusker Lager", 1, "")], "Delivered", "Cash"),
    ("Walk-in Guest", 1, [("Chicken Biryani", 1, ""), ("Fresh Passion Juice", 1, "")], "Delivered", "Cash"),
    ("Sarah Njeri", 4, [("Grilled Tilapia", 1, "lemon on the side"), ("House White Wine (Glass)", 1, "")], "Completed", None),
    ("Peter Otieno", 5, [("Chicken Wings", 1, ""), ("Nyama Choma Platter", 1, ""), ("Tusker Lager", 2, "")], "Processing", None),
    ("Walk-in Guest", 2, [("Soup of the Day", 1, ""), ("Beef Burger & Fries", 1, "")], "Sent", None),
    ("Mary Akinyi", 3, [("House Red Wine (Glass)", 1, ""), ("Fruit Salad", 1, "")], "Attending", None),
]

STEPS = {"Attending": 0, "Sent": 1, "Processing": 2, "Completed": 3, "Delivered": 4}


def _pc_for(item_code):
    group = frappe.db.get_value("Item", item_code, "item_group")
    target = GROUPS.get(group, "Kitchen")
    return frappe.db.get_value("Restaurant Object",
                               {"type": "Production Center", "description": target}, "name")


def _run_order(table_name, cust_name, dishes, final, pay_mode):
    customer = frappe.db.get_value("Customer", {"customer_name": cust_name})
    frappe.db.set_value("Restaurant Object", table_name, "customer", customer)
    table = frappe.get_doc("Restaurant Object", table_name)

    order = table.add_order()
    cls = type(order)
    entries = [_entry(n, q, RATES[n], note) for n, q, note in dishes]
    for e in entries:
        cls.push_item(order, e)
    order.reload()

    steps_target = STEPS[final]
    if steps_target >= 1:
        cls.send.fget(order)  # .send is a @property in the app; access fires dispatch
        order.reload()
    for e in entries:
        pc = frappe.get_doc("Restaurant Object", _pc_for(e["item_code"]))
        for _ in range(max(0, steps_target - 1)):
            pc.set_status_command(e["identifier"])

    invoice = None
    if pay_mode:
        order.reload()
        draft_entries = {i.identifier: i.as_dict() for i in order.entry_items}
        draft = cls.get_invoice(order, draft_entries, False)
        res = cls.make_invoice(order, {pay_mode: draft.grand_total})
        invoice = res.get("invoice_name")
        frappe.db.set_value("Restaurant Object", table_name, "customer", None)
    frappe.db.commit()
    return order.name, invoice


def simulate():
    frappe.set_user(USER)
    tables = frappe.get_all("Restaurant Object", filters={"room": room(), "type": "Table"},
                            order_by="creation", pluck="name")
    results = []
    for cust_name, t_idx, dishes, final, pay_mode in SERVICE:
        name, invoice = _run_order(tables[t_idx % len(tables)], cust_name, dishes, final, pay_mode)
        results.append((name, cust_name, final, pay_mode or "-", invoice or "-"))

    for cust, people, hours_from_now in [("Hotel Sunrise Ltd", 8, 6), ("Amina Hassan", 2, 24)]:
        try:
            b = frappe.new_doc("Restaurant Booking")
            b.customer = frappe.db.get_value("Customer", {"customer_name": cust})
            b.no_of_people = people
            b.reservation_time = frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=hours_from_now)
            b.reservation_end_time = frappe.utils.add_to_date(b.reservation_time, hours=2)
            b.insert(ignore_permissions=True)
        except Exception as e:
            print("booking skipped:", str(e)[:80])
    frappe.db.commit()

    print("SIMULATE OK")
    for r in results:
        print(*r)


def sell_one(customer="Walk-in Guest", dishes=None, pay="Cash"):
    """One complete order on a free table: seat -> order -> kitchen -> delivered -> paid."""
    frappe.set_user(USER)
    dishes = dishes or [("Grilled Tilapia", 1, ""), ("House Red Wine (Glass)", 1, "")]
    table_name = next(
        t for t in frappe.get_all("Restaurant Object",
                                  filters={"room": room(), "type": "Table"}, pluck="name")
        if not frappe.db.count("Table Order",
                               {"table": t, "status": ("not in", ["Invoiced", "Cancelled", "Closed"])}))
    name, invoice = _run_order(table_name, customer, dishes, "Delivered", pay)
    print("SOLD", name, "->", invoice)
    return invoice


# ---------------- inventory: ingredients, recipes, back-flush ----------------

def seed_inventory():
    frappe.set_user(USER)
    _ensure_item_group("Ingredients")

    for name, (uom, qty, rate) in INGREDIENTS.items():
        _ensure_item(name, "Ingredients", stock=True, uom=uom)

    opening = [n for n in INGREDIENTS
               if not frappe.db.get_value("Bin", {"item_code": n, "warehouse": warehouse()}, "actual_qty")]
    if opening:
        se = frappe.get_doc({
            "doctype": "Stock Entry", "stock_entry_type": "Material Receipt",
            "company": company(),
            "items": [{
                "item_code": n, "qty": INGREDIENTS[n][1],
                "t_warehouse": warehouse(), "basic_rate": INGREDIENTS[n][2],
            } for n in opening],
        })
        se.insert(ignore_permissions=True)
        se.submit()
        print("opening stock:", se.name, len(opening), "items")

    boms = 0
    for dish, parts in RECIPES.items():
        if frappe.db.exists("BOM", {"item": dish, "docstatus": 1}):
            continue
        try:
            bom = frappe.get_doc({
                "doctype": "BOM", "item": dish, "company": company(),
                "quantity": 1, "is_active": 1, "is_default": 1,
                "items": [{"item_code": ing, "qty": q, "uom": INGREDIENTS[ing][0],
                           "rate": INGREDIENTS[ing][2]} for ing, q in parts],
            })
            bom.insert(ignore_permissions=True)
            bom.submit()
            boms += 1
        except Exception as e:
            print("BOM skipped for", dish, "->", str(e)[:90])
    frappe.db.commit()
    print("SEED_INVENTORY OK — BOMs:", boms)


def layout_floor():
    """Arrange the floor: tables in a grid, Kitchen and Bar as side stations."""
    frappe.set_user(USER)
    tables = frappe.get_all("Restaurant Object", filters={"room": room(), "type": "Table"},
                            order_by="creation", pluck="name")
    colors = ["#1a4469", "#2e844e", "#97264f", "#505a62", "#1579d0", "#2d401d"]

    def style(x, y, z, w, h):
        return f'{{"x":"{x}","y":"{y}","z-index":"{z}","width":"{w}px","height":"{h}px"}}'

    for i, t in enumerate(tables):
        frappe.db.set_value("Restaurant Object", t, {
            "data_style": style(60 + (i % 3) * 260, 90 + (i // 3) * 220, 60 + i, 200, 130),
            "description": f"Table {i + 1}",
            "shape": "Square",
            "color": colors[i % len(colors)],
        })
    for pc in frappe.get_all("Restaurant Object", filters={"type": "Production Center"},
                             fields=["name", "description"]):
        frappe.db.set_value("Restaurant Object", pc.name, {
            "data_style": style(880, 90 if pc.description == "Kitchen" else 320, 90, 280, 160),
            "color": "#97264f" if pc.description == "Kitchen" else "#1a4469",
        })
    frappe.db.commit()
    print("LAYOUT OK —", len(tables), "tables arranged")


def backflush():
    """Consume ingredients for every submitted POS Invoice not yet back-flushed.
    Run at end of day (or after each service) — the restaurant's stock burn."""
    frappe.set_user(USER)
    done = set()
    for r in frappe.get_all("Stock Entry", filters={"docstatus": 1}, fields=["name", "remarks"]):
        if r.remarks and BACKFLUSH_TAG in r.remarks:
            done.update(r.remarks.split(BACKFLUSH_TAG, 1)[1].strip().split(","))

    pending = [n for n in frappe.get_all("POS Invoice", filters={"docstatus": 1}, pluck="name")
               if n not in done]
    if not pending:
        print("BACKFLUSH: nothing pending")
        return

    need = {}
    for inv in pending:
        for it in frappe.get_all("POS Invoice Item", filters={"parent": inv},
                                 fields=["item_code", "qty"]):
            for ing, q in RECIPES.get(it.item_code, []):
                need[ing] = need.get(ing, 0) + q * it.qty
    if not need:
        print("BACKFLUSH: no recipe items in pending invoices")
        return

    se = frappe.get_doc({
        "doctype": "Stock Entry", "stock_entry_type": "Material Issue",
        "company": company(),
        "remarks": f"Kitchen consumption for {len(pending)} invoices {BACKFLUSH_TAG} {','.join(pending)}",
        "items": [{"item_code": ing, "qty": round(q, 3), "s_warehouse": warehouse()}
                  for ing, q in sorted(need.items())],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    frappe.db.commit()
    print(f"BACKFLUSH OK — {se.name} covers {len(pending)} invoices")
    for ing, q in sorted(need.items()):
        bal = frappe.db.get_value("Bin", {"item_code": ing, "warehouse": warehouse()}, "actual_qty")
        print(f"  {ing}: -{round(q, 3)} -> {bal} {INGREDIENTS[ing][0]}")
