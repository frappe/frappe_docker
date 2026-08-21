
	def before_insert(self):
		# Walk-in fast path: a typed, unknown customer becomes a Customer record
		# (with the dialog's contact number) instead of a broken link error.
		if self.customer and not frappe.db.exists("Customer", self.customer):
			customer = frappe.new_doc("Customer")
			customer.customer_name = self.customer
			customer.customer_group = frappe.db.get_value("Customer Group", {"is_group": 0})
			customer.territory = frappe.db.get_value("Territory", {"is_group": 0})
			customer.mobile_no = self.contact_number
			customer.insert(ignore_permissions=True)
			self.customer = customer.name
