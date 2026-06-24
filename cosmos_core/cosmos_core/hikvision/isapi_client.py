import frappe
import requests
from requests.auth import HTTPDigestAuth


class HikvisionISAPIClient:
    def __init__(self, device):
        self.device = device
        protocol = "https" if device.use_ssl else "http"
        self.base_url = f"{protocol}://{device.ip_address}:{device.port}"
        password = device.get_password("password") or device.password
        self.auth = HTTPDigestAuth(device.username, password)

    def _get(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, auth=self.auth, timeout=15)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Hikvision GET {url}: {e}", "Hikvision ISAPI")
            raise

    def _post(self, endpoint, data):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.post(url, auth=self.auth, json=data, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Hikvision POST {url}: {e}", "Hikvision ISAPI")
            raise

    def get_device_info(self):
        return self._get("/ISAPI/System/deviceInfo").text

    def get_attendance_records(self, start_time, end_time, max_results=100):
        all_records = []
        position = 0
        fmt = "%Y-%m-%dT%H:%M:%S"
        st = start_time.strftime(fmt) if hasattr(start_time, "strftime") else str(start_time)
        et = end_time.strftime(fmt) if hasattr(end_time, "strftime") else str(end_time)

        while True:
            payload = {
                "AcsEventCond": {
                    "searchID": frappe.generate_hash(length=12),
                    "searchResultPosition": position,
                    "maxResults": min(max_results, 100),
                    "major": 0,
                    "minor": 0,
                    "startTime": st,
                    "endTime": et,
                }
            }
            try:
                resp = self._post("/ISAPI/AccessControl/AcsEvent?format=json", payload)
                data = resp.json()
            except Exception:
                try:
                    resp = self._post("/ISAPI/Attendance/RecordSearch?format=json", payload)
                    data = resp.json()
                except Exception:
                    break

            info_list = data.get("AcsEvent", {}).get("InfoList", [])
            if isinstance(info_list, dict):
                info_list = [info_list]
            if not info_list:
                break

            for item in info_list:
                emp_no = item.get("employeeNoString", "") or item.get("employeeNo", "")
                name = item.get("name", "")
                time_raw = item.get("time", "")
                att_status = item.get("attendanceStatus", "")
                if not time_raw:
                    continue
                pt = "IN" if str(att_status) in ("1", "in", "IN") else "OUT" if str(att_status) in ("2", "out", "OUT") else ""
                all_records.append({
                    "employee_user_id": emp_no,
                    "employee_name": name,
                    "punch_time": time_raw.replace("T", " ").split("+")[0].split(".")[0],
                    "punch_type": pt,
                    "device_id": item.get("deviceId", ""),
                    "attendance_status": str(att_status),
                    "log_id": str(item.get("serialNo", frappe.generate_hash(length=8))),
                })

            position += len(info_list)
            total = data.get("AcsEvent", {}).get("totalMatches", 0)
            if position >= total:
                break

        return all_records


@frappe.whitelist()
def test_connection(device_name):
    device = frappe.get_doc("Hikvision Device", device_name)
    try:
        client = HikvisionISAPIClient(device)
        info = client.get_device_info()
        if info:
            frappe.db.set_value("Hikvision Device", device_name, "last_sync_status", "Success")
            return "Connected successfully."
        return "Connected but no info received."
    except Exception as e:
        frappe.db.set_value("Hikvision Device", device_name, "last_sync_status", "Failed")
        return f"Connection failed: {e}"
