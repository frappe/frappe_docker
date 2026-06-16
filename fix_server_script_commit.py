"""
fix_server_script_commit.py
Removes frappe.db.commit() from the OnSite WIP warehouse server script.
In DocType Event server scripts, Frappe manages the transaction automatically —
calling frappe.db.commit() inside the script throws AttributeError in the sandbox.
Run via: bench --site frontend execute frappe.fix_server_script_commit.run
"""

import frappe

SCRIPT_NAME = "Furnitex - Auto Create OnSite WIP Warehouse"

FIXED_SCRIPT = """\
# Auto-fires after a new Project is saved
# Creates "{Project Name} - OnSite WIP" warehouse automatically

project_name   = doc.project_name or doc.name
company        = doc.company or "Furnitex"
abbr           = frappe.db.get_value("Company", company, "abbr") or "F"
wh_short_name  = project_name + " - OnSite WIP"
warehouse_name = wh_short_name + " - " + abbr

root_wh = frappe.db.get_value(
    "Warehouse",
    {"company": company, "is_group": 1},
    "name"
) or ("All Warehouses - " + abbr)

if not frappe.db.exists("Warehouse", warehouse_name):
    wh = frappe.get_doc({
        "doctype":          "Warehouse",
        "warehouse_name":   wh_short_name,
        "parent_warehouse": root_wh,
        "company":          company,
        "is_group":         0,
    })
    wh.flags.ignore_permissions = True
    wh.insert()
    # NOTE: no frappe.db.commit() here — Frappe handles the transaction
    frappe.msgprint(
        "OnSite WIP Warehouse created: <b>" + warehouse_name + "</b>",
        alert=True, indicator="green"
    )
"""


def run():
    frappe.set_user("Administrator")

    if not frappe.db.exists("Server Script", SCRIPT_NAME):
        print(f"  [WARN] Server Script '{SCRIPT_NAME}' not found — nothing to fix.")
        return

    doc = frappe.get_doc("Server Script", SCRIPT_NAME)
    doc.script = FIXED_SCRIPT
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()

    print(f"  [OK] Removed frappe.db.commit() from: {SCRIPT_NAME}")
    print("  Warehouse auto-creation will now work without AttributeError.")
