frappe.ui.form.on("Hikvision Device", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Sync Now"), function() {
                frappe.call({
                    method: "cosmos_core.hikvision.sync_service.sync_single_device",
                    args: { device_name: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__("Sync completed: {0} logs processed", [r.message]));
                            frm.reload_doc();
                        }
                    }
                });
            }, __("Actions"));

            frm.add_custom_button(__("Test Connection"), function() {
                frappe.call({
                    method: "cosmos_core.hikvision.isapi_client.test_connection",
                    args: { device_name: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                        }
                    }
                });
            }, __("Actions"));
        }
    }
});
