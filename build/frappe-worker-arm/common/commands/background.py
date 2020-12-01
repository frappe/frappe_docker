from frappe.utils.scheduler import start_scheduler


def main():
    print("Starting background scheduler . . .")
    start_scheduler()
    exit(0)


if __name__ == "__main__":
    main()
