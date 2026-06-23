import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from datetime import datetime


class WPSSalaryFile(Document):
    def validate(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            frappe.throw("Start Date cannot be after End Date")
        self.calculate_totals()

    def calculate_totals(self):
        self.total_employees = len(self.employees or [])
        self.total_salary_amount = sum(d.salary_amount or 0 for d in (self.employees or []))

    def on_submit(self):
        self.generate_wps_file_content()

    def on_cancel(self):
        pass

    def generate_wps_file_content(self):
        if not self.employees:
            frappe.throw("No employees found in this WPS file")

        company = frappe.get_doc("Company", self.company)
        lines = []

        # Record Type 1: Header
        header = self._make_header(company)
        lines.append(header)

        # Record Type 2: Employee details
        for emp in self.employees:
            lines.append(self._make_detail(emp, company))

        # Record Type 3: Trailer
        trailer = self._make_trailer()
        lines.append(trailer)

        content = "\r\n".join(lines)

        # Generate filename and save
        filename = f"WPS_{self.company}_{self.start_date}_{self.end_date}.txt"
        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "is_private": 1,
            "content": content,
            "attached_to_doctype": self.doctype,
            "attached_to_name": self.name,
        })
        _file.save(ignore_permissions=True)
        frappe.msgprint(f"WPS file generated: {filename}")

    def _make_header(self, company):
        rec_type = "1"
        file_type = "S"
        bank_code = self._get_bank_code(company)
        branch_code = "001"
        company_id = (company.name or "").ljust(20)[:20]
        company_name = (company.company_name or "").ljust(40)[:40]
        file_date = datetime.now().strftime("%d%m%Y")
        total_emp = str(self.total_employees or 0).rjust(6, "0")
        total_amt = f"{self.total_salary_amount or 0:.2f}".replace(".", "").rjust(15, "0")
        filler = " " * 154
        return f"{rec_type}{file_type}{bank_code}{branch_code}{company_id}{company_name}{file_date}{total_emp}{total_amt}{filler}"

    def _make_detail(self, emp, company):
        rec_type = "2"
        emp_id = (emp.employee or "").ljust(20)[:20]
        emp_name = (emp.employee_name or "").ljust(40)[:40]
        bank_code = self._get_bank_code(company)
        branch_code = "001"
        account_no = (emp.iban or emp.bank_account_no or "").ljust(20)[:20]
        salary_amt = f"{emp.salary_amount or 0:.2f}".replace(".", "").rjust(15, "0")
        filler = " " * 160
        return f"{rec_type}{emp_id}{emp_name}{bank_code}{branch_code}{account_no}{salary_amt}{filler}"

    def _make_trailer(self):
        rec_type = "3"
        total_recs = str(self.total_employees or 0).rjust(6, "0")
        total_amt = f"{self.total_salary_amount or 0:.2f}".replace(".", "").rjust(15, "0")
        filler = " " * 237
        return f"{rec_type}{total_recs}{total_amt}{filler}"

    def _get_bank_code(self, company):
        bank_code = frappe.db.get_value("Bank Account", {"company": company.name, "is_company_account": 1}, "bank")
        if bank_code and frappe.db.exists("Bank", bank_code):
            return bank_code.ljust(3)[:3]
        return "000"
