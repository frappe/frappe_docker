import frappe
from frappe.model.document import Document

class MonthlyMarketRate(Document):
    def validate(self):
        if not self.title:
            self.title = "Market Rates - " + str(self.month)
        self.set_item_rates()

    def on_submit(self):
        self.update_variations()

    def set_item_rates(self):
        for row in self.items:
            if row.item:
                item_rates = get_item_rates(row.item)
                row.valuation_rate = item_rates.get("valuation_rate")
                row.last_purchase_rate = item_rates.get("last_purchase_rate")
                row.standard_rate = item_rates.get("standard_rate")

    def update_variations(self):
        for row in self.items:
            if row.market_rate and row.valuation_rate:
                row.variation_pct = round((row.market_rate - row.valuation_rate) / row.valuation_rate * 100, 2) if row.valuation_rate else 0


@frappe.whitelist()
def get_item_rates(item_code):
    rates = {"valuation_rate": 0, "last_purchase_rate": 0, "standard_rate": 0}
    if not item_code:
        return rates
    doc = frappe.get_cached_value("Item", item_code, ["valuation_rate", "last_purchase_rate", "standard_rate"], as_dict=1)
    if doc:
        rates.update({k: v or 0 for k, v in doc.items()})
    return rates


@frappe.whitelist()
def get_variation_report(month):
    data = frappe.db.sql("""
        SELECT
            mri.item, mri.item_name, mri.item_type,
            mri.market_rate, mri.valuation_rate,
            mri.last_purchase_rate, mri.standard_rate,
            mri.variation_pct, mri.uom,
            mmr.month, mmr.name as entry_name
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabMarket Rate Item` mri ON mri.parent = mmr.name
        WHERE mmr.docstatus = 1 AND mmr.month = %s
        ORDER BY ABS(mri.variation_pct) DESC
    """, month, as_dict=1)
    return data


@frappe.whitelist()
def get_best_supplier_rates(month=None):
    """Get best (lowest) supplier rate for each item in a given month"""
    if not month:
        latest = frappe.db.sql("""
            SELECT month FROM `tabMonthly Market Rate`
            WHERE docstatus = 1 ORDER BY month DESC LIMIT 1
        """)
        month = latest[0][0] if latest else frappe.utils.today()

    data = frappe.db.sql("""
        SELECT
            smr.item, smr.supplier, smr.rate as supplier_rate,
            smr.uom, smr.supplier_name,
            mri.market_rate, mri.valuation_rate,
            mri.variation_pct,
            ROUND((smr.rate - mri.market_rate) / mri.market_rate * 100, 2) as supplier_vs_market_pct
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabSupplier Material Rate` smr ON smr.parent = mmr.name
        LEFT JOIN `tabMarket Rate Item` mri
            ON mri.parent = mmr.name AND mri.item = smr.item
        WHERE mmr.docstatus = 1 AND mmr.month = %s
        ORDER BY smr.item, smr.rate ASC
    """, month, as_dict=1)
    return data


@frappe.whitelist()
def get_supplier_price_comparison(month=None):
    """Get items with multiple supplier quotes showing price spread"""
    if not month:
        latest = frappe.db.sql("""
            SELECT month FROM `tabMonthly Market Rate`
            WHERE docstatus = 1 ORDER BY month DESC LIMIT 1
        """)
        month = latest[0][0] if latest else frappe.utils.today()

    data = frappe.db.sql("""
        SELECT
            smr.item,
            mri.item_name,
            mri.market_rate,
            MIN(smr.rate) as min_supplier_rate,
            MAX(smr.rate) as max_supplier_rate,
            AVG(smr.rate) as avg_supplier_rate,
            COUNT(DISTINCT smr.supplier) as supplier_count,
            ROUND((MAX(smr.rate) - MIN(smr.rate)) / AVG(smr.rate) * 100, 2) as price_spread_pct,
            ROUND((MIN(smr.rate) - mri.market_rate) / mri.market_rate * 100, 2) as best_supplier_vs_market_pct
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabSupplier Material Rate` smr ON smr.parent = mmr.name
        LEFT JOIN `tabMarket Rate Item` mri
            ON mri.parent = mmr.name AND mri.item = smr.item
        WHERE mmr.docstatus = 1 AND mmr.month = %s
        GROUP BY smr.item
        ORDER BY price_spread_pct DESC
    """, month, as_dict=1)
    return data
