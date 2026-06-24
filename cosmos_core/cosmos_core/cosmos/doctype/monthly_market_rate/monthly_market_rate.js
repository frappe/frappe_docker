frappe.ui.form.on("Monthly Market Rate", {
    refresh: function(frm) {
        frm.add_custom_button(__("Fetch All Items"), function() {
            frappe.call({
                method: "cosmos_core.analysis.analysis.get_all_items_for_rate_entry",
                args: { item_type: "Both" },
                callback: function(r) {
                    if (r.message) {
                        frm.clear_table("items");
                        r.message.forEach(function(item) {
                            var row = frm.add_child("items");
                            row.item = item.name;
                            row.item_name = item.item_name;
                            row.item_type = item.item_type || "Both";
                            row.uom = item.stock_uom;
                        });
                        frm.refresh_field("items");
                        frappe.msgprint(__("{0} items added").format(r.message.length));
                    }
                }
            });
        }, __("Actions"));
    }
});
frappe.ui.form.on("Market Rate Item", {
    item: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.item) {
            frappe.call({
                method: "cosmos_core.cosmos.doctype.monthly_market_rate.monthly_market_rate.get_item_rates",
                args: { item_code: row.item },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, "valuation_rate", r.message.valuation_rate);
                        frappe.model.set_value(cdt, cdn, "last_purchase_rate", r.message.last_purchase_rate);
                        frappe.model.set_value(cdt, cdn, "standard_rate", r.message.standard_rate);
                    }
                }
            });
        }
    },
    market_rate: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.market_rate && row.valuation_rate) {
            var pct = ((row.market_rate - row.valuation_rate) / row.valuation_rate) * 100;
            frappe.model.set_value(cdt, cdn, "variation_pct", pct.toFixed(2));
        }
    }
}),
frappe.ui.form.on("Supplier Material Rate", {
    item: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.item) {
            frappe.model.set_value(cdt, cdn, "uom", "");
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Item",
                    filters: { name: row.item },
                    fieldname: "stock_uom"
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, "uom", r.message.stock_uom);
                    }
                }
            });
        }
    }
});
