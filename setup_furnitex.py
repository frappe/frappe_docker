"""
Furnitex ERPNext v16 Setup Script
Run inside container via:
  bench --site frontend execute setup_furnitex.run_all
Or directly:
  python /home/frappe/setup_furnitex.py
"""

import frappe
import frappe.defaults


COMPANY   = "Furnitex"
SITE      = "frontend"
ABBR      = None   # resolved at runtime via get_abbr()

def get_abbr():
    global ABBR
    if not ABBR:
        ABBR = frappe.db.get_value("Company", COMPANY, "abbr") or "F"
    return ABBR


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def exists(doctype, name):
    return frappe.db.exists(doctype, name)

def ok(msg):
    print(f"  [OK]   {msg}")

def skip(msg):
    print(f"  [SKIP] {msg}")

def warn(msg):
    print(f"  [WARN] {msg}")


# ─────────────────────────────────────────────────────────────
# 1. UOMs
# ─────────────────────────────────────────────────────────────

def create_uoms():
    print("\n[1/9] Creating UOMs...")
    uoms = [
        ("SqFt",   0),
        ("Rft",    0),
        ("Bag",    1),
        ("Sheet",  1),
        ("Bundle", 1),
        ("Cubic Ft", 0),
    ]
    for uom_name, whole in uoms:
        if not exists("UOM", uom_name):
            d = frappe.get_doc({
                "doctype": "UOM",
                "uom_name": uom_name,
                "must_be_whole_number": whole,
            })
            d.flags.ignore_permissions = True
            d.flags.ignore_mandatory   = True
            d.insert()
            ok(f"UOM: {uom_name}")
        else:
            skip(f"UOM: {uom_name}")
    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 2. ITEM GROUPS
# ─────────────────────────────────────────────────────────────

def create_item_groups():
    print("\n[2/9] Creating Item Groups...")
    groups = [
        ("Raw Materials - Furnitex",  "All Item Groups"),
        ("Plywood & Board",           "Raw Materials - Furnitex"),
        ("Laminates & Veneer",        "Raw Materials - Furnitex"),
        ("Hardware & Fittings",       "Raw Materials - Furnitex"),
        ("Civil & Surface Materials", "Raw Materials - Furnitex"),
        ("Execution Services",        "All Item Groups"),
        ("Loose Furniture",           "All Item Groups"),
    ]
    for name, parent in groups:
        if not exists("Item Group", name):
            d = frappe.get_doc({
                "doctype":           "Item Group",
                "item_group_name":   name,
                "parent_item_group": parent,
                "is_group":          0,
            })
            d.flags.ignore_permissions = True
            d.insert()
            ok(f"Item Group: {name}")
        else:
            skip(f"Item Group: {name}")
    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 3. SUPPLIER GROUPS
# ─────────────────────────────────────────────────────────────

def create_supplier_groups():
    print("\n[3/9] Creating Supplier Groups...")
    groups = [
        ("Local Market Vendor (Unregistered)", "All Supplier Groups"),
        ("GST Registered Vendor",              "All Supplier Groups"),
        ("Labour Contractor",                  "All Supplier Groups"),
    ]
    for name, parent in groups:
        if not exists("Supplier Group", name):
            d = frappe.get_doc({
                "doctype":               "Supplier Group",
                "supplier_group_name":   name,
                "parent_supplier_group": parent,
            })
            d.flags.ignore_permissions = True
            d.insert()
            ok(f"Supplier Group: {name}")
        else:
            skip(f"Supplier Group: {name}")
    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 4. WAREHOUSES
# ─────────────────────────────────────────────────────────────

def create_warehouses():
    print("\n[4/9] Creating Warehouses...")
    abbr = get_abbr()

    # Find the company's root warehouse group
    root_wh = frappe.db.get_value(
        "Warehouse",
        {"company": COMPANY, "is_group": 1},
        "name"
    )
    if not root_wh:
        root_wh = f"All Warehouses - {abbr}"

    warehouses = [
        ("Main Store",     root_wh, 0),
        ("Rejected Stock", root_wh, 0),
    ]
    for w_short, parent, is_group in warehouses:
        # ERPNext appends company abbr: "Main Store - F"
        w_full = f"{w_short} - {abbr}"
        if not exists("Warehouse", w_full):
            d = frappe.get_doc({
                "doctype":          "Warehouse",
                "warehouse_name":   w_short,
                "parent_warehouse": parent,
                "company":          COMPANY,
                "is_group":         is_group,
            })
            d.flags.ignore_permissions = True
            d.insert()
            ok(f"Warehouse: {w_full}")
        else:
            skip(f"Warehouse: {w_full}")
    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 5. TAX TEMPLATES
