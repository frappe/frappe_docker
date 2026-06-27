import frappe
from frappe.utils import today, add_days, getdate


def send_visa_expiry_alerts():
    """Daily scheduler job: check for visas expiring within 30 days and send alerts."""
    threshold = add_days(today(), 30)

    expiring_visas = frappe.db.sql("""
        SELECT
            evd.name,
            evd.employee,
            evd.visa_type,
            evd.expiry_date,
            evd.passport_number
        FROM `tabEmployee Visa Detail` evd
        WHERE evd.expiry_date BETWEEN %s AND %s
          AND evd.status != 'Expired'
    """, (today(), threshold), as_dict=True)

    for visa in expiring_visas:
        employee_name = frappe.db.get_value("Employee", visa.employee, "employee_name")
        days_left = (getdate(visa.expiry_date) - getdate(today())).days

        subject = f"Visa Expiry Alert - {employee_name}"
        message = f"""
<h3>Visa Expiry Alert</h3>
<p><b>Employee:</b> {employee_name}</p>
<p><b>Visa Type:</b> {visa.visa_type}</p>
<p><b>Passport Number:</b> {visa.passport_number}</p>
<p><b>Expiry Date:</b> {visa.expiry_date}</p>
<p><b>Days Remaining:</b> {days_left} days</p>
<p>Please take necessary action to renew the visa.</p>
        """

        # Send to users with HR Manager role
        recipients = frappe.db.sql_list("""
            SELECT DISTINCT parent FROM `tabHas Role`
            WHERE role IN ('HR Manager', 'HR User', 'System Manager')
              AND parent != 'Guest'
        """)

        for recipient in recipients:
            try:
                frappe.sendmail(
                    recipients=recipient,
                    subject=subject,
                    message=message,
                    reference_doctype="Employee Visa Detail",
                    reference_name=visa.name,
                )
            except Exception:
                frappe.log_error(
                    title="Visa Expiry Alert Failed",
                    message=f"Failed to send alert for {visa.name}"
                )

        # Update status to "About to Expire"
        frappe.db.set_value("Employee Visa Detail", visa.name, "status", "About to Expire", update_modified=False)

    frappe.db.commit()
    return len(expiring_visas)
