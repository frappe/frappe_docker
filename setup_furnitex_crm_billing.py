"""
setup_furnitex_crm_billing.py
Full CRM + Billing setup for Furnitex (ERPNext v16)
Run: bench --site frontend execute frappe.setup_furnitex_crm_billing.run
"""

import frappe

COMPANY = "Furnitex"


def ok(msg):   print(f"  [OK]   {msg}")
def skip(msg): print(f"  [SKIP] {msg}")

def safe_insert(doc):
    try:
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory   = True
        doc.insert()
        return True
    except frappe.DuplicateEntryError:
        return False
    except Exception as e:
        if "Duplicate entry" in str(e):
            return False
        raise

def exists(dt, name):
    return frappe.db.exists(dt, name)

def exists_f(dt, filters):
    return frappe.db.get_value(dt, filters, "name")


# ──────────────────────────────────────────────────────────────
# 1. CUSTOMER GROUPS (Interior-specific)
# ──────────────────────────────────────────────────────────────
def create_customer_groups():
    print("\n[1] Customer Groups...")
    groups = [
        ("Residential - Individual",  "Individual"),
        ("Residential - Builder Flat","Individual"),
        ("Commercial - Office",       "Commercial"),
        ("Commercial - Restaurant",   "Commercial"),
        ("Commercial - Hotel",        "Commercial"),
        ("Commercial - Retail",       "Commercial"),
        ("Builder / Developer",       "Commercial"),
    ]
    for name, parent in groups:
        if not exists("Customer Group", name):
            d = frappe.get_doc({
                "doctype":            "Customer Group",
                "customer_group_name": name,
                "parent_customer_group": parent,
                "is_group":           0,
            })
            if safe_insert(d): ok(f"Customer Group: {name}")
            else: skip(f"{name} (dup)")
        else:
            skip(f"Customer Group: {name}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 2. TERRITORIES (Kolkata geography)
# ──────────────────────────────────────────────────────────────
def create_territories():
    print("\n[2] Territories...")
    # (name, parent)
    territories = [
        ("West Bengal",     "India"),
        ("Kolkata",         "West Bengal"),
        ("South Kolkata",   "Kolkata"),
        ("North Kolkata",   "Kolkata"),
        ("Salt Lake",       "Kolkata"),
        ("New Town",        "Kolkata"),
        ("Rajarhat",        "Kolkata"),
        ("Howrah",          "West Bengal"),
        ("Hooghly",         "West Bengal"),
    ]
    for name, parent in territories:
        if not exists("Territory", name):
            d = frappe.get_doc({
                "doctype":          "Territory",
                "territory_name":   name,
                "parent_territory": parent,
                "is_group":         0,
            })
            if safe_insert(d): ok(f"Territory: {name}")
            else: skip(f"{name} (dup)")
        else:
            skip(f"Territory: {name}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 3. LEAD SOURCES  (added as custom Select field on Lead)
# ──────────────────────────────────────────────────────────────
LEAD_SOURCES = "\n".join([
    "Instagram",
    "Facebook",
    "Word of Mouth",
    "Client Referral",
    "Just Dial",
    "Housing.com",
    "99acres / MagicBricks",
    "Site Board / Hoarding",
    "Google Search",
    "Direct Walk-In",
    "Architect / Designer Referral",
    "Builder Tie-up",
    "Exhibition / Home Fair",
    "YouTube",
    "WhatsApp Broadcast",
])

def create_lead_sources():
    # Lead Source is a standalone CRM-app doctype not installed here.
    # We add it as a custom Select field on Lead + Opportunity instead.
    print("\n[3] Lead Sources (as custom Select field)...")

    for dt, after_field in [("Lead", "qualification_status"), ("Opportunity", "opportunity_type")]:
        cf_name = f"{dt}-furnitex_lead_source"
        if not exists("Custom Field", cf_name):
            d = frappe.get_doc({
                "doctype":      "Custom Field",
                "dt":           dt,
                "fieldname":    "furnitex_lead_source",
                "label":        "Lead Source",
                "fieldtype":    "Select",
                "options":      LEAD_SOURCES,
                "insert_after": after_field,
                "in_list_view": 1,
                "in_standard_filter": 1,
            })
            if safe_insert(d): ok(f"Lead Source Select field → {dt}")
            else: skip(f"{dt}.furnitex_lead_source (dup)")
        else:
            skip(f"Lead Source field exists on {dt}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 4. SALES PERSONS
# ──────────────────────────────────────────────────────────────
def create_sales_persons():
    print("\n[4] Sales Persons...")
    persons = [
        ("Furnitex - Site Team",  "Sales Team"),
        ("Furnitex - Design Team","Sales Team"),
        ("Furnitex - BD Manager", "Sales Team"),
    ]
    for name, parent in persons:
        if not exists("Sales Person", name):
            d = frappe.get_doc({
                "doctype":          "Sales Person",
                "sales_person_name": name,
                "parent_sales_person": parent,
                "is_group":         0,
                "enabled":          1,
            })
            if safe_insert(d): ok(f"Sales Person: {name}")
            else: skip(f"{name} (dup)")
        else:
            skip(f"Sales Person: {name}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 5. MODE OF PAYMENT (Furnitex extras)
# ──────────────────────────────────────────────────────────────
def create_payment_modes():
    print("\n[5] Modes of Payment...")
    modes = [
        ("NEFT / RTGS",   "Bank"),
        ("IMPS",          "Bank"),
        ("Google Pay",    "Bank"),
        ("PhonePe",       "Bank"),
        ("Paytm",         "Bank"),
        ("Cash - Site",   "Cash"),
    ]

    # find default bank account
    bank_acct = frappe.db.get_value("Account",
        {"account_type": "Bank", "company": COMPANY, "is_group": 0}, "name")
    cash_acct  = frappe.db.get_value("Account",
        {"account_type": "Cash", "company": COMPANY, "is_group": 0}, "name")

    for name, mtype in modes:
        if not exists("Mode of Payment", name):
            d_dict = {
                "doctype":          "Mode of Payment",
                "mode_of_payment":  name,
                "type":             mtype,
            }
            acct = bank_acct if mtype == "Bank" else cash_acct
            if acct:
                d_dict["accounts"] = [{
                    "company": COMPANY,
                    "default_account": acct,
                }]
            d = frappe.get_doc(d_dict)
            if safe_insert(d): ok(f"Mode of Payment: {name}")
            else: skip(f"{name} (dup)")
        else:
            skip(f"Mode of Payment: {name}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 6. PAYMENT TERMS TEMPLATES
# ──────────────────────────────────────────────────────────────
def create_payment_terms():
    print("\n[6] Payment Terms Templates...")

    templates = [

        # ── A: Standard Interior Project (milestone-based) ───────
        {
            "name": "Furnitex - Standard Interior Project",
            "terms": [
                {"payment_term_name": "30% Advance on Agreement",
                 "invoice_portion": 30, "credit_days": 0,
                 "description": "Booking advance on signing agreement"},
                {"payment_term_name": "30% on 50% Site Completion",
                 "invoice_portion": 30, "credit_days": 30,
                 "description": "Second milestone: 50% work done"},
                {"payment_term_name": "30% on Work Completion",
                 "invoice_portion": 30, "credit_days": 60,
                 "description": "Third milestone: work complete"},
                {"payment_term_name": "10% on Final Handover",
                 "invoice_portion": 10, "credit_days": 75,
                 "description": "Retention released at handover"},
            ],
        },

        # ── B: 50-50 (smaller projects) ──────────────────────────
        {
            "name": "Furnitex - 50-50 Advance",
            "terms": [
                {"payment_term_name": "50% Advance",
                 "invoice_portion": 50, "credit_days": 0,
                 "description": "Advance before work begins"},
                {"payment_term_name": "50% on Delivery",
                 "invoice_portion": 50, "credit_days": 30,
                 "description": "Balance on delivery / installation"},
            ],
        },

        # ── C: 100% Advance (small orders / loose furniture) ─────
        {
            "name": "Furnitex - 100% Advance",
            "terms": [
                {"payment_term_name": "100% Advance",
                 "invoice_portion": 100, "credit_days": 0,
                 "description": "Full payment before production"},
            ],
        },

        # ── D: Lumpsum 3-stage (commercial projects) ─────────────
        {
            "name": "Furnitex - Commercial 3-Stage",
            "terms": [
                {"payment_term_name": "40% Advance - Commercial",
                 "invoice_portion": 40, "credit_days": 0,
                 "description": "Mobilisation advance"},
                {"payment_term_name": "40% Mid-Stage - Commercial",
                 "invoice_portion": 40, "credit_days": 45,
                 "description": "Mid-project milestone"},
                {"payment_term_name": "20% Retention - Commercial",
                 "invoice_portion": 20, "credit_days": 90,
                 "description": "Retention on final handover"},
            ],
        },
    ]

    for t in templates:
        tname = t["name"]
        if not exists_f("Payment Terms Template", {"template_name": tname}):
            # Ensure Payment Term records exist for each row
            term_rows = []
            for term in t["terms"]:
                pt_name = term["payment_term_name"]
                if not exists("Payment Term", pt_name):
                    pt = frappe.get_doc({
                        "doctype":           "Payment Term",
                        "payment_term_name": pt_name,
                        "invoice_portion":   term["invoice_portion"],
                        "credit_days_based_on": "Day(s) after invoice date",
                        "credit_days":       term["credit_days"],
                        "description":       term["description"],
                    })
                    safe_insert(pt)
                term_rows.append({
                    "payment_term":   pt_name,
                    "invoice_portion": term["invoice_portion"],
                    "credit_days_based_on": "Day(s) after invoice date",
                    "credit_days":    term["credit_days"],
                    "description":    term["description"],
                })

            d = frappe.get_doc({
                "doctype":       "Payment Terms Template",
                "template_name": tname,
                "terms":         term_rows,
            })
            if safe_insert(d): ok(f"Payment Terms: {tname}")
            else: skip(f"{tname} (dup)")
        else:
            skip(f"Payment Terms: {tname}")

    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 7. TERMS AND CONDITIONS TEMPLATES
# ──────────────────────────────────────────────────────────────
def create_terms_conditions():
    print("\n[7] Terms & Conditions Templates...")

    templates = [

        # ── Quotation T&C ─────────────────────────────────────────
        {
            "title": "Furnitex - Quotation Terms",
            "terms": """<h3>Terms &amp; Conditions — Furnitex Interior</h3>
<ol>
<li><strong>Validity:</strong> This quotation is valid for <strong>15 days</strong> from the date of issue.</li>
<li><strong>Scope:</strong> Only items listed in this quotation are included. Any additional work will be quoted separately.</li>
<li><strong>Payment Schedule:</strong> 30% advance on confirmation, 30% at 50% completion, 30% at completion, 10% on handover.</li>
<li><strong>Timeline:</strong> Work commences within 7 working days of advance payment and site clearance. Timeline communicated separately.</li>
<li><strong>Material:</strong> All materials as specified. Substitution only with client approval.</li>
<li><strong>Civil Work:</strong> Civil, electrical, plumbing work by client unless specifically included above.</li>
<li><strong>Site Access:</strong> Client to ensure unobstructed site access during working hours (9 AM – 6 PM).</li>
<li><strong>Warranty:</strong> 1-year workmanship warranty. Hardware warranty as per manufacturer.</li>
<li><strong>Disputes:</strong> Subject to Kolkata jurisdiction.</li>
</ol>
<p><em>Furnitex | Interior Design &amp; Furniture | Kolkata</em></p>""",
        },

        # ── Sales Invoice T&C ─────────────────────────────────────
        {
            "title": "Furnitex - Invoice Terms",
            "terms": """<h3>Invoice Terms — Furnitex Interior</h3>
<ol>
<li><strong>Payment Due:</strong> As per agreed payment schedule. Late payment attracts 2% per month interest.</li>
<li><strong>Goods:</strong> Materials remain property of Furnitex until full payment is received.</li>
<li><strong>Defects:</strong> Any defects must be reported within 7 days of delivery/installation.</li>
<li><strong>Warranty:</strong> 1-year warranty on workmanship from date of handover. Excludes wear, misuse, and civil damage.</li>
<li><strong>Disputes:</strong> Subject to Kolkata jurisdiction only.</li>
</ol>
<p>Bank: [Your Bank] | A/c: [Account No] | IFSC: [IFSC] | UPI: [UPI ID]</p>
<p><em>Thank you for choosing Furnitex!</em></p>""",
        },

        # ── Purchase Order T&C ────────────────────────────────────
        {
            "title": "Furnitex - Purchase Order Terms",
            "terms": """<h3>Purchase Order Terms — Furnitex</h3>
<ol>
<li>Delivery as per schedule agreed. Delays will be notified promptly.</li>
<li>Materials must match specifications. Furnitex reserves the right to reject substandard material.</li>
<li>Invoice must reference this PO number.</li>
<li>Furnitex is not liable for GST on unregistered supplier purchases.</li>
</ol>""",
        },
    ]

    for t in templates:
        if not exists("Terms and Conditions", t["title"]):
            d = frappe.get_doc({
                "doctype": "Terms and Conditions",
                "title":   t["title"],
                "terms":   t["terms"],
            })
            if safe_insert(d): ok(f"T&C: {t['title']}")
            else: skip(f"T&C: {t['title']} (dup)")
        else:
            skip(f"T&C: {t['title']}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 8. PRICE LIST — Furnitex Interior Rate Card
# ──────────────────────────────────────────────────────────────
def create_price_list():
    print("\n[8] Price Lists & Item Prices...")

    pl_name = "Furnitex Interior Rate Card"
    if not exists("Price List", pl_name):
        d = frappe.get_doc({
            "doctype":   "Price List",
            "price_list_name": pl_name,
            "currency":  "INR",
            "selling":   1,
            "buying":    0,
            "enabled":   1,
        })
        if safe_insert(d): ok(f"Price List: {pl_name}")
        else: skip(f"{pl_name} (dup)")
    else:
        skip(f"Price List: {pl_name}")

    frappe.db.commit()

    # ── Standard Item Prices (on both Standard Selling + Interior Rate Card) ──
    item_prices = [
        # (item_code, rate)  — per SqFt or per Nos
        ("SVC-FC-EXEC",    185),   # False Ceiling / SqFt
        ("SVC-WAR-LAM",    950),   # Laminate Wardrobe / SqFt
        ("SVC-KIT-EXEC",  1100),   # Modular Kitchen / SqFt
        ("SVC-FLOOR",      120),   # Flooring / SqFt
        ("SVC-LUMP",         0),   # Lumpsum — rate set per project
        ("SVC-DESIGN",   15000),   # Design consultation / Nos
        ("SVC-CONVEY",    2000),   # Conveyance / trip
        ("SVC-LABOUR",     700),   # Labour / day
        ("SVC-ELECTRIC",     0),   # Electrical — per quote
        ("SVC-PAINT",      35),    # Painting / SqFt
    ]

    price_lists = ["Standard Selling", pl_name]
    for pl in price_lists:
        if not exists("Price List", pl):
            continue
        for code, rate in item_prices:
            if not exists("Item", code):
                continue
            if not exists_f("Item Price", {"item_code": code, "price_list": pl, "selling": 1}):
                ip = frappe.get_doc({
                    "doctype":    "Item Price",
                    "item_code":  code,
                    "price_list": pl,
                    "selling":    1,
                    "currency":   "INR",
                    "price_list_rate": rate,
                })
                if safe_insert(ip): ok(f"Item Price: {code} ₹{rate} [{pl}]")
                else: skip(f"Item Price: {code} [{pl}] (dup)")
            else:
                skip(f"Item Price: {code} [{pl}]")

    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 9. CUSTOM FIELDS — CRM & BILLING
# ──────────────────────────────────────────────────────────────
def create_crm_billing_fields():
    print("\n[9] CRM & Billing Custom Fields...")

    fields = [

        # ── CUSTOMER ─────────────────────────────────────────────
        ("Customer", "whatsapp_number",    "WhatsApp Number",
         "Data",  None,  "mobile_no",          0),
        ("Customer", "property_address",   "Property / Site Address",
         "Small Text", None, "whatsapp_number", 0),
        ("Customer", "project_type",       "Project Type",
         "Select", "Residential\nCommercial\nHospitality\nRetail", "property_address", 0),
        ("Customer", "property_size_sqft", "Approx. Area (SqFt)",
         "Float",  None,  "project_type",       0),
        ("Customer", "budget_range",       "Budget Range",
         "Select",
         "Under ₹5 Lakhs\n₹5–10 Lakhs\n₹10–25 Lakhs\n₹25–50 Lakhs\nAbove ₹50 Lakhs",
         "property_size_sqft", 0),
        ("Customer", "referred_by",        "Referred By",
         "Data",  None,  "budget_range",        0),

        # ── LEAD ─────────────────────────────────────────────────
        ("Lead", "whatsapp_number",    "WhatsApp Number",
         "Data",  None,  "mobile_no",        0),
        ("Lead", "project_type_lead",  "Project Type",
         "Select", "Residential\nCommercial\nHospitality\nRetail",
         "whatsapp_number", 0),
        ("Lead", "property_address",   "Property / Site Address",
         "Small Text", None, "project_type_lead", 0),
        ("Lead", "area_sqft",          "Approx. Area (SqFt)",
         "Float",  None,  "property_address",  0),
        ("Lead", "budget_range",       "Budget Range",
         "Select",
         "Under ₹5 Lakhs\n₹5–10 Lakhs\n₹10–25 Lakhs\n₹25–50 Lakhs\nAbove ₹50 Lakhs",
         "area_sqft", 0),
        ("Lead", "site_visit_done",    "Site Visit Done",
         "Check", None,  "budget_range",      0),
        ("Lead", "site_visit_date",    "Site Visit Date",
         "Date",  None,  "site_visit_done",   0),
        ("Lead", "estimated_value",    "Estimated Project Value (₹)",
         "Currency", None, "site_visit_date", 0),

        # ── QUOTATION ────────────────────────────────────────────
        ("Quotation", "site_address",          "Site / Delivery Address",
         "Small Text", None, "customer_address", 0),
        ("Quotation", "scope_of_work",         "Scope of Work",
         "Small Text", None, "site_address",     0),
        ("Quotation", "site_visit_date",       "Site Visit Date",
         "Date",  None,  "scope_of_work",      0),
        ("Quotation", "expected_start_date_q", "Expected Start Date",
         "Date",  None,  "site_visit_date",    0),
        ("Quotation", "expected_handover_date","Expected Handover Date",
         "Date",  None,  "expected_start_date_q", 0),
        ("Quotation", "design_style",          "Design Style",
         "Select",
         "Modern / Contemporary\nTraditional / Classic\nMinimalist\nIndustrial\nBohemian\nMediterranean",
         "expected_handover_date", 0),

        # ── SALES INVOICE ────────────────────────────────────────
        # 'project' field is native on Sales Invoice in v16 — no custom field needed.
        # Adding billing-specific extras after 'customer_name' instead.
        ("Sales Invoice", "milestone_description", "Milestone Description",
         "Small Text", None, "customer_name", 0),
        ("Sales Invoice", "payment_mode_note",     "Payment Mode Note",
         "Data",  None, "milestone_description", 0),

        # ── OPPORTUNITY ──────────────────────────────────────────
        ("Opportunity", "property_address",    "Property / Site Address",
         "Small Text", None, "customer_name", 0),
        ("Opportunity", "area_sqft",           "Area (SqFt)",
         "Float",  None, "property_address",  0),
        ("Opportunity", "design_style",        "Design Style",
         "Select",
         "Modern / Contemporary\nTraditional / Classic\nMinimalist\nIndustrial\nBohemian\nMediterranean",
         "area_sqft", 0),
        ("Opportunity", "site_visit_done",     "Site Visit Done",
         "Check", None, "design_style",       0),
        ("Opportunity", "site_visit_date",     "Site Visit Date",
         "Date",  None, "site_visit_done",    0),
    ]

    for dt, fn, label, ft, opts, after, in_list in [
        (*f, 0) if len(f) == 6 else f for f in fields
    ]:
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
            }
            if opts:
                d_dict["options"] = opts
            d = frappe.get_doc(d_dict)
            if safe_insert(d): ok(f"Custom Field: {dt}.{fn}")
            else: skip(f"{dt}.{fn} (dup)")
        else:
            skip(f"Custom Field: {dt}.{fn}")

    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 10. SAMPLE CUSTOMERS (Kolkata residential)
# ──────────────────────────────────────────────────────────────
def create_sample_customers():
    print("\n[10] Sample Customers...")

    customers = [
        {
            "customer_name":  "Sharma Residence - Salt Lake",
            "customer_group": "Residential - Individual",
            "territory":      "Salt Lake",
            "customer_type":  "Individual",
        },
        {
            "customer_name":  "Mukherjee Apartment - Behala",
            "customer_group": "Residential - Builder Flat",
            "territory":      "South Kolkata",
            "customer_type":  "Individual",
        },
        {
            "customer_name":  "Bansal Office - Park Street",
            "customer_group": "Commercial - Office",
            "territory":      "Kolkata",
            "customer_type":  "Company",
        },
    ]
    for c in customers:
        if not exists("Customer", c["customer_name"]):
            d = frappe.get_doc({"doctype": "Customer", **c})
            if safe_insert(d): ok(f"Customer: {c['customer_name']}")
            else: skip(f"{c['customer_name']} (dup)")
        else:
            skip(f"Customer: {c['customer_name']}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 11. SELLING SETTINGS — set Furnitex defaults
# ──────────────────────────────────────────────────────────────
def configure_selling_settings():
    print("\n[11] Selling & CRM Settings...")
    try:
        s = frappe.get_single("Selling Settings")
        s.cust_master_name        = "Customer Name"
        s.customer_group          = "Residential - Individual"
        s.territory               = "Kolkata"
        s.price_list              = "Standard Selling"
        s.selling_price_list      = "Standard Selling"
        s.flags.ignore_permissions = True
        s.save()
        ok("Selling Settings updated")
    except Exception as e:
        skip(f"Selling Settings: {e}")

    try:
        b = frappe.get_single("Buying Settings")
        b.supp_master_name        = "Supplier Name"
        b.supplier_group          = "Local Market Vendor (Unregistered)"
        b.flags.ignore_permissions = True
        b.save()
        ok("Buying Settings updated")
    except Exception as e:
        skip(f"Buying Settings: {e}")

    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 12. CRM PIPELINE — Sales Stages + Opportunity Types
# ──────────────────────────────────────────────────────────────
def create_crm_stages():
    print("\n[12] CRM Pipeline (Sales Stages + Opportunity Types)...")

    # ── Sales Stages ─────────────────────────────────────────
    furnitex_stages = [
        "New Enquiry",
        "Site Visit Scheduled",
        "Site Visit Done",
        "Design Presentation",
        "Quotation Sent",
        "Negotiation",
        "PO / Work Order Received",
        "Work In Progress",
        "Handover Done",
    ]
    for stage in furnitex_stages:
        if not exists("Sales Stage", stage):
            try:
                d = frappe.get_doc({
                    "doctype":    "Sales Stage",
                    "stage_name": stage,
                })
                if safe_insert(d): ok(f"Sales Stage: {stage}")
                else: skip(f"{stage} (dup)")
            except Exception as e:
                skip(f"Sales Stage {stage}: {e}")
        else:
            skip(f"Sales Stage: {stage}")

    # ── Opportunity Types ─────────────────────────────────────
    opp_types = [
        "Interior Design - Full Home",
        "Interior Design - Bedroom",
        "Interior Design - Kitchen",
        "Interior Design - Office",
        "Interior Design - Restaurant",
        "Loose Furniture Supply",
        "Renovation / Refurbishment",
        "False Ceiling Only",
        "Wardrobe / Storage Only",
        "Flooring Only",
    ]
    for ot in opp_types:
        if not exists("Opportunity Type", ot):
            try:
                d = frappe.get_doc({
                    "doctype": "Opportunity Type",
                    "name":    ot,
                })
                if safe_insert(d): ok(f"Opportunity Type: {ot}")
                else: skip(f"{ot} (dup)")
            except Exception as e:
                skip(f"Opportunity Type {ot}: {e}")
        else:
            skip(f"Opportunity Type: {ot}")

    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 13. PRINT FORMAT — Quotation (set default T&C)
# ──────────────────────────────────────────────────────────────
def configure_print_defaults():
    print("\n[13] Setting default T&C on Quotation & Sales Invoice...")

    # Set default terms on Quotation doctype
    try:
        meta = frappe.get_meta("Quotation")
        default_tc = "Furnitex - Quotation Terms"
        if exists("Terms and Conditions", default_tc):
            frappe.db.set_default("terms_and_conditions_quotation", default_tc)
            ok(f"Default T&C for Quotation: {default_tc}")
    except Exception as e:
        skip(f"Quotation T&C default: {e}")

    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# 14. LETTER HEAD
# ──────────────────────────────────────────────────────────────
def create_letter_head():
    print("\n[14] Letter Head...")
    lh_name = "Furnitex"
    if not exists("Letter Head", lh_name):
        d = frappe.get_doc({
            "doctype":         "Letter Head",
            "letter_head_name": lh_name,
            "is_default":      1,
            "source":          "Rich Text",
            "content": """
<div style="font-family: 'Segoe UI', Arial, sans-serif; border-bottom: 3px solid #2c3e50; padding-bottom: 12px; margin-bottom: 8px;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td>
        <h1 style="margin:0; font-size:28px; color:#2c3e50; letter-spacing:2px;">FURNITEX</h1>
        <p style="margin:2px 0 0; font-size:12px; color:#7f8c8d; letter-spacing:1px;">
          INTERIOR DESIGN &amp; FURNITURE MANUFACTURING
        </p>
      </td>
      <td style="text-align:right; font-size:11px; color:#555; line-height:1.6;">
        Kolkata, West Bengal — India<br>
        📞 +91 XXXXX XXXXX<br>
        ✉ info@furnitex.in<br>
        🌐 www.furnitex.in
      </td>
    </tr>
  </table>
</div>""",
            "footer": """
<div style="font-family: Arial, sans-serif; border-top: 1px solid #ccc; padding-top: 6px; font-size: 10px; color: #888; text-align: center;">
  Furnitex | Interior Design &amp; Furniture | Kolkata | GSTIN: [Your GSTIN] | CIN: [If applicable]
</div>""",
        })
        if safe_insert(d): ok(f"Letter Head: {lh_name}")
        else: skip(f"Letter Head {lh_name} (dup)")
    else:
        skip(f"Letter Head: {lh_name}")
    frappe.db.commit()


# ──────────────────────────────────────────────────────────────
# MASTER RUNNER
# ──────────────────────────────────────────────────────────────
def run():
    frappe.set_user("Administrator")

    print("\n" + "=" * 58)
    print("  FURNITEX — CRM + BILLING SETUP")
    print("=" * 58)

    create_customer_groups()
    create_territories()
    create_lead_sources()
    create_sales_persons()
    create_payment_modes()
    create_payment_terms()
    create_terms_conditions()
    create_price_list()
    create_crm_billing_fields()
    create_sample_customers()
    configure_selling_settings()
    create_crm_stages()
    configure_print_defaults()
    create_letter_head()

    frappe.clear_cache()

    print("\n" + "=" * 58)
    print("  CRM + BILLING SETUP COMPLETE — refresh your browser")
    print("=" * 58 + "\n")
