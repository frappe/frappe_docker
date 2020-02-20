import frappe
from frappe.utils.scheduler import start_scheduler

print("Starting background scheduler . . .")
start_scheduler()

exit(0)
