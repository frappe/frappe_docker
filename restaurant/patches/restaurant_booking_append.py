
	def _ensure_walkin_customer(self):
		# v16 validates links before any doc hook fires, so insert()/save() are
		# overridden to first turn a typed walk-in name into a real Customer.
		if self.customer and not frappe.db.exists("Customer", self.customer):
			customer = frappe.new_doc("Customer")
			customer.customer_name = self.customer
			customer.customer_group = frappe.db.get_value("Customer Group", {"is_group": 0})
			customer.territory = frappe.db.get_value("Territory", {"is_group": 0})
			customer.mobile_no = self.contact_number
			customer.insert(ignore_permissions=True)
			self.customer = customer.name

	def insert(self, *args, **kwargs):
		self._ensure_walkin_customer()
		return super().insert(*args, **kwargs)

	def save(self, *args, **kwargs):
		self._ensure_walkin_customer()
		return super().save(*args, **kwargs)