# ─────────────────────────────────────────────────────────────

def _find_account(account_name_fragment, root_type=None, account_type=None):
    """Find an account by partial name match under the company."""
    filters = {"company": COMPANY, "is_group": 0}
    if root_type:
        filters["root_type"] = root_type
    if account_type:
        filters["account_type"] = account_type

    # Try exact name match first
    result = frappe.db.get_value("Account",
        dict(filters, account_name=account_name_fragment), "name")
    if result:
        return result

    # Try LIKE match
    like_pattern = f"%{account_name_fragment}%"
    result = frappe.db.sql(
        """SELECT name FROM `tabAccount`
           WHERE company=%s AND is_group=0
             AND account_name LIKE %s
           LIMIT 1""",
        (COMPANY, like_pattern), as_dict=0
    )
    return result[0][0] if result else None


def create_tax_templates():
    print("\n[5/9] Creating Tax Templates...")

    # ── No GST (URD Purchase) ──
    urd = "No GST - URD Purchase"
    if not exists("Purchase Taxes and Charges Template", urd):
        d = frappe.get_doc({
            "doctype":    "Purchase Taxes and Charges Template",
            "title":      urd,
            "company":    COMPANY,
            "is_default": 0,
            "taxes":      [],   # zero rows = zero tax, clean COGS booking
        })
        d.flags.ignore_permissions = True
        d.insert()
        ok(f"Purchase Tax Template: {urd}")
    else:
        skip(f"Purchase Tax Template: {urd}")

    # ── GST 18% Purchase ──
    gst18_p = "GST 18% - Purchase"
    if not exists("Purchase Taxes and Charges Template", gst18_p):
        cgst = _find_account("CGST")
        sgst = _find_account("SGST")
        taxes = []
        if cgst:
            taxes.append({"charge_type": "On Net Total", "account_head": cgst, "rate": 9, "description": "CGST @ 9%"})
        if sgst:
            taxes.append({"charge_type": "On Net Total", "account_head": sgst, "rate": 9, "description": "SGST @ 9%"})
        d = frappe.get_doc({
            "doctype":    "Purchase Taxes and Charges Template",
            "title":      gst18_p,
            "company":    COMPANY,
            "is_default": 0,
            "taxes":      taxes,
        })
        d.flags.ignore_permissions = True
        d.insert()
        ok(f"Purchase Tax Template: {gst18_p}" + (" (no accounts found, empty)" if not taxes else ""))
    else:
        skip(f"Purchase Tax Template: {gst18_p}")

    # ── GST 18% Sales ──
    gst18_s = "GST 18% - Sales"
    if not exists("Sales Taxes and Charges Template", gst18_s):
        cgst = _find_account("CGST")
        sgst = _find_account("SGST")
        taxes = []
        if cgst:
            taxes.append({"charge_type": "On Net Total", "account_head": cgst, "rate": 9, "description": "CGST @ 9%"})
        if sgst:
            taxes.append({"charge_type": "On Net Total", "account_head": sgst, "rate": 9, "description": "SGST @ 9%"})
        d = frappe.get_doc({
            "doctype":    "Sales Taxes and Charges Template",
            "title":      gst18_s,
            "company":    COMPANY,
            "is_default": 0,
            "taxes":      taxes,
        })
        d.flags.ignore_permissions = True
        d.insert()
        ok(f"Sales Tax Template: {gst18_s}" + (" (no accounts found, empty)" if not taxes else ""))
    else:
        skip(f"Sales Tax Template: {gst18_s}")

    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 6. SERVICE ITEMS (Non-stock billing items)
# ─────────────────────────────────────────────────────────────

