import os
from frappe.utils.background_jobs import start_worker


def main():
    queue = os.environ.get("WORKER_TYPE", "default")
    start_worker(queue, False)
    exit(0)


if __name__ == "__main__":
    main()
