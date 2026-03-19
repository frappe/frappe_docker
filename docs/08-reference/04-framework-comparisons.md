---
title: Framework Comparisons
---

# Framework Comparisons

> **Note:** This section provides comparisons to other frameworks for developers familiar with them. If you're new to all frameworks, you can skip this section - the rest of the guide is self-contained.

## Frappe vs Django Concepts

### Project Structure Comparison

**Django Project:**

```python
myproject/
├── myproject/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── blog/              # Django app
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── shop/              # Django app
└── users/             # Django app
```

**Frappe Bench:**

```
bench/
├── apps/
│   ├── frappe/        # Core framework (comparable to Django itself)
│   ├── erpnext/       # Complete business app (like Django + DRF + Celery + admin)
│   ├── hrms/          # HR Management app
│   └── my_custom_app/ # YOUR custom app
└── sites/
    └── mysite.com/    # Site instance (like Django project + database)
        ├── site_config.json
        └── private/files/
```

### Conceptual Mapping

| Django             | Frappe            | Notes                                           |
| ------------------ | ----------------- | ----------------------------------------------- |
| Model              | DocType           | But includes UI, permissions, API automatically |
| View               | Controller method | Much less code needed                           |
| Admin              | Desk              | More powerful, auto-generated                   |
| DRF Serializer     | Built-in          | Automatic from DocType                          |
| Celery task        | Background job    | Built-in, no separate setup                     |
| signals            | hooks.py          | More structured                                 |
| Management command | bench command     | More discoverable                               |

### Key Architectural Differences

1. **Multi-tenancy**

   - Django: One app = one database (typically)
   - Frappe: One installation = many sites, each with own database

2. **Background Jobs**

   - Django: Requires Celery + Redis + worker setup
   - Frappe: Built-in queue system, just use `enqueue()`

3. **Real-time**

   - Django: Requires Channels + Redis + ASGI setup
   - Frappe: Socket.IO built-in, automatic for DocType updates

4. **Admin/Management**

   - Django: Admin for models, basic CRUD
   - Frappe: Full-featured Desk with reports, dashboards, permissions

5. **API**
   - Django: Manual DRF setup, serializers, views
   - Frappe: Automatic REST + RPC from DocType definitions

### Code Comparison Example

**Creating a "Customer" model:**

Django (requires ~50+ lines):

```python
# models.py
class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

# serializers.py
class CustomerSerializer(serializers.ModelSerializer):
    # ...

# views.py
class CustomerViewSet(viewsets.ModelViewSet):
    # ...

# urls.py
router.register(r'customers', CustomerViewSet)

# admin.py
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # ...
```

Frappe (DocType JSON + ~10 lines Python):

```json
// customer.json (auto-generated via UI or code)
{
  "name": "Customer",
  "fields": [
    { "fieldname": "customer_name", "fieldtype": "Data" },
    { "fieldname": "email", "fieldtype": "Data", "unique": 1 }
  ]
}
```

```python
# customer.py (only for custom business logic)
import frappe
from frappe.model.document import Document

class Customer(Document):
    def validate(self):
        # Custom validation logic only
        pass
```

✅ **Automatically includes:**

- REST API (`/api/resource/Customer`)
- List view, Form view
- Search, Filters, Sorting
- Permissions (Create, Read, Update, Delete)
- Audit trail (created_by, modified_by, versions)
- Print formats, Email templates

### When to Choose Frappe vs Django

**Choose Frappe when:**

- Building business applications (ERP, CRM, project management)
- Need multi-tenancy out-of-the-box
- Want rapid development with auto-generated UI
- Need role-based permissions and workflows
- Building for non-technical users who need customization

**Choose Django when:**

- Building consumer web apps (social media, e-commerce frontend)
- Need full control over every aspect
- Have highly custom UI requirements
- Team is already Django-expert
- Building API-only services

**Hybrid Approach:**
Many teams use both: Frappe for back-office/admin tools, Django for customer-facing web apps.
