"""
update_furnitex_info.py
Updates ERPNext with real Furnitex business details from furnitex.co.in
Run via: bench --site frontend execute frappe.update_furnitex_info.run
"""

import frappe

COMPANY = "Furnitex"

ADDRESS       = "6/A/108 Mukundapur"
CITY          = "Kolkata"
STATE         = "West Bengal"
PINCODE       = "700099"
COUNTRY       = "India"
PHONE         = "+91 62905 91422"
EMAIL         = "info.furnitex@gmail.com"
WEBSITE       = "https://furnitex.co.in"
INSTAGRAM     = "https://www.instagram.com/frunitex"
LEGAL_NAME    = "Furnitex Atelier Pvt. Ltd."
TAGLINE       = "Redefine What Surrounds You"
FULL_ADDR     = f"{ADDRESS}, {CITY} - {PINCODE}, {STATE}, {COUNTRY}"
REP_NAME      = "Subhankar Dhar"
OFFICE_HOURS  = "Monday – Saturday, 10:00 AM – 7:00 PM IST"


def run():
    frappe.set_user("Administrator")

    update_company()
    update_address()
    update_letter_head()
    update_terms_conditions()

    frappe.db.commit()
    frappe.clear_cache()
    print("\n✓ Furnitex business info updated successfully.\n")


# ── 1. Company record ─────────────────────────────────────────────────────────

def update_company():
    co = frappe.get_doc("Company", COMPANY)
    co.phone_no      = PHONE
    co.email         = EMAIL
    co.website       = WEBSITE
    co.company_name  = COMPANY          # keep short name as primary
    co.flags.ignore_permissions = True
    co.save()
    print(f"  ✓ Company record updated: phone={PHONE}, email={EMAIL}")


# ── 2. Address record ─────────────────────────────────────────────────────────

def update_address():
    # Check if a Furnitex address already exists
    existing = frappe.db.get_value(
        "Address",
        {"address_title": COMPANY, "address_type": "Billing"},
        "name"
    )

    addr_doc = {
        "doctype":        "Address",
        "address_title":  COMPANY,
        "address_type":   "Billing",
        "address_line1":  ADDRESS,
        "city":           CITY,
        "state":          STATE,
        "pincode":        PINCODE,
        "country":        COUNTRY,
        "phone":          PHONE,
        "email_id":       EMAIL,
        "is_primary_address": 1,
        "links": [{
            "link_doctype": "Company",
            "link_name":    COMPANY
        }]
    }

    if existing:
        doc = frappe.get_doc("Address", existing)
        doc.update(addr_doc)
        doc.flags.ignore_permissions = True
        doc.save()
        print(f"  ✓ Address updated: {FULL_ADDR}")
    else:
        doc = frappe.get_doc(addr_doc)
        doc.flags.ignore_permissions = True
        doc.insert()
        print(f"  ✓ Address created: {FULL_ADDR}")


# ── 3. Letter Head ────────────────────────────────────────────────────────────

LETTER_HEAD_HTML = f"""
<div style="font-family:'Segoe UI',Arial,sans-serif; padding:0; margin:0;">
  <table width="100%" style="border-bottom:2px solid #1a1a1a; padding-bottom:14px; margin-bottom:8px;">
    <tr>
      <td style="vertical-align:top; width:60%;">
        <div style="font-size:26px; font-weight:700; letter-spacing:3px; color:#1a1a1a; text-transform:uppercase;">
          FURNITEX
        </div>
        <div style="font-size:10px; letter-spacing:2px; color:#555; text-transform:uppercase; margin-top:2px;">
          {TAGLINE}
        </div>
        <div style="font-size:9px; color:#888; margin-top:4px;">
          {LEGAL_NAME}
        </div>
      </td>
      <td style="vertical-align:top; text-align:right; width:40%; font-size:9.5px; color:#444; line-height:1.7;">
        <div>{ADDRESS}</div>
        <div>{CITY} - {PINCODE}, {STATE}</div>
        <div>Phone: {PHONE}</div>
        <div>Email: {EMAIL}</div>
        <div>Web: furnitex.co.in</div>
      </td>
    </tr>
  </table>
</div>
"""

def update_letter_head():
    lh_name = "Furnitex"
    if frappe.db.exists("Letter Head", lh_name):
        doc = frappe.get_doc("Letter Head", lh_name)
        doc.content = LETTER_HEAD_HTML
        doc.is_default = 1
        doc.flags.ignore_permissions = True
        doc.save()
        print("  ✓ Letter Head updated with real contact details")
    else:
        doc = frappe.get_doc({
            "doctype":   "Letter Head",
            "letter_head_name": lh_name,
            "content":   LETTER_HEAD_HTML,
            "is_default": 1,
        })
        doc.flags.ignore_permissions = True
        doc.insert()
        print("  ✓ Letter Head created")