def create_service_items():
    print("\n[6/9] Creating Service Items...")

    income_acct = _find_account("Sales", root_type="Income") or \
                  _find_account("Service", root_type="Income")

    items = [
        # (code, name, uom, description)
        ("SVC-FC-EXEC",    "False Ceiling Execution",         "SqFt",  "Labour + material for false ceiling. Bill per SqFt OR as lumpsum."),
        ("SVC-WAR-LAM",    "Laminate Wardrobe Fabrication",   "SqFt",  "Laminate wardrobe fabrication per SqFt."),
        ("SVC-KIT-EXEC",   "Modular Kitchen Execution",       "SqFt",  "Modular kitchen fabrication and installation."),
        ("SVC-FLOOR",      "Flooring Execution",              "SqFt",  "Vinyl/Wood/Tile flooring supply and installation."),
        ("SVC-LUMP",       "Lumpsum Contract Work",           "Nos",   "Fixed-price lumpsum milestone. Change qty to 1 always."),
        ("SVC-DESIGN",     "Interior Design Consultation",    "Nos",   "Design + drawing fee — lumpsum."),
        ("SVC-CONVEY",     "Site Conveyance & Transport",     "Nos",   "Transport charges to/from site."),
        ("SVC-LABOUR",     "Direct Site Labour",              "Nos",   "Daily-wage labour charges."),
        ("SVC-ELECTRIC",   "Electrical Work Execution",       "Nos",   "Electrical points, wiring, fitting."),
        ("SVC-PAINT",      "Painting & Polish Execution",     "SqFt",  "Wall painting / wood polish per SqFt."),
    ]

    for code, name, uom, desc in items:
        if not exists("Item", code):
            d_dict = {
                "doctype":          "Item",
                "item_code":        code,
                "item_name":        name,
                "item_group":       "Execution Services",
                "description":      desc,
                "stock_uom":        uom,
                "sales_uom":        uom,
                "is_stock_item":    0,
                "is_purchase_item": 0,
                "is_sales_item":    1,
                "standard_rate":    0,
            }
            if income_acct:
                d_dict["item_defaults"] = [{
                    "company":        COMPANY,
                    "income_account": income_acct,
                }]
            d = frappe.get_doc(d_dict)
            d.flags.ignore_permissions = True
            d.insert()
            ok(f"Service Item: {code} [{uom}]")
        else:
            skip(f"Service Item: {code}")

    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 7. RAW MATERIAL ITEMS (Stock items)
# ─────────────────────────────────────────────────────────────

def create_raw_material_items():
    print("\n[7/9] Creating Raw Material Items...")

    cogs_acct = (_find_account("Cost of Goods Sold", root_type="Expense") or
                 _find_account("Stock Expenses",      root_type="Expense") or
                 _find_account("Expenses Included",   root_type="Expense"))

    default_wh = f"Main Store - {get_abbr()}"
    if not exists("Warehouse", default_wh):
        default_wh = frappe.db.get_value(
            "Warehouse", {"company": COMPANY, "is_group": 0}, "name"
        )

    items = [
        # (code, name, uom, group)
        ("RM-PLY-19MM",  "Plywood 19mm BWR 8x4",        "Sheet",   "Plywood & Board"),
        ("RM-PLY-12MM",  "Plywood 12mm BWR 8x4",        "Sheet",   "Plywood & Board"),
        ("RM-PLY-6MM",   "Plywood 6mm 8x4",             "Sheet",   "Plywood & Board"),
        ("RM-MDF-18MM",  "MDF Board 18mm 8x4",          "Sheet",   "Plywood & Board"),
        ("RM-HDF-3MM",   "HDF 3mm 8x4",                 "Sheet",   "Plywood & Board"),
        ("RM-LAM-1MM",   "Laminate Sheet 1mm 8x4",      "Sheet",   "Laminates & Veneer"),
        ("RM-VEN-NAT",   "Veneer Sheet Natural Wood",   "Sheet",   "Laminates & Veneer"),
        ("RM-LAM-ACRY",  "Acrylic Laminate Sheet",      "Sheet",   "Laminates & Veneer"),
        ("RM-HW-HINGE",  "Concealed Hinge (pair)",      "Nos",     "Hardware & Fittings"),
        ("RM-HW-CHAN18", "Drawer Channel 18 inch",      "Nos",     "Hardware & Fittings"),
        ("RM-HW-CHAN24", "Drawer Channel 24 inch",      "Nos",     "Hardware & Fittings"),
        ("RM-HW-HANDLE", "Cabinet Handle",              "Nos",     "Hardware & Fittings"),
        ("RM-HW-LOCK",   "Drawer Lock",                 "Nos",     "Hardware & Fittings"),
        ("RM-HW-SCREW",  "Wood Screw Assorted",         "Bundle",  "Hardware & Fittings"),
        ("RM-CIV-CEM",   "OPC Cement 53 Grade",         "Bag",     "Civil & Surface Materials"),
        ("RM-CIV-PUTTY", "Wall Putty White",            "Bag",     "Civil & Surface Materials"),
        ("RM-CIV-PRIMER","Primer Interior",             "Nos",     "Civil & Surface Materials"),
        ("RM-CIV-GYPS",  "Gypsum Board 8x4 12.5mm",    "Sheet",   "Civil & Surface Materials"),
        ("RM-CIV-GYPS-C","Gypsum Cornice / Grid",      "Rft",     "Civil & Surface Materials"),
    ]

    for code, name, uom, group in items:
        if not exists("Item", code):
            d_dict = {
                "doctype":           "Item",
                "item_code":         code,
                "item_name":         name,
                "item_group":        group,
                "stock_uom":         uom,
                "is_stock_item":     1,
                "is_purchase_item":  1,
                "is_sales_item":     0,
                "valuation_method":  "FIFO",
            }
            defaults = {"company": COMPANY}
            if default_wh:
                defaults["default_warehouse"] = default_wh
            if cogs_acct:
                defaults["expense_account"] = cogs_acct
            d_dict["item_defaults"] = [defaults]

            d = frappe.get_doc(d_dict)
            d.flags.ignore_permissions = True
            d.insert()
            ok(f"Raw Material: {code} [{uom}]")
        else:
            skip(f"Raw Material: {code}")

    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 8. SAMPLE SUPPLIERS
