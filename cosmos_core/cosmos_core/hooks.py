app_name = "cosmos_core"
app_title = "CosmOS"
app_publisher = "Protect PLast LLC Middle East"
app_description = "CosmOS For Protect PLast LLC Middle East"
app_email = "saleelhussain@gmail.com"
app_license = "gpl-2.0"

# Branding
app_logo_url = "/assets/cosmos_core/images/cosmos-logo.png"
app_icon = "/assets/cosmos_core/images/cosmos-icon.png"
app_splash = "/assets/cosmos_core/images/cosmos-logo.png"
app_email_splash = "/assets/cosmos_core/images/cosmos-email-logo.png"

# Replace Frappe brand everywhere
app_include_css = "/assets/cosmos_core/css/cosmos.css"

# Help dropdown items (replaces Frappe defaults)
standard_help_items = [
    {
        "item_label": "CosmOS Support",
        "item_type": "Route",
        "route": "/support",
        "is_standard": 1,
    },
    {
        "item_label": "About CosmOS",
        "item_type": "Action",
        "action": "frappe.ui.toolbar.show_about()",
        "is_standard": 1,
    },
    {
        "item_label": "Keyboard Shortcuts",
        "item_type": "Action",
        "action": "frappe.ui.toolbar.show_shortcuts(event)",
        "is_standard": 1,
    },
    {
        "item_label": "System Health",
        "item_type": "Route",
        "route": "/desk/system-health-report",
        "is_standard": 1,
    },
]

# Scheduled tasks
scheduler_events = {
    "cron": {
        "0 6 * * *": [
            "cosmos_core.visa_alerts.send_visa_expiry_alerts"
        ]
    },
    "all": [
        "cosmos_core.hikvision.sync_service.sync_all_devices"
    ],
}
