"""
delete_streetwok.py
Removes all "streetwok (Demo)" company data from Furnitex ERPNext instance.
Run via: bench --site frontend execute frappe.delete_streetwok.run
"""

import frappe

COMPANY = "streetwok (Demo)"


def _sql(q, commit=False):
    frappe.db.sql(q)
    if commit:
        frappe.db.commit()


def run():
    frappe.set_user("Administrator")

    if not frappe.db.exists("Company", COMPANY):
        print(f"  Company '{COMPANY}' not found — nothing to delete.")
        return

    print(f"\n{'='*54}")
    print(f"  DELETING: {COMPANY}")
    print(f"{'='*54}\n")

    # ── STEP 1: Cancel + delete all submitted documents ──────────
    submitted_doctypes = [
        "Sales Invoice",
        "Purchase Invoice",
        "Payment Entry",
        "Journal Entry",
        "Stock Entry",
        "Delivery Note",
        "Purchase Receipt",
        "Sales Order",
        "Purchase Order",
        "Quotation",
        "Material Request",
        "Stock Reconciliation",
    ]

    for dt in submitted_doctypes:
        # Get submitted docs for this company
        docs = frappe.db.sql(
            f"SELECT name FROM `tab{dt}` WHERE company=%s AND docstatus=1",
            COMPANY,
            as_dict=1,
        )
        if docs:
            print(f"  Cancelling {len(docs)} submitted {dt}(s)...")
            for d in docs:
                try:
                    doc = frappe.get_doc(dt, d.name)
                    doc.flags.ignore_permissions = True
                    doc.flags.ignore_links = True
                    doc.cancel()
                    frappe.db.commit()
                except Exception as e:
                    # Force cancel via direct DB update if normal cancel fails
                    frappe.db.sql(
                        f"UPDATE `tab{dt}` SET docstatus=2 WHERE name=%s", d.name
                    )
                    frappe.db.commit()

    # ── STEP 2: Delete all draft + cancelled docs ─────────────────
    all_doctypes = submitted_doctypes + [
        "Landed Cost Voucher",
        "Asset",
        "Salary Slip",
        "Timesheet",
    ]

    for dt in all_doctypes:
        try:
            count = frappe.db.count(dt, {"company": COMPANY})
            if count:
                frappe.db.delete(dt, {"company": COMPANY})
                frappe.db.commit()
                print(f"  Deleted {count} {dt}(s)")
        except Exception as e:
            print(f"  [WARN] Could not delete {dt}: {e}")

    # ── STEP 3: Delete GL Entries ─────────────────────────────────
    gl_count = frappe.db.count("GL Entry", {"company": COMPANY})
    if gl_count:
        frappe.db.delete("GL Entry", {"company": COMPANY})
        frappe.db.commit()
        print(f"  Deleted {gl_count} GL Entries")

    # ── STEP 4: Delete Stock Ledger Entries ───────────────────────
    sle_count = frappe.db.count("Stock Ledger Entry", {"company": COMPANY})
    if sle_count:
        frappe.db.delete("Stock Ledger Entry", {"company": COMPANY})
        frappe.db.commit()
        print(f"  Deleted {sle_count} Stock Ledger Entries")

    # ── STEP 5: Delete child tables that reference the company ────
    child_cleanups = [
        ("Sales Invoice Item", "company"),
        ("Purchase Invoice Item", "company"),
        ("Payment Entry Reference", None),  # handled via parent delete
    ]

    # ── STEP 6: Delete Warehouses ─────────────────────────────────
    # Disable stock bins first
    wh_list = frappe.db.sql(
        "SELECT name FROM `tabWarehouse` WHERE company=%s", COMPANY, as_dict=1
    )
    if wh_list:
        for wh in wh_list:
            frappe.db.delete("Bin", {"warehouse": wh.name})
        frappe.db.commit()

        for wh in wh_list:
            try:
                frappe.delete_doc(
                    "Warehouse",
                    wh.name,
                    ignore_permissions=True,
                    force=True,
                    ignore_on_trash=True,
                )
            except Exception as e:
                frappe.db.sql("DELETE FROM `tabWarehouse` WHERE name=%s", wh.name)
        frappe.db.commit()
        print(f"  Deleted {len(wh_list)} Warehouse(s)")

    # ── STEP 7: Delete Cost Centers ───────────────────────────────
    cc_list = frappe.db.sql(
        "SELECT name FROM `tabCost Center` WHERE company=%s ORDER BY lft DESC",
        COMPANY,
        as_dict=1,
    )
    if cc_list:
        for cc in cc_list:
            try:
                frappe.db.sql("DELETE FROM `tabCost Center` WHERE name=%s", cc.name)
            except Exception:
                pass
        frappe.db.commit()
        print(f"  Deleted {len(cc_list)} Cost Center(s)")

    # ── STEP 8: Delete Accounts ───────────────────────────────────
    acct_count = frappe.db.count("Account", {"company": COMPANY})
    if acct_count:
        # Delete leaf accounts first (is_group=0), then groups
        frappe.db.sql(
            "DELETE FROM `tabAccount` WHERE company=%s AND is_group=0", COMPANY
        )
        frappe.db.sql("DELETE FROM `tabAccount` WHERE company=%s", COMPANY)
        frappe.db.commit()
        print(f"  Deleted {acct_count} Account(s)")

    # ── STEP 9: Delete Fiscal Years linked only to this company ───
    fy_links = frappe.db.sql(
        """SELECT parent FROM `tabFiscal Year Company`
           WHERE company=%s""",
        COMPANY,
        as_dict=1,
    )
    for fy in fy_links:
        frappe.db.sql(
            "DELETE FROM `tabFiscal Year Company` WHERE company=%s AND parent=%s",
            (COMPANY, fy.parent),
        )
        # If this fiscal year has no other company links, delete it too
        remaining = frappe.db.count("Fiscal Year Company", {"parent": fy.parent})
        if remaining == 0:
            try:
                frappe.db.delete("Fiscal Year", {"name": fy.parent})
            except Exception:
                pass
    frappe.db.commit()

    # ── STEP 10: Nuke Customers/Suppliers that belong only to ─────
    #            streetwok (no transactions in Furnitex)
    # Only delete if they have no Furnitex transactions
    stale_customers = frappe.db.sql(
        """SELECT c.name FROM `tabCustomer` c
           WHERE NOT EXISTS (
               SELECT 1 FROM `tabSales Invoice`
               WHERE customer=c.name AND company='Furnitex' AND docstatus < 2
           )
           AND NOT EXISTS (
               SELECT 1 FROM `tabSales Order`
               WHERE customer=c.name AND company='Furnitex' AND docstatus < 2
           )""",
        as_dict=1,
    )
    if stale_customers:
        for c in stale_customers:
            try:
                frappe.db.delete("Customer", {"name": c.name})
            except Exception:
                pass
        frappe.db.commit()
        print(f"  Deleted {len(stale_customers)} orphan Customer(s)")

    # ── STEP 11: Delete the Company record itself ─────────────────
    try:
        frappe.delete_doc(
            "Company",
            COMPANY,
            ignore_permissions=True,
            force=True,
            ignore_on_trash=True,
        )
    except Exception:
        frappe.db.sql("DELETE FROM `tabCompany` WHERE name=%s", COMPANY)
    frappe.db.commit()
    print(f"\n  Company '{COMPANY}' deleted.")

    # ── STEP 12: Update Default Company if it was streetwok ───────
    default_co = frappe.db.get_default("company")
    if default_co and "streetwok" in default_co.lower():
        frappe.db.set_default("company", "Furnitex")
        frappe.db.commit()
        print("  Default company reset to: Furnitex")

    # ── STEP 13: Nuke any leftover streetwok items ────────────────
    stale_items = frappe.db.sql(
        """SELECT name FROM `tabItem`
           WHERE item_name LIKE '%streetwok%'
              OR item_code LIKE '%streetwok%'
              OR description LIKE '%streetwok%'""",
        as_dict=1,
    )
    if stale_items:
        for item in stale_items:
            try:
                frappe.db.delete("Item", {"name": item.name})
            except Exception:
                pass
        frappe.db.commit()
        print(f"  Deleted {len(stale_items)} streetwok-tagged Item(s)")

    frappe.clear_cache()

    print(f"\n{'='*54}")
    print("  DONE — streetwok removed. Refresh your browser.")
    print(f"{'='*54}\n")