# ─────────────────────────────────────────────────────────────

def create_suppliers():
    print("\n[8/9] Creating Sample Suppliers...")

    suppliers = [
        # (name, group, gst_category)
        ("Local Hardware Market - Kolkata",   "Local Market Vendor (Unregistered)", "Unregistered"),
        ("Burrabazar Plywood Supplier",        "Local Market Vendor (Unregistered)", "Unregistered"),
        ("Fancy Laminates - Howrah",           "Local Market Vendor (Unregistered)", "Unregistered"),
        ("Modern Furniture Hardware - BBD Bag","Local Market Vendor (Unregistered)", "Unregistered"),
        ("Registered Hardware Supplier Ltd",   "GST Registered Vendor",             "Registered Regular"),
        ("Site Labour Contractor - Ramesh",    "Labour Contractor",                  "Unregistered"),
    ]

    for name, group, gst_cat in suppliers:
        if not exists("Supplier", name):
            d = frappe.get_doc({
                "doctype":          "Supplier",
                "supplier_name":    name,
                "supplier_group":   group,
                "country":          "India",
                "gst_category":     gst_cat,
                "default_currency": "INR",
            })
            d.flags.ignore_permissions = True
            d.insert()
            ok(f"Supplier: {name} [{gst_cat}]")
        else:
            skip(f"Supplier: {name}")

    frappe.db.commit()

    # Set URD tax default on all Unregistered suppliers
    urd_template = "No GST - URD Purchase"
    if exists("Purchase Taxes and Charges Template", urd_template):
        urd_suppliers = frappe.db.sql(
            """SELECT name FROM `tabSupplier`
               WHERE supplier_group = 'Local Market Vendor (Unregistered)'""",
            as_dict=1
        )
        for s in urd_suppliers:
            frappe.db.set_value(
                "Supplier", s.name,
                "default_purchase_taxes_and_charges_template", urd_template
            )
        frappe.db.commit()
        ok(f"Set '{urd_template}' as default tax on {len(urd_suppliers)} URD supplier(s)")


# ─────────────────────────────────────────────────────────────
# 9. CUSTOM FIELDS
# ─────────────────────────────────────────────────────────────

def create_custom_fields():
    print("\n[9/9] Creating Custom Fields...")

    # (dt, fieldname, label, fieldtype, options, insert_after, in_list_view)
    fields = [
        ("Purchase Invoice", "is_urd_purchase",  "URD Purchase (No GST)",
         "Check",  None,      "supplier",         1),
        ("Purchase Invoice", "furnitex_project",  "Project",
         "Link",   "Project", "is_urd_purchase",  1),
        ("Purchase Order",   "furnitex_project",  "Project",
         "Link",   "Project", "supplier",         1),
        ("Stock Entry",      "furnitex_project",  "Project",
         "Link",   "Project", "purpose",          1),
        ("Delivery Note",    "furnitex_project",  "Project",
         "Link",   "Project", "customer",         0),
        ("Journal Entry",    "furnitex_project",  "Project",
         "Link",   "Project", "voucher_type",     0),
    ]

    for dt, fn, label, ft, opts, after, in_list in fields:
        cf_name = f"{dt}-{fn}"
        if not exists("Custom Field", cf_name):
            d_dict = {
                "doctype":      "Custom Field",
                "dt":           dt,
                "fieldname":    fn,
                "label":        label,
                "fieldtype":    ft,
                "insert_after": after,
                "in_list_view": in_list,
                "in_standard_filter": 1,
                "search_index": 1,
            }
            if opts:
                d_dict["options"] = opts
            d = frappe.get_doc(d_dict)
            d.flags.ignore_permissions = True
            d.insert()
            ok(f"Custom Field: {dt}.{fn}")
        else:
            skip(f"Custom Field: {dt}.{fn}")

    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 10. SERVER SCRIPTS (Automation)
