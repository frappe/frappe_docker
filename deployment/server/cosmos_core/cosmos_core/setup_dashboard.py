import frappe


def run():
    print("=== Setting up CosmoERP Dashboard ===")
    create_number_cards()
    create_dashboard_charts()
    create_dashboard_workspace()
    setup_hr_shortcuts()
    print("=== Dashboard setup complete ===")


def create_number_cards():
    cards = [
        {"label": "Total Employees", "document_type": "Employee", "function": "Count", "filter": "[]", "color": "#24963f"},
        {"label": "Active Employees", "document_type": "Employee", "function": "Count", "filter": "[[\"Employee\",\"status\",\"=\",\"Active\"]]", "color": "#24963f"},
        {"label": "Employees on Leave Today", "document_type": "Leave Application", "function": "Count", "filter": "[[\"Leave Application\",\"status\",\"=\",\"Approved\"],[\"Leave Application\",\"from_date\",\"<=\",\"Today\"],[\"Leave Application\",\"to_date\",\">=\",\"Today\"]]", "color": "#ff6b6b"},
        {"label": "Biometric Devices", "document_type": "Hikvision Device", "function": "Count", "filter": "[]", "color": "#e17055"},
        {"label": "Total Users", "document_type": "User", "function": "Count", "filter": "[[\"User\",\"enabled\",\"=\",1],[\"User\",\"name\",\"!=\",\"Administrator\"],[\"User\",\"name\",\"!=\",\"Guest\"]]", "color": "#3498db"},
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
                    "color": card_data.get("color", "#24963f"),
                    "type": "Document Type",
                    "show_percentage_stats": 1,
                    "stats_time_interval": "Daily",
                    "aggregate_function_based_on": "creation",
                })
                doc.insert(ignore_permissions=True)
                print(f"  Created Number Card: {name}")
            except Exception as e:
                print(f"  Skipped {name}: {e}")


def create_dashboard_charts():
    charts = [
        {"chart_name": "Employees by Department", "chart_type": "Group By", "group_by_based_on": "department", "aggregate_function_based_on": "name", "group_by_type": "Count", "type": "Bar", "document_type": "Employee", "color": "#24963f"},
        {"chart_name": "Employees by Employment Type", "chart_type": "Group By", "group_by_based_on": "employment_type", "aggregate_function_based_on": "name", "group_by_type": "Count", "type": "Pie", "document_type": "Employee", "color": "#6c5ce7"},
        {"chart_name": "Employee Gender Distribution", "chart_type": "Group By", "group_by_based_on": "gender", "aggregate_function_based_on": "name", "group_by_type": "Count", "type": "Percentage", "document_type": "Employee", "color": "#00b894"},
        {"chart_name": "Employees by Branch", "chart_type": "Group By", "group_by_based_on": "branch", "aggregate_function_based_on": "name", "group_by_type": "Count", "type": "Bar", "document_type": "Employee", "color": "#fdcb6e"},
        {"chart_name": "Biometric Devices Status", "chart_type": "Group By", "group_by_based_on": "last_sync_status", "aggregate_function_based_on": "name", "group_by_type": "Count", "type": "Bar", "document_type": "Hikvision Device", "color": "#e17055"},
    ]
    for chart_data in charts:
        name = chart_data["chart_name"]
        if not frappe.db.exists("Dashboard Chart", name):
            try:
                doc = frappe.get_doc({
                    "doctype": "Dashboard Chart",
                    "chart_name": name,
                    "chart_type": chart_data["chart_type"],
                    "group_by_based_on": chart_data["group_by_based_on"],
                    "aggregate_function_based_on": chart_data.get("aggregate_function_based_on"),
                    "group_by_type": chart_data.get("group_by_type", "Count"),
                    "type": chart_data["type"],
                    "document_type": chart_data["document_type"],
                    "color": chart_data.get("color", "#24963f"),
                    "is_public": 1,
                    "filters_json": "[]",
                    "number_of_groups": 0,
                })
                doc.insert(ignore_permissions=True)
                print(f"  Created Chart: {name}")
            except Exception as e:
                print(f"  Skipped {name}: {e}")


def create_dashboard_workspace():
    ws_name = "CosmoERP Dashboard"
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
            "roles": [{"role": "System Manager"}, {"role": "HR Manager"}, {"role": "HR User"}],
        })
        ws.insert(ignore_permissions=True)
        print(f"  Created Workspace: {ws_name}")

    existing_charts = {c.chart_name for c in (ws.charts or [])}
    for cn in ["Employees by Department", "Employees by Employment Type", "Employee Gender Distribution", "Employees by Branch", "Biometric Devices Status"]:
        if cn not in existing_charts and frappe.db.exists("Dashboard Chart", cn):
            ws.append("charts", {"chart_name": cn, "label": cn})

    existing_cards = {c.number_card_name for c in (ws.number_cards or [])}
    for card_name in ["Total Employees", "Active Employees", "Employees on Leave Today", "Biometric Devices", "Total Users"]:
        if card_name not in existing_cards and frappe.db.exists("Number Card", card_name):
            ws.append("number_cards", {"number_card_name": card_name, "label": card_name})

    ws.save(ignore_permissions=True)
    print(f"  Updated Workspace: {ws_name}")


def setup_hr_shortcuts():
    ws_name = "CosmoERP Dashboard"
    if not frappe.db.exists("Workspace", ws_name):
        return
    ws = frappe.get_doc("Workspace", ws_name)
    existing = {s.label for s in (ws.shortcuts or [])}
    items = [
        {"label": "Employee Master", "type": "DocType", "doc_type": "Employee", "link_to": "Employee"},
        {"label": "Attendance", "type": "DocType", "doc_type": "Attendance", "link_to": "Attendance"},
        {"label": "Leave Application", "type": "DocType", "doc_type": "Leave Application", "link_to": "Leave Application"},
        {"label": "Payroll Entry", "type": "DocType", "doc_type": "Payroll Entry", "link_to": "Payroll Entry"},
        {"label": "Hikvision Devices", "type": "DocType", "doc_type": "Hikvision Device", "link_to": "Hikvision Device"},
        {"label": "Biometric Logs", "type": "DocType", "doc_type": "Hikvision Attendance Log", "link_to": "Hikvision Attendance Log"},
        {"label": "WPS Salary File", "type": "DocType", "doc_type": "WPS Salary File", "link_to": "WPS Salary File"},
        {"label": "Employee Checkin", "type": "DocType", "doc_type": "Employee Checkin", "link_to": "Employee Checkin"},
    ]
    for item in items:
        if item["label"] not in existing:
            ws.append("shortcuts", item)
    ws.save(ignore_permissions=True)
    print(f"  Shortcuts added to {ws_name}")
