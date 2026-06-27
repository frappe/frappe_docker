import frappe
from frappe.utils import now_datetime, get_datetime
from datetime import datetime, timedelta


def sync_all_devices():
    devices = frappe.get_all("Hikvision Device", filters={"is_active": 1}, pluck="name")
    for device_name in devices:
        try:
            device = frappe.get_doc("Hikvision Device", device_name)
            interval = device.sync_interval or 5
            if device.last_sync_time:
                last_sync = get_datetime(device.last_sync_time)
                if now_datetime() < last_sync + timedelta(minutes=interval):
                    continue
            sync_single_device(device_name)
        except Exception as e:
            frappe.log_error(f"Error syncing Hikvision device {device_name}: {e}", "Hikvision Sync")


@frappe.whitelist()
def sync_single_device(device_name):
    from cosmos_core.hikvision.isapi_client import HikvisionISAPIClient

    device = frappe.get_doc("Hikvision Device", device_name)
    client = HikvisionISAPIClient(device)

    sync_log = frappe.get_doc({
        "doctype": "Hikvision Sync Log",
        "device": device_name,
        "status": "In Progress",
        "start_time": now_datetime(),
        "end_time": now_datetime(),
    })
    sync_log.insert(ignore_permissions=True)
    frappe.db.commit()

    try:
        end_time = now_datetime()
        if device.last_sync_time:
            start_time = get_datetime(device.last_sync_time) - timedelta(minutes=1)
        else:
            start_time = end_time - timedelta(days=7)

        records = client.get_attendance_records(start_time, end_time)
        created_count = 0

        for record in records:
            log_id = record.get("log_id") or frappe.generate_hash(length=12)
            if frappe.db.exists("Hikvision Attendance Log", {"log_id": log_id}):
                continue

            att_log = frappe.get_doc({
                "doctype": "Hikvision Attendance Log",
                "device": device_name,
                "employee_user_id": record["employee_user_id"],
                "employee_name": record.get("employee_name", ""),
                "punch_time": record["punch_time"],
                "punch_type": record.get("punch_type", ""),
                "device_id": record.get("device_id", ""),
                "log_id": log_id,
                "attendance_status": record.get("attendance_status", ""),
            })
            att_log.insert(ignore_permissions=True)
            created_count += 1

            if att_log.punch_type in ("IN", "OUT"):
                try:
                    _create_employee_checkin(att_log)
                    att_log.db_set("is_synced", 1)
                except Exception as e:
                    att_log.db_set("error_log", str(e))

        frappe.db.set_value("Hikvision Device", device_name, "last_sync_time", now_datetime())
        frappe.db.set_value("Hikvision Device", device_name, "last_sync_status", "Success")

        sync_log.db_set({
            "status": "Success",
            "end_time": now_datetime(),
            "records_fetched": len(records),
            "records_created": created_count,
        })
        return str(len(records))

    except Exception as e:
        frappe.db.set_value("Hikvision Device", device_name, "last_sync_status", "Failed")
        sync_log.db_set({"status": "Failed", "end_time": now_datetime(), "error_message": str(e)})
        frappe.log_error(f"Hikvision sync failed for {device_name}: {e}", "Hikvision Sync")
        raise


def _create_employee_checkin(att_log):
    employee = frappe.db.get_value(
        "Employee",
        {"attendance_device_id": att_log.employee_user_id, "status": "Active"},
        "name",
    )
    if not employee:
        att_log.db_set("error_log", f"No active employee mapped for user ID: {att_log.employee_user_id}")
        return

    if frappe.db.exists("Employee Checkin", {"employee": employee, "time": att_log.punch_time}):
        return

    checkin = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee,
        "log_type": att_log.punch_type,
        "time": att_log.punch_time,
        "device_id": f"Hikvision-{att_log.device or att_log.device_id}",
    })
    checkin.insert(ignore_permissions=True)
    att_log.db_set("employee_checkin", checkin.name)