# ─────────────────────────────────────────────────────────────

def create_server_scripts():
    print("\n[+] Creating Server Scripts...")

    # Script 1: Auto-create OnSite WIP Warehouse on Project insert
    wip_script_name  = "Furnitex - Auto Create OnSite WIP Warehouse"
    wip_script_code  = """
# Auto-fires after a new Project is saved
# Creates "{Project Name} - OnSite WIP" warehouse automatically

project_name   = doc.project_name or doc.name
company        = doc.company or "Furnitex"
abbr           = frappe.db.get_value("Company", company, "abbr") or "F"
# OnSite WIP name uses company abbr so ERPNext accepts it
wh_short_name  = project_name + " - OnSite WIP"
warehouse_name = wh_short_name + " - " + abbr

# Find root warehouse group for this company
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
    frappe.db.commit()
    frappe.msgprint(
        "OnSite WIP Warehouse created: <b>" + warehouse_name + "</b>",
        alert=True, indicator="green"
    )
"""

    if not exists("Server Script", wip_script_name):
        d = frappe.get_doc({
            "doctype":           "Server Script",
            "name":              wip_script_name,
            "script_type":       "DocType Event",
            "reference_doctype": "Project",
            "doctype_event":     "After Insert",
            "enabled":           1,
            "script":            wip_script_code,
        })
        d.flags.ignore_permissions = True
        d.insert()
        ok(f"Server Script: {wip_script_name}")
    else:
        skip(f"Server Script: {wip_script_name}")

    # Script 2: Auto-clear taxes on URD Purchase Invoice (Before Save)
    urd_script_name = "Furnitex - Clear GST on URD Purchase"
    urd_script_code = """
# Fires Before Save on Purchase Invoice
# If flagged as URD Purchase, wipes all tax rows and expense accounts = COGS

if doc.is_urd_purchase:
    doc.taxes = []
    doc.taxes_and_charges = ""

    cogs_acct = frappe.db.get_value(
        "Account",
        {"account_name": "Cost of Goods Sold",
         "company": doc.company, "is_group": 0},
        "name"
    )
    if cogs_acct:
        for item in doc.items:
            item.expense_account = cogs_acct
"""

    if not exists("Server Script", urd_script_name):
        d = frappe.get_doc({
            "doctype":           "Server Script",
            "name":              urd_script_name,
            "script_type":       "DocType Event",
            "reference_doctype": "Purchase Invoice",
            "doctype_event":     "Before Save",
            "enabled":           1,
            "script":            urd_script_code,
        })
        d.flags.ignore_permissions = True
        d.insert()
        ok(f"Server Script: {urd_script_name}")
    else:
        skip(f"Server Script: {urd_script_name}")

    frappe.db.commit()


# ─────────────────────────────────────────────────────────────
# 11. PROJECT PROFITABILITY CUSTOM REPORT (Page Script)
# ─────────────────────────────────────────────────────────────

