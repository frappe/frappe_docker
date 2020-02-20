import os, frappe
from frappe.utils.background_jobs import start_worker

queue = os.environ.get("WORKER_TYPE", "default")
start_worker(queue, False)

exit(0)
