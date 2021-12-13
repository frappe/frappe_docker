import frappe.app
import frappe.database.db_manager
import frappe.utils.bench_helper


def patch_database_creator():
    """
    We need to interrupt Frappe site database creation to monkeypatch
    functions that resolve host for user that owns site database.
    In frappe_docker this was implemented in "new" command:
    https://github.com/frappe/frappe_docker/blob/c808ad1767feaf793a2d14541ac0f4d9cbab45b3/build/frappe-worker/commands/new.py#L87
    """

    frappe.database.db_manager.DbManager.get_current_host = lambda self: "%"


def main() -> int:
    patch_database_creator()
    frappe.utils.bench_helper.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
