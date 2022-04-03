from __future__ import annotations

import click
import click.exceptions
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


def patch_click_usage_error():
    bits: tuple[str, ...] = (
        click.style(
            "Only Frappe framework bench commands are available in container setup.",
            fg="yellow",
            bold=True,
        ),
        "https://frappeframework.com/docs/v13/user/en/bench/frappe-commands",
    )
    notice = "\n".join(bits)

    def format_message(self: click.exceptions.UsageError):
        if "No such command" in self.message:
            return f"{notice}\n\n{self.message}"
        return self.message

    click.exceptions.UsageError.format_message = format_message


def main() -> int:
    patch_database_creator()
    patch_click_usage_error()
    frappe.utils.bench_helper.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
