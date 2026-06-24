'''Analysis Division - Business Intelligence for Market Rate Analysis

Provides tools for:
- Monthly market rate tracking
- Variation analysis (market vs valuation vs purchase)
- Trend analysis and BI reports
'''
import frappe
from frappe.utils import today, getdate, add_months, flt


@frappe.whitelist()
def get_all_items_for_rate_entry(item_type="Both"):
    filters = {"disabled": 0}
    if item_type and item_type != "Both":
        filters["item_type"] = item_type
    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=["name", "item_name", "item_type", "stock_uom"]
    )
    return items


@frappe.whitelist()
def get_bi_summary():
    '''Get Business Intelligence summary data for the dashboard'''
    # Latest month with data
    latest = frappe.db.sql("""
        SELECT month FROM `tabMonthly Market Rate`
        WHERE docstatus = 1 ORDER BY month DESC LIMIT 1
    """)
    latest_month = latest[0][0] if latest else today()

    data = frappe.db.sql("""
        SELECT
            COUNT(*) as total_items,
            SUM(CASE WHEN mri.variation_pct > 0 THEN 1 ELSE 0 END) as items_above,
            SUM(CASE WHEN mri.variation_pct < 0 THEN 1 ELSE 0 END) as items_below,
            SUM(CASE WHEN mri.variation_pct = 0 THEN 1 ELSE 0 END) as items_equal,
            AVG(mri.variation_pct) as avg_variation,
            MAX(mri.variation_pct) as max_variation,
            MIN(mri.variation_pct) as min_variation,
            AVG(mri.market_rate) as avg_market_rate,
            AVG(mri.valuation_rate) as avg_valuation_rate
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabMarket Rate Item` mri ON mri.parent = mmr.name
        WHERE mmr.docstatus = 1 AND mmr.month = %s
    """, latest_month, as_dict=1)

    result = data[0] if data else {}
    result["latest_month"] = str(latest_month)
    result["total_months"] = frappe.db.count("Monthly Market Rate", {"docstatus": 1})
    return result


@frappe.whitelist()
def get_chart_data(months=6):
    '''Get monthly trend data for BI charts'''
    data = frappe.db.sql("""
        SELECT
            mmr.month,
            AVG(mri.market_rate) as avg_market,
            AVG(mri.valuation_rate) as avg_valuation,
            AVG(mri.last_purchase_rate) as avg_purchase,
            AVG(mri.variation_pct) as avg_variation
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabMarket Rate Item` mri ON mri.parent = mmr.name
        WHERE mmr.docstatus = 1
        GROUP BY mmr.month
        ORDER BY mmr.month DESC
        LIMIT %s
    """, int(months), as_dict=1)

    data.reverse()
    labels = [str(d.month) for d in data]
    datasets = [
        {"name": "Avg Market Rate", "values": [flt(d.avg_market) for d in data]},
        {"name": "Avg Valuation Rate", "values": [flt(d.avg_valuation) for d in data]},
        {"name": "Avg Purchase Rate", "values": [flt(d.avg_purchase) for d in data]},
    ]

    return {"labels": labels, "datasets": datasets}


@frappe.whitelist()
def get_item_category_breakdown(month=None):
    if not month:
        latest = frappe.db.sql("""
            SELECT month FROM `tabMonthly Market Rate`
            WHERE docstatus = 1 ORDER BY month DESC LIMIT 1
        """)
        month = latest[0][0] if latest else today()

    data = frappe.db.sql("""
        SELECT
            mri.item_type,
            COUNT(*) as count,
            AVG(mri.variation_pct) as avg_variation,
            AVG(mri.market_rate) as avg_market,
            AVG(mri.valuation_rate) as avg_valuation
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabMarket Rate Item` mri ON mri.parent = mmr.name
        WHERE mmr.docstatus = 1 AND mmr.month = %s
        GROUP BY mri.item_type
    """, month, as_dict=1)

    return data


@frappe.whitelist()
def get_top_variations(limit=10, month=None):
    if not month:
        latest = frappe.db.sql("""
            SELECT month FROM `tabMonthly Market Rate`
            WHERE docstatus = 1 ORDER BY month DESC LIMIT 1
        """)
        month = latest[0][0] if latest else today()

    data = frappe.db.sql("""
        SELECT
            mri.item, mri.item_name, mri.item_type,
            mri.market_rate, mri.valuation_rate,
            mri.variation_pct
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabMarket Rate Item` mri ON mri.parent = mmr.name
        WHERE mmr.docstatus = 1 AND mmr.month = %s
        ORDER BY ABS(mri.variation_pct) DESC
        LIMIT %s
    """, (month, int(limit)), as_dict=1)

    return data