PROFIT_REPORT_SCRIPT = '''
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data    = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Project"),            "fieldname": "project",        "fieldtype": "Link", "options": "Project", "width": 160},
        {"label": _("Customer"),           "fieldname": "customer",       "fieldtype": "Data", "width": 160},
        {"label": _("Revenue Billed (₹)"), "fieldname": "revenue",        "fieldtype": "Currency", "width": 130},
        {"label": _("Raw Mat. Cost (₹)"),  "fieldname": "raw_mat_cost",   "fieldtype": "Currency", "width": 130},
        {"label": _("Mat. Consumed (₹)"),  "fieldname": "mat_consumed",   "fieldtype": "Currency", "width": 130},
        {"label": _("Labour/Conv. (₹)"),   "fieldname": "labour_cost",    "fieldtype": "Currency", "width": 130},
        {"label": _("Total Cost (₹)"),     "fieldname": "total_cost",     "fieldtype": "Currency", "width": 130},
        {"label": _("Net Margin (₹)"),     "fieldname": "net_margin",     "fieldtype": "Currency", "width": 130},
        {"label": _("Margin %"),           "fieldname": "margin_pct",     "fieldtype": "Percent",  "width": 90},
    ]

def get_data(filters):
    company = filters.get("company") if filters else None
    project_filter = filters.get("project") if filters else None

    proj_sql = ""
    args = []
    if company:
        proj_sql += " AND p.company = %s"
        args.append(company)
    if project_filter:
        proj_sql += " AND p.name = %s"
        args.append(project_filter)

    projects = frappe.db.sql(
        f"SELECT name, project_name, customer FROM `tabProject` WHERE 1=1 {proj_sql}",
        args, as_dict=1
    )

    rows = []
    for p in projects:
        pname = p.name

        revenue = (frappe.db.sql(
            "SELECT COALESCE(SUM(base_grand_total),0) v FROM `tabSales Invoice` WHERE project=%s AND docstatus=1",
            pname, as_dict=1)[0].v or 0)

        raw_mat = (frappe.db.sql(
            "SELECT COALESCE(SUM(base_net_total),0) v FROM `tabPurchase Invoice` WHERE furnitex_project=%s AND docstatus=1",
            pname, as_dict=1)[0].v or 0)

        consumed = (frappe.db.sql(
            """SELECT COALESCE(SUM(sed.amount),0) v
               FROM `tabStock Entry Detail` sed
               JOIN `tabStock Entry` se ON se.name=sed.parent
               WHERE se.furnitex_project=%s AND se.stock_entry_type='Material Issue' AND se.docstatus=1""",
            pname, as_dict=1)[0].v or 0)

        labour = (frappe.db.sql(
            """SELECT COALESCE(SUM(jvd.debit),0) v
               FROM `tabJournal Entry Account` jvd
               JOIN `tabJournal Entry` jv ON jv.name=jvd.parent
               WHERE jv.project=%s AND jv.docstatus=1
                 AND jvd.account LIKE '%Labour%'""",
            pname, as_dict=1)[0].v or 0)

        total_cost  = raw_mat + consumed + labour
        net_margin  = revenue - total_cost
        margin_pct  = round((net_margin / revenue * 100), 2) if revenue else 0

        rows.append({
            "project":     pname,
            "customer":    p.customer,
            "revenue":     revenue,
            "raw_mat_cost":raw_mat,
            "mat_consumed":consumed,
            "labour_cost": labour,
            "total_cost":  total_cost,
            "net_margin":  net_margin,
            "margin_pct":  margin_pct,
        })

    rows.sort(key=lambda r: r["net_margin"])
    return rows
'''

def create_custom_report():
    print("\n[+] Creating Custom Report: Furnitex Project Profitability...")
    report_name = "Furnitex Project Profitability"
    if not exists("Report", report_name):
        d = frappe.get_doc({
            "doctype":     "Report",
            "report_name": report_name,
            "ref_doctype": "Project",
            "report_type": "Script Report",
            "is_standard": "No",
            "module":      "ERPNext",
            "script":      PROFIT_REPORT_SCRIPT,
        })
        d.flags.ignore_permissions = True
        d.insert()
        ok(f"Custom Report: {report_name}")
        frappe.db.commit()
    else:
        skip(f"Custom Report: {report_name}")


# ─────────────────────────────────────────────────────────────
# MASTER RUNNER
# ─────────────────────────────────────────────────────────────

def run_all():
    frappe.set_user("Administrator")
    print("\n" + "=" * 58)
    print("  FURNITEX ERPNEXT v16 — AUTOMATED SETUP")
    print("  Company: Furnitex | India | INR")
    print("=" * 58)

    create_uoms()
    create_item_groups()
    create_supplier_groups()
    create_warehouses()
    create_tax_templates()
    create_service_items()
    create_raw_material_items()
    create_suppliers()
    create_custom_fields()
    create_server_scripts()
    create_custom_report()

    frappe.clear_cache()

    print("\n" + "=" * 58)
    print("  SETUP COMPLETE — refresh your browser")
    print("=" * 58 + "\n")


if __name__ == "__main__":
    import sys
    frappe.init(site="frontend")
    frappe.connect()
    run_all()
    frappe.destroy()
