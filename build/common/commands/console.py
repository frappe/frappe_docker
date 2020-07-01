import sys
import frappe
import IPython

from frappe.utils import get_sites


def console(site):
    "Start ipython console for a site"
    if site not in get_sites():
        print("Site {0} does not exist on the current bench".format(site))
        return

    frappe.init(site=site)
    frappe.connect()
    frappe.local.lang = frappe.db.get_default("lang")
    all_apps = frappe.get_installed_apps()
    for app in all_apps:
        locals()[app] = __import__(app)
    print("Apps in this namespace:\n{}".format(", ".join(all_apps)))
    IPython.embed(display_banner="", header="")


def main():
    site = sys.argv[-1]
    console(site)
    if frappe.redis_server:
        frappe.redis_server.connection_pool.disconnect()


if __name__ == "__main__":
    main()
