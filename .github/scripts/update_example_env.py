import os
import re


def get_versions():
    frappe_version = os.getenv("FRAPPE_VERSION")
    erpnext_version = os.getenv("ERPNEXT_VERSION")
    assert frappe_version, "No Frappe version set"
    assert erpnext_version, "No ERPNext version set"
    return frappe_version, erpnext_version


def update_env(frappe_version: str, erpnext_version: str):
    with open("example.env", "r+") as f:
        content = f.read()
        for env, var in (
            ("FRAPPE_VERSION", frappe_version),
            ("ERPNEXT_VERSION", erpnext_version),
        ):
            content = re.sub(rf"{env}=.*", f"{env}={var}", content)
        f.seek(0)
        f.truncate()
        f.write(content)


def main() -> int:
    update_env(*get_versions())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
