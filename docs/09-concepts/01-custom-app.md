---
title: Custom Apps
---

# Frappe Custom Applications

## What Are Frappe Custom Apps?

Custom apps are self-contained, modular business applications that extend Frappe's functionality. They follow a convention-over-configuration approach where the framework provides most boilerplate automatically.

## Custom App Structure

```
my_custom_app/
├── hooks.py                          # App configuration and hooks into Frappe lifecycle
├── modules.txt                       # List of business modules in this app
├── my_custom_app/
│   ├── __init__.py
│   ├── config/
│   │   └── desktop.py                # Desktop workspace icons and shortcuts
│   ├── my_module/                    # Business domain module (e.g., sales, inventory)
│   │   ├── doctype/                  # Document Types (data models)
│   │   │   ├── customer/
│   │   │   │   ├── customer.py       # Python controller (business logic)
│   │   │   │   ├── customer.json     # Model definition (schema, validation)
│   │   │   │   └── customer.js       # Frontend logic (UI interactions)
│   │   └── page/                     # Custom pages (dashboards, reports)
│   ├── public/                       # Static assets (CSS, JS, images)
│   ├── templates/                    # Jinja2 templates for web pages
│   └── www/                          # Web pages accessible via routes
└── requirements.txt                  # Python package dependencies
```

## Built-in Features (Auto-generated)

Every Frappe app automatically includes:

- **REST API** - Automatic CRUD endpoints from DocType definitions
- **Permissions system** - Row-level and field-level access control
- **Audit trails** - Automatic version tracking and change history
- **Custom fields** - Runtime field additions without code changes
- **Workflows** - Configurable approval and state management
- **Reports** - Query builder and report designer
- **Print formats** - PDF generation with custom templates
- **Email integration** - Template-based email sending
- **File attachments** - Document attachment management

## Creating Custom Apps

```bash
# Enter the development container
docker exec -it <container_name> bash

# Create new app (interactive prompts will ask for details)
bench new-app my_custom_app

# Install app to a site
bench --site mysite.com install-app my_custom_app

# Create a new DocType (data model)
bench --site mysite.com console
>>> bench.new_doc("DocType", {...})
# Or use the web UI: Setup → Customize → DocType → New
```