@frappe.whitelist()
def get_item_price_history(item_code, months=12):
    data = frappe.db.sql("""
        SELECT
            mmr.month,
            mri.market_rate, mri.valuation_rate,
            mri.last_purchase_rate, mri.variation_pct
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabMarket Rate Item` mri ON mri.parent = mmr.name
        WHERE mmr.docstatus = 1 AND mri.item = %s
        ORDER BY mmr.month DESC
        LIMIT %s
    """, (item_code, int(months)), as_dict=1)

    data.reverse()
    return data


@frappe.whitelist()
def get_supplier_bi_summary(month=None):
    """BI summary for supplier rates"""
    if not month:
        latest = frappe.db.sql("""
            SELECT month FROM `tabMonthly Market Rate`
            WHERE docstatus = 1 ORDER BY month DESC LIMIT 1
        """)
        month = latest[0][0] if latest else frappe.utils.today()

    data = frappe.db.sql("""
        SELECT
            COUNT(DISTINCT smr.supplier) as total_suppliers,
            COUNT(DISTINCT smr.item) as items_with_supplier_rates,
            COUNT(*) as total_entries,
            AVG(smr.rate) as avg_supplier_rate,
            MIN(smr.rate) as min_rate,
            MAX(smr.rate) as max_rate,
            AVG(mri.market_rate) as avg_market_rate,
            ROUND((AVG(smr.rate) - AVG(mri.market_rate)) / AVG(mri.market_rate) * 100, 2) as avg_supplier_vs_market_pct
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabSupplier Material Rate` smr ON smr.parent = mmr.name
        LEFT JOIN `tabMarket Rate Item` mri
            ON mri.parent = mmr.name AND mri.item = smr.item
        WHERE mmr.docstatus = 1 AND mmr.month = %s
    """, month, as_dict=1)
    return data[0] if data else {}


@frappe.whitelist()
def get_supplier_trend_data(months=6):
    """Monthly trend of supplier vs market rates"""
    data = frappe.db.sql("""
        SELECT
            mmr.month,
            AVG(smr.rate) as avg_supplier_rate,
            AVG(mri.market_rate) as avg_market_rate,
            AVG(mri.valuation_rate) as avg_valuation_rate
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabSupplier Material Rate` smr ON smr.parent = mmr.name
        LEFT JOIN `tabMarket Rate Item` mri
            ON mri.parent = mmr.name AND mri.item = smr.item
        WHERE mmr.docstatus = 1
        GROUP BY mmr.month
        ORDER BY mmr.month DESC
        LIMIT %s
    """, int(months), as_dict=1)

    data.reverse()
    labels = [str(d.month) for d in data]
    datasets = [
        {"name": "Avg Supplier Rate", "values": [flt(d.avg_supplier_rate) for d in data]},
        {"name": "Avg Market Rate", "values": [flt(d.avg_market_rate) for d in data]},
        {"name": "Avg Valuation Rate", "values": [flt(d.avg_valuation_rate) for d in data]},
    ]
    return {"labels": labels, "datasets": datasets}


@frappe.whitelist()
def get_best_supplier_per_item(month=None):
    """Best (cheapest) supplier for each item"""
    if not month:
        latest = frappe.db.sql("""
            SELECT month FROM `tabMonthly Market Rate`
            WHERE docstatus = 1 ORDER BY month DESC LIMIT 1
        """)
        month = latest[0][0] if latest else frappe.utils.today()

    data = frappe.db.sql("""
        SELECT
            smr.item, mri.item_name, mri.item_type,
            smr.supplier, smr.supplier_name,
            smr.rate as supplier_rate,
            mri.market_rate, mri.valuation_rate,
            ROUND((smr.rate - mri.market_rate) / mri.market_rate * 100, 2) as vs_market_pct
        FROM `tabMonthly Market Rate` mmr
        JOIN `tabSupplier Material Rate` smr ON smr.parent = mmr.name
        LEFT JOIN `tabMarket Rate Item` mri
            ON mri.parent = mmr.name AND mri.item = smr.item
        WHERE mmr.docstatus = 1 AND mmr.month = %s
        AND (smr.item, smr.rate) IN (
            SELECT item, MIN(rate)
            FROM `tabSupplier Material Rate`
            WHERE parent = mmr.name
            GROUP BY item
        )
        ORDER BY vs_market_pct ASC
    """, month, as_dict=1)
    return data