# ── 4. Terms & Conditions ─────────────────────────────────────────────────────

QUOTATION_TC = f"""<div style="font-size:10.5px; line-height:1.8; color:#333;">
<strong>FURNITEX — Quotation Terms &amp; Conditions</strong><br><br>

1. <strong>Validity:</strong> This quotation is valid for 15 days from the date of issue.<br>
2. <strong>Payment Terms:</strong> 30% advance on order confirmation, 30% at 50% completion, 30% at completion, 10% at handover.<br>
3. <strong>Delivery:</strong> Timelines are estimated and subject to site readiness and material availability. Furnitex is not liable for delays caused by site conditions.<br>
4. <strong>Design Changes:</strong> Any changes post order confirmation may attract additional charges and revised timelines.<br>
5. <strong>Material:</strong> All materials as specified. Substitutions may be made with equivalent or superior alternatives with prior intimation.<br>
6. <strong>Site Access:</strong> Client to ensure uninterrupted site access during agreed working hours: {OFFICE_HOURS}.<br>
7. <strong>Warranty:</strong> 1-year manufacturing warranty on all Furnitex-fabricated items. Hardware and third-party products carry manufacturer warranty.<br>
8. <strong>Dispute Resolution:</strong> All disputes subject to Kolkata jurisdiction.<br><br>

<em>Furnitex Atelier Pvt. Ltd. · {ADDRESS}, {CITY} - {PINCODE} · {PHONE} · {EMAIL}</em>
</div>"""

INVOICE_TC = f"""<div style="font-size:10.5px; line-height:1.8; color:#333;">
<strong>FURNITEX — Invoice Terms &amp; Conditions</strong><br><br>

1. <strong>Payment Due:</strong> Payment is due within 7 days of invoice date unless otherwise agreed in writing.<br>
2. <strong>Late Payment:</strong> Overdue amounts attract interest at 18% per annum.<br>
3. <strong>GST:</strong> GST as applicable under Indian law is charged additionally where mentioned.<br>
4. <strong>Delivery &amp; Installation:</strong> Goods remain property of Furnitex until full payment is received.<br>
5. <strong>Returns:</strong> Custom-manufactured furniture is non-returnable. Defects to be reported within 48 hours of delivery.<br>
6. <strong>Warranty:</strong> 1-year manufacturing defect warranty. Normal wear, misuse, or site-caused damage not covered.<br>
7. <strong>Disputes:</strong> Subject to Kolkata jurisdiction.<br><br>

<em>Furnitex Atelier Pvt. Ltd. · {ADDRESS}, {CITY} - {PINCODE} · {PHONE} · {EMAIL}</em>
</div>"""

PO_TC = f"""<div style="font-size:10.5px; line-height:1.8; color:#333;">
<strong>FURNITEX — Purchase Order Terms &amp; Conditions</strong><br><br>

1. <strong>Acceptance:</strong> Supply of goods/services against this PO constitutes acceptance of these terms.<br>
2. <strong>Quality:</strong> All materials must conform to the specifications mentioned. Substandard materials will be rejected at supplier's cost.<br>
3. <strong>Delivery:</strong> Deliver to the address specified on the PO by the agreed date. Delays must be communicated 48 hours in advance.<br>
4. <strong>Invoice:</strong> Raise GST-compliant invoice (or cash memo for URD) with PO reference. Payment processed within 7 days of invoice receipt and material acceptance.<br>
5. <strong>Warranty:</strong> Supplier warrants materials against defects for minimum 6 months from delivery.<br>
6. <strong>Jurisdiction:</strong> Kolkata courts have exclusive jurisdiction.<br><br>

<em>Furnitex Atelier Pvt. Ltd. · {ADDRESS}, {CITY} - {PINCODE} · {PHONE} · {EMAIL}</em>
</div>"""

TC_MAP = {
    "Furnitex - Quotation T&C":     QUOTATION_TC,
    "Furnitex - Invoice T&C":       INVOICE_TC,
    "Furnitex - Purchase Order T&C": PO_TC,
}

def update_terms_conditions():
    for title, content in TC_MAP.items():
        if frappe.db.exists("Terms and Conditions", title):
            doc = frappe.get_doc("Terms and Conditions", title)
            doc.terms = content
            doc.flags.ignore_permissions = True
            doc.save()
            print(f"  ✓ Updated T&C: {title}")
        else:
            doc = frappe.get_doc({
                "doctype":  "Terms and Conditions",
                "title":    title,
                "terms":    content,
                "selling":  1,
                "buying":   1,
                "hr":       0,
            })
            doc.flags.ignore_permissions = True
            doc.insert()
            print(f"  ✓ Created T&C: {title}")
