import frappe

def run():
    print("=== Setting up Analysis Division ===")
    create_bi_number_cards()
    create_bi_charts()
    create_analysis_workspace()
    update_existing_data()
    print("=== Analysis Division setup complete ===")


def create_bi_number_cards():
    cards = [
        {"label": "Monthly Rate Entries", "document_type": "Monthly Market Rate", "function": "Count", "filter": '[[\"Monthly Market Rate\",\"docstatus\",\"=\",1]]', "color": "#3498db"},
    ]
    for card_data in cards:
        name = card_data["label"]
        if not frappe.db.exists("Number Card", name):
            try:
                doc = frappe.get_doc({
                    "doctype": "Number Card",
                    "label": name,
                    "document_type": card_data["document_type"],
                    "function": card_data.get("function", "Count"),
                    "filter": card_data.get("filter", "[]"),
                    "color": card_data.get("color", "#3498db"),
                    "type": "Document Type",
                    "show_percentage_stats": 1,
                    "stats_time_interval": "Daily",
                })
                doc.insert(ignore_permissions=True)
                print(f"  Created Number Card: {name}")
            except Exception as e:
                print(f"  Skipped {name}: {e}")


def create_bi_charts():
    charts = [
        {"chart_name": "Market Rate Trend", "chart_type": "Custom", "type": "Line", "color": "#24963f",
         "custom_options": '{"method": "cosmos_core.analysis.analysis.get_chart_data", "args": {"months": 6}}'},
        {"chart_name": "Items with Highest Variation", "chart_type": "Custom", "type": "Bar", "color": "#e74c3c",
         "custom_options": '{"method": "cosmos_core.analysis.analysis.get_top_variations", "args": {"limit": 10}}'},
    ]
    for chart_data in charts:
        name = chart_data["chart_name"]
        if not frappe.db.exists("Dashboard Chart", name):
            try:
                doc = frappe.get_doc({
                    "doctype": "Dashboard Chart",
                    "chart_name": name,
                    "chart_type": chart_data["chart_type"],
                    "type": chart_data["type"],
                    "color": chart_data.get("color", "#24963f"),
                    "is_public": 1,
                    "filters_json": "[]",
                    "custom_options": chart_data.get("custom_options", "{}"),
                })
                doc.insert(ignore_permissions=True)
                print(f"  Created Chart: {name}")
            except Exception as e:
                print(f"  Skipped {name}: {e}")


def create_analysis_workspace():
    ws_name = "Analysis Division"
    if frappe.db.exists("Workspace", ws_name):
        ws = frappe.get_doc("Workspace", ws_name)
    else:
        ws = frappe.get_doc({
            "doctype": "Workspace",
            "module": "CosmOS",
            "label": ws_name,
            "title": ws_name,
            "app": "cosmos_core",
            "type": "Workspace",
            "public": 1,
            "roles": [
                {"role": "System Manager"},
                {"role": "Stock Manager"},
                {"role": "Accounts Manager"},
                {"role": "Stock User"},
            ],
        })
        ws.insert(ignore_permissions=True)
        print(f"  Created Workspace: {ws_name}")

    existing_charts = {c.chart_name for c in (ws.charts or [])}
    for cn in ["Market Rate Trend", "Items with Highest Variation"]:
        if cn not in existing_charts and frappe.db.exists("Dashboard Chart", cn):
            ws.append("charts", {"chart_name": cn, "label": cn})

    existing_cards = {c.number_card_name for c in (ws.number_cards or [])}
    for cn in ["Monthly Rate Entries"]:
        if cn not in existing_cards and frappe.db.exists("Number Card", cn):
            ws.append("number_cards", {"number_card_name": cn, "label": cn})

    existing_sc = {s.label for s in (ws.shortcuts or [])}
    shortcuts = [
        {"label": "Monthly Market Rate", "type": "DocType", "doc_type": "Monthly Market Rate", "link_to": "Monthly Market Rate"},
        {"label": "Item Master", "type": "DocType", "doc_type": "Item", "link_to": "Item"},
        {"label": "Item Price", "type": "DocType", "doc_type": "Item Price", "link_to": "Item Price"},
        {"label": "Stock Ledger", "type": "DocType", "doc_type": "Stock Ledger Entry", "link_to": "Stock Ledger Entry"},
        {"label": "Purchase Receipt", "type": "DocType", "doc_type": "Purchase Receipt", "link_to": "Purchase Receipt"},
    ]
    for s in shortcuts:
        if s["label"] not in existing_sc:
            ws.append("shortcuts", s)

    ws.save(ignore_permissions=True)
    print(f"  Updated Workspace: {ws_name}")


def update_existing_data():
    """Update any existing Monthly Market Rate entries with current rates"""
    entries = frappe.get_all("Monthly Market Rate", {"docstatus": 1}, pluck="name")
    for name in entries:
        doc = frappe.get_doc("Monthly Market Rate", name)
        for row in doc.items:
            if row.item:
                rates = get_item_rates(row.item)
                row.valuation_rate = rates.get("valuation_rate")
                row.last_purchase_rate = rates.get("last_purchase_rate")
                row.standard_rate = rates.get("standard_rate")
                if row.market_rate and row.valuation_rate:
                    row.variation_pct = round((row.market_rate - row.valuation_rate) / row.valuation_rate * 100, 2) if row.valuation_rate else 0
        doc.db_update()
    print(f"  Updated {len(entries)} existing entries with current rates")


def get_item_rates(item_code):
    rates = {"valuation_rate": 0, "last_purchase_rate": 0, "standard_rate": 0}
    if not item_code:
        return rates
    doc = frappe.get_cached_value("Item", item_code, ["valuation_rate", "last_purchase_rate", "standard_rate"], as_dict=1)
    if doc:
        for k in rates:
            rates[k] = doc.get(k) or 0
    return rates


if __name__ == "__main__":
    run()
