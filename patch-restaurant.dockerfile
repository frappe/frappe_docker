FROM custom-erpnext:v16.6.0
USER frappe
RUN sed -i "s/Sales Taxes And Charges/Sales Taxes and Charges/; s/tax += item.tax_amount$/tax += (item.tax_amount or 0)/; s/amount += item.amount$/amount += (item.amount or 0)/; s/\"rate\", \"amount\"/\"rate\", \"tax_amount\"/; s/tax\.amount or 0/tax.tax_amount or 0/" apps/restaurant_management/restaurant_management/restaurant_management/doctype/table_order/table_order.py
RUN sed -i "s/RM = new RestaurantManage(wrapper);/RM = window.RM = new RestaurantManage(wrapper);/" apps/restaurant_management/restaurant_management/restaurant_management/page/restaurant_manage/restaurant_manage.js
