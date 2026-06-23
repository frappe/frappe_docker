import frappe, re

def rebrand(html):
    """Replace all brand references."""
    html = html.replace("ERPNext", "CosmOS")
    html = html.replace("Erpnext", "CosmOS")
    html = html.replace("erpnext", "cosmos")
    html = html.replace("Frappe Framework", "CosmOS Framework")
    html = html.replace("Frappe HR", "CosmosERP HR")
    html = html.replace("Frappe ", "CosmOS ")
    html = html.replace("frappe ", "CosmOS ")
    html = html.replace("/cosmos/", "/erpnext/")
    html = html.replace("href=\"/docs/", "href=\"https://docs.cosmoserp.com/")
    html = re.sub(r'href="[^"]*erpnext[^"]*"', '', html)
    html = html.replace("href=\"/", "href=\"/app/")
    html = html.replace("/app//app/", "/app/")
    html = html.replace("https://docs.cosmoserp.com/", "")
    return html

def update_article(route, content):
    """Update or create a help article."""
    content = rebrand(content)
    existing = frappe.db.get_value("Help Article", {"route": route})
    if existing:
        frappe.db.set_value("Help Article", existing, "content", content)
        print(f"  Updated: {route}")
    else:
        print(f"  SKIP (no article): {route}")

def run():
    print("=== Updating articles with official documentation content ===\n")
    
    # ── Accounts / Finance ──
    update_article("chart-of-accounts", """<h1>Chart of Accounts</h1>
<p>The Chart of Accounts is the backbone of the financial system. It organises all financial transactions into a hierarchical structure of groups and ledgers.</p>

<h2>Account Types</h2>
<ul>
<li><strong>Assets</strong> – Current Assets (cash, bank, receivables) and Fixed Assets (property, equipment)</li>
<li><strong>Liabilities</strong> – Current Liabilities (payables, taxes) and Long-term Liabilities (loans)</li>
<li><strong>Equity</strong> – Owner's capital, retained earnings</li>
<li><strong>Income</strong> – Revenue from sales, services, and other income</li>
<li><strong>Expenses</strong> – Operating expenses, cost of goods sold, administrative costs</li>
</ul>

<h2>How to Create an Account</h2>
<ol>
<li>Go to Chart of Accounts via Awesome Bar</li>
<li>Click Add New Account</li>
<li>Select the parent account and enter the account name</li>
<li>Choose the account type (Asset, Liability, Equity, Income, or Expense)</li>
<li>Save – the account is ready for transactions</li>
</ol>

<h2>Managing Accounts</h2>
<ul>
<li><strong>Group Accounts</strong> summarise child ledgers (e.g., "Current Assets" groups "Cash" and "Bank")</li>
<li><strong>Ledger Accounts</strong> are leaf-level accounts where transactions are posted</li>
<li>Accounts can be frozen to prevent further postings</li>
<li>Set account currency for multi-currency ledgers</li>
</ul>""")

    update_article("journal-entries", """<h1>Journal Entries</h1>
<p>A Journal Entry is a standard accounting transaction that affects multiple accounts where the sum of debits equals the sum of credits.</p>

<h2>When to Use Journal Entries</h2>
<ul>
<li>Opening balances when migrating from another system</li>
<li>Adjustments and corrections</li>
<li>Inter-account transfers</li>
<li>Accruals and prepayments</li>
<li>Depreciation entries</li>
<li>Credit notes and debit notes</li>
<li>Contra entries (cash to bank, etc.)</li>
</ul>

<h2>Creating a Journal Entry</h2>
<ol>
<li>Go to Journal Entry → New</li>
<li>Select the Entry Type (Journal Entry, Bank Entry, Cash Entry, Credit Card Entry, Contra Entry, etc.)</li>
<li>Set the Posting Date</li>
<li>In the Accounting Entries table, add rows with Account, Debit, and Credit amounts</li>
<li>Optionally set Party Type and Party for customer/supplier entries</li>
<li>Total debits must equal total credits</li>
<li>Save and Submit to post to the General Ledger</li>
</ol>

<h2>Journal Entry Types</h2>
<ul>
<li><strong>Journal Entry</strong> – General purpose (expenses, salary crediting, etc.)</li>
<li><strong>Inter Company Journal Entry</strong> – Transactions between group companies</li>
<li><strong>Bank Entry</strong> – Payments via bank account</li>
<li><strong>Cash Entry</strong> – Payments via cash account</li>
<li><strong>Credit Card Entry</strong> – Credit card transactions</li>
<li><strong>Debit Note</strong> – Against supplier returns</li>
<li><strong>Credit Note</strong> – Against customer returns</li>
<li><strong>Contra Entry</strong> – Within same company (bank to cash, etc.)</li>
<li><strong>Opening Entry</strong> – Opening balances when migrating</li>
<li><strong>Depreciation</strong> – Fixed asset depreciation</li>
<li><strong>Exchange Rate Revaluation</strong> – Multi-currency adjustments</li>
</ul>""")

    update_article("payments", """<h1>Payments</h1>
<p>A Payment Entry records money received from customers or paid to suppliers. It can be made against Sales Invoices, Purchase Invoices, Sales Orders (advance), Purchase Orders (advance), Expense Claims, or as an Internal Transfer.</p>

<h2>Payment Types</h2>
<ul>
<li><strong>Receive</strong> – Customer payments against sales invoices</li>
<li><strong>Pay</strong> – Supplier payments against purchase invoices</li>
<li><strong>Internal Transfer</strong> – Move money between your own accounts (bank to cash, bank to bank, etc.)</li>
</ul>

<h2>Creating a Payment Entry</h2>
<ol>
<li>Go to Payment Entry → New</li>
<li>Select Payment Type (Receive/Pay/Internal Transfer)</li>
<li>Choose the Party (Customer or Supplier)</li>
<li>Select Mode of Payment (Bank, Cash, Cheque, Credit Card, etc.)</li>
<li>Enter the Amount Paid</li>
<li>Optionally allocate against specific invoices via Get Outstanding Invoices</li>
<li>Select the Bank Account or Cash Account (Paid From / Paid To)</li>
<li>Save and Submit</li>
</ol>

<h2>Key Features</h2>
<ul>
<li><strong>Unallocated Amount</strong> – Overpayments stored as credit for future invoices</li>
<li><strong>Write Off</strong> – Small differences can be written off to a loss account</li>
<li><strong>Multi-Currency</strong> – Payments in foreign currency with exchange gain/loss tracking</li>
<li><strong>Deductions</strong> – Apply deductions or losses against the payment</li>
</ul>""")

    update_article("sales-and-purchase-invoices", """<h1>Sales & Purchase Invoices</h1>

<h2>Sales Invoice</h2>
<p>A Sales Invoice is a bill sent to a Customer. On submission, CosmOS updates the receivable and books income against the Customer Account. Sales Invoices can be created from Sales Orders, Delivery Notes, or directly (e.g., POS).</p>

<h3>Creating a Sales Invoice</h3>
<ol>
<li>Go to Sales Invoice → New</li>
<li>Select the Customer</li>
<li>Set the Payment Due Date</li>
<li>In the Items table, select Items and set quantities (prices auto-fetch from Item Price)</li>
<li>Add taxes via Sales Taxes and Charges Template</li>
<li>Save and Submit</li>
</ol>

<h3>Key Features</h3>
<ul>
<li><strong>Update Stock</strong> – Automatically update inventory on submission</li>
<li><strong>Credit Note</strong> – Process returns via Is Return checkbox</li>
<li><strong>Advance Payment</strong> – Link advance payments received</li>
<li><strong>Payment Terms</strong> – Split payment into multiple due dates</li>
<li><strong>Discounts</strong> – Apply item-level or invoice-level discounts</li>
<li><strong>Loyalty Points</strong> – Redeem loyalty program points</li>
</ul>

<h2>Purchase Invoice</h2>
<p>A Purchase Invoice is a bill received from a Supplier. On submission, CosmOS updates the payable and books expenses against the Supplier Account. Purchase Invoices can be created from Purchase Orders or Purchase Receipts.</p>

<h3>Creating a Purchase Invoice</h3>
<ol>
<li>Go to Purchase Invoice → New</li>
<li>Select the Supplier</li>
<li>Set the Due Date for payment</li>
<li>Add Items and quantities (rates auto-fetch)</li>
<li>Add taxes via Purchase Taxes and Charges Template</li>
<li>Save and Submit</li>
</ol>

<h3>Key Features</h3>
<ul>
<li><strong>Is Paid</strong> – Mark if already paid via advance payment</li>
<li><strong>Debit Note</strong> – Process returns to supplier</li>
<li><strong>Holding Invoices</strong> – Temporarily hold payment</li>
<li><strong>Tax Withholding</strong> – Auto-deduct TDS/Tax at source</li>
<li><strong>Provisional Accounting</strong> – Accrue expenses before invoicing</li>
</ul>""")

    update_article("vat", """<h1>VAT (UAE)</h1>
<p>CosmOS supports UAE VAT at the standard rate of 5% with full compliance reporting.</p>

<h2>VAT Setup</h2>
<ol>
<li>Configure VAT accounts in the Chart of Accounts (Output VAT, Input VAT)</li>
<li>Create Item Tax Templates with VAT rate for applicable items</li>
<li>Set up Sales Taxes and Charges Templates and Purchase Taxes and Charges Templates</li>
<li>Assign templates to Customers or Suppliers via Tax Category</li>
</ol>

<h2>VAT Return</h2>
<ul>
<li>Navigate to VAT Return under Accounts</li>
<li>Select the period (monthly or quarterly)</li>
<li>CosmOS auto-calculates Output VAT, Input VAT, and Net VAT payable/receivable</li>
<li>Generate the return and export for FTA filing</li>
</ul>

<h2>Tax Accounts</h2>
<p>For Tax Accounts, go to Chart of Accounts, select an account, and set the Account Type to Tax. This ensures the account is available in tax templates.</p>""")

    update_article("financial-reports", """<h1>Financial Reports</h1>
<p>CosmOS provides a complete suite of financial reports for management, analysis, and compliance.</p>

<h2>Standard Financial Reports</h2>
<ul>
<li><strong>Profit and Loss Statement</strong> – Revenue, COGS, and expenses over a period</li>
<li><strong>Balance Sheet</strong> – Assets, liabilities, and equity snapshot</li>
<li><strong>Cash Flow Statement</strong> – Operating, investing, and financing cash flows</li>
<li><strong>Accounts Receivable</strong> – Outstanding customer invoices by ageing</li>
<li><strong>Accounts Payable</strong> – Outstanding supplier bills by ageing</li>
<li><strong>General Ledger</strong> – All transactions sorted by account and date</li>
<li><strong>Trial Balance</strong> – Debit/credit totals for every account</li>
<li><strong>Bank Reconciliation</strong> – Match bank statements with system entries</li>
<li><strong>Budget Variance</strong> – Actual vs budget comparison</li>
</ul>

<h2>Running Reports</h2>
<ol>
<li>Navigate to the report via Awesome Bar or the Accounts workspace</li>
<li>Set the Company, From Date, and To Date</li>
<li>Click Show to generate</li>
<li>Export to Excel or print the report</li>
</ol>""")

    # ── CRM & Sales ──
    update_article("crm-module-overview", """<h1>CRM Module Overview</h1>
<p>The CRM module is designed to enhance customer interactions and streamline sales processes. It provides a unified platform for managing customer interactions and sales activities.</p>

<h2>Key Features</h2>
<ul>
<li><strong>Lead Management</strong> – Capture, track, and nurture potential leads through the sales funnel</li>
<li><strong>Opportunity Tracking</strong> – Manage sales opportunities, track progress, and forecast revenue</li>
<li><strong>Customer Management</strong> – Detailed customer profiles with contact information, transaction history, and communication logs</li>
<li><strong>Activity Management</strong> – Schedule and track meetings, calls, and follow-ups</li>
<li><strong>Quotations and Sales Orders</strong> – Generate quotes and manage orders</li>
<li><strong>Reports and Analytics</strong> – Sales performance, pipeline, and customer behaviour insights</li>
</ul>

<h2>Sales Pipeline Stages</h2>
<ol>
<li><strong>Lead</strong> – Initial inquiry or contact</li>
<li><strong>Opportunity</strong> – Qualified lead with potential value</li>
<li><strong>Customer</strong> – Converted and onboarded</li>
<li><strong>Quotation</strong> – Price proposal sent</li>
<li><strong>Sales Order</strong> – Order confirmed and fulfilled</li>
</ol>""")

    update_article("leads-and-opportunities", """<h1>Leads & Opportunities</h1>

<h2>Leads</h2>
<p>A Lead is a potential customer who might be interested in your products or services. Sales executives work on leads by calling, building relationships, and sending information.</p>

<h3>Creating a Lead</h3>
<ol>
<li>Go to Lead → New</li>
<li>If the person represents an organisation, check "Lead is an Organization" and enter the Company Name</li>
<li>If an individual, enter Person Name and Gender</li>
<li>Enter Email Address and contact details</li>
<li>Set Status (Lead, Open, Replied, Interested, Converted, Do Not Contact)</li>
<li>Set Lead Source to track where the lead came from</li>
<li>Save</li>
</ol>

<h3>Lead Statuses</h3>
<ul>
<li><strong>Lead</strong> – Default, action needed</li>
<li><strong>Open</strong> – Sales executive needs to contact</li>
<li><strong>Replied</strong> – Information provided, response awaited</li>
<li><strong>Opportunity</strong> – Qualified and may lead to sale</li>
<li><strong>Quotation</strong> – Quotation created</li>
<li><strong>Converted</strong> – Order confirmed</li>
<li><strong>Do Not Contact</strong> – Not interested</li>
</ul>

<h2>Opportunities</h2>
<p>An Opportunity is a qualified lead. When a lead is looking for a product or service you offer, convert it into an opportunity.</p>

<h3>Creating an Opportunity</h3>
<ol>
<li>Go to Opportunity → Add Opportunity</li>
<li>Select "Opportunity From" – Lead or Customer</li>
<li>Set Opportunity Type (Sales, Support, Maintenance, etc.)</li>
<li>Enter Opportunity Amount and Probability of conversion</li>
<li>Use "With Items" to capture specific products/services needed</li>
<li>Save</li>
</ol>

<h3>Key Features</h3>
<ul>
<li>Auto-close opportunities after a set number of days</li>
<li>Capture lost reasons and competitors for analysis</li>
<li>Create Quotations directly from Opportunities</li>
<li>Auto-assign to sales executives via Assignment Rules</li>
<li>Minutes to First Response tracking</li>
</ul>""")

    update_article("customers-and-quotations", """<h1>Customers & Quotations</h1>

<h2>Customers</h2>
<p>The Customer master stores all information about your customers including contact details, addresses, payment terms, credit limits, and tax information.</p>

<h3>Creating a Customer</h3>
<ol>
<li>Go to Customer → New</li>
<li>Enter Customer Name</li>
<li>Select Customer Group</li>
<li>Set Territory</li>
<li>Add addresses and contacts</li>
<li>Set payment terms and credit limit</li>
<li>Save</li>
</ol>

<h2>Quotations</h2>
<p>A Quotation is a price proposal sent to a customer. It can be created directly or from an Opportunity or Lead.</p>

<h3>Creating a Quotation</h3>
<ol>
<li>Go to Quotation → New</li>
<li>Select Customer</li>
<li>Add Items with quantities (prices auto-fetch from Price List)</li>
<li>Apply discounts, taxes, and shipping charges</li>
<li>Set validity period</li>
<li>Print or email PDF to customer</li>
<li>Convert accepted Quotations to Sales Orders</li>
</ol>

<h2>Sales Orders</h2>
<p>A Sales Order confirms the customer order with delivery schedule. Track fulfilment against deliveries and invoices.</p>
<ul>
<li>Reserve stock if enabled</li>
<li>Partial deliveries allowed</li>
<li>Item-wise fulfilment tracking</li>
<li>Link to Delivery Notes and Sales Invoices</li>
</ul>""")

    # ── HR & Payroll ──
    update_article("hr-module-overview", """<h1>HR Module Overview</h1>
<p>The HR module manages the complete employee lifecycle from hiring through payroll and separation.</p>

<h2>Key Features</h2>
<ul>
<li><strong>Employee Master</strong> – Personal details, employment history, documents, visa tracking</li>
<li><strong>Leave Management</strong> – Leave types, allocations, applications, and balances</li>
<li><strong>Attendance</strong> – Daily check-in/out, monthly attendance, shift management</li>
<li><strong>Payroll</strong> – Salary structures, payroll processing, salary slips, WPS file generation</li>
<li><strong>Recruitment</strong> – Job openings, applicants, interviews, and offers</li>
<li><strong>Performance</strong> – Appraisals, goals, feedback, and KRA tracking</li>
<li><strong>Employee Lifecycle</strong> – Onboarding, promotions, transfers, and separation</li>
<li><strong>Visa Management</strong> – Multi-visa tracking per employee with 30-day expiry alerts</li>
<li><strong>Gratuity</strong> – Automated UAE end-of-service gratuity calculation</li>
</ul>""")

    update_article("employee-master", """<h1>Employee Master</h1>
<p>The Employee doctype is the central record for every staff member. To set up the employee master, first create Employment Types, Branches, Departments, Designations, and Grades.</p>

<h2>Employee Information</h2>
<ul>
<li><strong>Personal Details</strong> – Name, DOB, gender, marital status, nationality</li>
<li><strong>Contact</strong> – Email, phone, address, emergency contact</li>
<li><strong>Employment</strong> – Employee ID, joining date, employment type, grade, department, designation, reports to</li>
<li><strong>Visa Details</strong> – Table of visa records with passport number, visa type, issue/expiry dates, and documents</li>
<li><strong>Bank Details</strong> – Bank name, account number, IBAN for salary transfers</li>
<li><strong>Salary Info</strong> – Salary structure, components, effective dates</li>
</ul>

<h3>Creating an Employee</h3>
<ol>
<li>Go to Employee → New</li>
<li>Fill required fields (Employee Name, Company, Date of Joining)</li>
<li>Navigate through tabs to add all relevant information</li>
<li>Save</li>
</ol>""")

    update_article("leave-management", """<h1>Leave Management</h1>

<h2>Leave Setup</h2>
<p>To set up leaves, create the following in order:</p>
<ol>
<li><strong>Leave Type</strong> – Define types (Annual Leave, Sick Leave, Casual Leave) with max days, carry-forward rules, and encashment</li>
<li><strong>Holiday List</strong> – Annual holidays that are not counted in leave applications</li>
<li><strong>Leave Policy</strong> – Combine leave types with allocations to manage employee leaves across the company</li>
</ol>

<h2>Leave Allocation</h2>
<ul>
<li>Allocate leave balances per employee per period</li>
<li>Bulk allocation via Leave Policy Assignment</li>
<li>Auto-allocate on employee creation</li>
</ul>

<h2>Leave Application</h2>
<ol>
<li>Employee applies via Leave Application</li>
<li>Selects Leave Type, From/To dates, and reason</li>
<li>Optionally attach supporting documents</li>
<li>Save – triggers approval workflow</li>
<li>Manager Approves or Rejects</li>
<li>Approved leave deducts from the employee's balance</li>
</ol>""")

    update_article("attendance", """<h1>Attendance</h1>

<h2>Marking Attendance</h2>
<ul>
<li><strong>Manual</strong> – Create individual Attendance records</li>
<li><strong>Attendance Tool</strong> – Bulk mark attendance for multiple employees in a date range</li>
<li><strong>Employee Checkin</strong> – Biometric/device integration or manual check-in/out logs</li>
<li><strong>Shift Management</strong> – Assign shifts; auto-calculate early/late arrivals and overtime</li>
</ul>

<h2>Attendance Reports</h2>
<ul>
<li><strong>Monthly Attendance Sheet</strong> – Present/absent/leave/holiday per employee</li>
<li><strong>Attendance Summary</strong> – Aggregate view for payroll processing</li>
<li><strong>Overtime Slip</strong> – Computed overtime based on shift schedules</li>
</ul>""")

    update_article("payroll-processing", """<h1>Payroll Processing</h1>

<h2>Payroll Setup</h2>
<p>Before processing payroll, set up the following:</p>
<ol>
<li><strong>Payroll Period</strong> – Define monthly, quarterly, or yearly periods</li>
<li><strong>Salary Components</strong> – Create Earnings (Basic, Housing Allowance, etc.) and Deductions (Income Tax, Social Security, etc.)</li>
<li><strong>Income Tax Slab</strong> – Define tax brackets for auto-calculation</li>
<li><strong>Salary Structure</strong> – Combine components into a structure</li>
<li><strong>Salary Structure Assignment</strong> – Assign to each employee</li>
</ol>

<h2>Processing Payroll via Payroll Entry</h2>
<ol>
<li>Go to Payroll Entry → New</li>
<li>Select Company, Payroll Period, and Posting Date</li>
<li>Set frequency and filters (Branch, Department, Designation)</li>
<li>Click Get Employees to fetch eligible employees</li>
<li>Click Create Salary Slips to generate draft salary slips</li>
<li>Verify each salary slip</li>
<li>Click Submit Salary Slip to finalise (books accrual journal entry)</li>
<li>Click Make Bank Entry to generate payment voucher</li>
</ol>

<h2>Salary Slip</h2>
<p>Each employee receives a Salary Slip showing earnings breakdown, deductions breakdown, net pay, and year-to-date totals.</p>""")

    update_article("wps-salary-file", """<h1>WPS Salary File (UAE)</h1>
<p>The WPS (Wage Protection System) Salary File generates a text file in UAE Central Bank format for salary disbursement.</p>

<h2>Prerequisites</h2>
<ul>
<li><strong>Company Bank Account</strong> marked as Is Company Account with IBAN and bank code</li>
<li><strong>Employee Bank Details</strong> – Bank name, IBAN, and account number in Employee records</li>
<li>Payroll processed for the relevant period</li>
</ul>

<h2>Creating a WPS Salary File</h2>
<ol>
<li>Go to WPS Salary File → New</li>
<li>Select Company and Pay Period</li>
<li>In WPS Salary Detail table, add rows with Employee and Salary Amount</li>
<li>Set Posting Date</li>
<li>Submit – The UAE format text file is auto-generated and attached</li>
<li>Download and upload to your bank or EWPS portal</li>
</ol>

<h2>File Format</h2>
<ul>
<li><strong>Header Record</strong> – File type, company code, bank code, total count, total amount</li>
<li><strong>Detail Records</strong> – One per employee: ID, name, IBAN, bank code, amount</li>
<li><strong>Trailer Record</strong> – Total count, total amount, checksum</li>
</ul>""")

    update_article("gratuity", """<h1>Gratuity (UAE)</h1>
<p>CosmOS automatically calculates UAE end-of-service gratuity based on the applicable Labour Law rules.</p>

<h2>Gratuity Rules</h2>
<ul>
<li><strong>Limited Contract</strong> – Fixed-term contract termination</li>
<li><strong>Unlimited Contract (Termination by Employer)</strong></li>
<li><strong>Unlimited Contract (Resignation by Employee)</strong></li>
</ul>

<h2>Calculation</h2>
<ul>
<li>Basic salary as the calculation base</li>
<li>Service period from date of joining</li>
<li>Different slabs: first 5 years vs. subsequent years</li>
<li>Daily wage = Basic Salary / 30</li>
</ul>

<h2>Generating Gratuity</h2>
<ol>
<li>Go to Gratuity → New</li>
<li>Select Employee – service period and basic salary auto-populate</li>
<li>Choose the Gratuity Rule</li>
<li>CosmOS calculates the amount</li>
<li>Save and Submit</li>
</ol>""")

    update_article("recruitment", """<h1>Recruitment</h1>

<h2>Job Opening</h2>
<p>Create job postings with title, description, requirements, and vacancy count. Publish on the website careers page.</p>
<p>If an active Staffing Plan exists, CosmOS validates open positions and current employment count.</p>

<h2>Job Applicant</h2>
<ul>
<li>Applicants apply via website or added manually</li>
<li>Upload CV/resume and cover letter</li>
<li>Status tracking: Open, Replied, Interview Scheduled, Rejected, Selected</li>
</ul>

<h2>Interview</h2>
<ul>
<li>Schedule interviews for shortlisted candidates</li>
<li>Multiple rounds with different interviewers</li>
<li>Record feedback and ratings</li>
<li>Make hiring decisions</li>
</ul>

<h2>Job Offer</h2>
<ul>
<li>Extend offers with salary, start date, and benefits</li>
<li>Track acceptance/rejection</li>
<li>Convert accepted offers to Employee records</li>
</ul>""")

    # ── Buying ──
    update_article("buying-module-overview", """<h1>Buying & Procurement Overview</h1>
<p>The Buying module manages the complete procurement process from supplier selection to purchase order fulfillment.</p>

<h2>Suppliers</h2>
<ul>
<li>Supplier master with contact details, addresses, and payment terms</li>
<li>Scorecard for performance evaluation</li>
<li>View outstanding bills and payment history</li>
</ul>

<h2>Material Request</h2>
<p>Raise requests for materials needed. Set required date and priority. Auto-create Purchase Orders from approved requests.</p>

<h2>Request for Quotation (RFQ)</h2>
<p>Send RFQs to multiple suppliers, collect and compare quotations, select the best offer, and create a Purchase Order.</p>

<h2>Purchase Order</h2>
<p>A Purchase Order is a binding contract with a Supplier to buy items under given conditions. It can be created from a Material Request or Supplier Quotation.</p>
<ol>
<li>Go to Purchase Order → New</li>
<li>Select Supplier and required by date</li>
<li>Add Items with quantities and prices</li>
<li>Set taxes and shipping</li>
<li>Save and Submit</li>
</ol>

<h2>Purchase Receipt</h2>
<p>Record goods received from suppliers. Updates stock quantities and valuation. Quality inspection can be triggered on receipt.</p>""")

    # ── Stock ──
    update_article("stock-module-overview", """<h1>Stock & Inventory Overview</h1>
<p>The Stock module manages all aspects of inventory and supply chain operations.</p>

<h2>Key Capabilities</h2>
<ul>
<li><strong>Inventory Tracking</strong> – Monitor stock levels, track movements, manage warehouses</li>
<li><strong>Item Management</strong> – Define products, track variants, manage pricing</li>
<li><strong>Stock Transactions</strong> – Receipts, deliveries, transfers, and reconciliations</li>
<li><strong>Serial & Batch Tracking</strong> – Individual item traceability</li>
<li><strong>Reports & Analytics</strong> – Stock levels, valuations, and trends</li>
</ul>""")

    update_article("items-and-warehouses", """<h1>Items & Warehouses</h1>

<h2>Items</h2>
<p>An Item is a product or service offered by your company. CosmOS supports raw materials, sub-assemblies, finished goods, item variants, and services.</p>

<h3>Creating an Item</h3>
<ol>
<li>Go to Item → New</li>
<li>Enter Item Code and Item Name</li>
<li>Select Item Group</li>
<li>Set Default Unit of Measure (Nos, Kgs, Meters, etc.)</li>
<li>Set Default Warehouse</li>
<li>Configure valuation method (FIFO or Moving Average)</li>
<li>Enable Serial/Batch tracking if needed</li>
<li>Save</li>
</ol>

<h3>Item Features</h3>
<ul>
<li><strong>Variants</strong> – Size, colour, or configurable attributes</li>
<li><strong>Barcodes</strong> – Scan to add items in transactions (EAN/UPC)</li>
<li><strong>Auto Reorder</strong> – Automatic Material Requests when stock dips below reorder level</li>
<li><strong>Multiple UOM</strong> – Sell in different units with conversion factors</li>
<li><strong>Item Tax Templates</strong> – Apply specific tax rates per item</li>
<li><strong>Quality Inspection</strong> – Inspect before purchase or delivery</li>
</ul>

<h2>Warehouses</h2>
<p>Create warehouses by location with parent-child hierarchy. Each warehouse tracks its own stock balance.</p>
<ul>
<li>Default warehouse per item</li>
<li>Group warehouses supported</li>
<li>Warehouse-specific inventory reports</li>
</ul>""")

    update_article("stock-transactions", """<h1>Stock Transactions</h1>

<h2>Stock Entry</h2>
<p>Used for internal stock movements:</p>
<ul>
<li><strong>Material Receipt</strong> – Receive stock from supplier</li>
<li><strong>Material Issue</strong> – Issue stock for consumption</li>
<li><strong>Material Transfer</strong> – Move stock between warehouses</li>
<li><strong>Manufacture</strong> – Finished goods from raw materials</li>
<li><strong>Repack</strong> – Change item composition</li>
<li><strong>Send to Subcontractor</strong> – Issue raw materials to subcontractor</li>
</ul>

<h2>Delivery Note</h2>
<p>Dispatch goods to customers against Sales Orders. Updates stock and COGS. Packing list for logistics.</p>
<ol>
<li>Go to Delivery Note → New</li>
<li>Select Customer</li>
<li>Add Items with quantities from Sales Order</li>
<li>Set warehouse for each item</li>
<li>Save and Submit</li>
</ol>

<h2>Purchase Receipt</h2>
<p>Receive goods from suppliers against Purchase Orders. Quality inspection can be conducted at receipt.</p>

<h2>Stock Reconciliation</h2>
<p>Adjust physical stock vs system stock. Used for initial setup or periodic counting.</p>""")

    update_article("serial-and-batch-tracking", """<h1>Serial & Batch Tracking</h1>

<h2>Serial Numbers</h2>
<ul>
<li>Track individual items through their lifecycle</li>
<li>Each serial number is unique per item</li>
<li>Capture serials on receipt, delivery, and stock entry</li>
<li>View serial history: received, transferred, delivered, returned</li>
<li>Ideal for electronics, machinery, high-value items</li>
</ul>

<h2>Batch Numbers</h2>
<ul>
<li>Track groups of items sharing the same batch/lot</li>
<li>Capture batch number, manufacturing date, expiry date</li>
<li>Auto-assign batches from supplier and date</li>
<li>Ideal for pharmaceuticals, food, chemicals</li>
</ul>

<h2>Enabling Tracking</h2>
<p>In the Item master, enable Has Serial No or Has Batch No. Once enabled and transactions exist, these settings cannot be changed.</p>""")

    # ── Manufacturing ──
    update_article("manufacturing-module", """<h1>Manufacturing Module</h1>
<p>The Manufacturing module streamlines and optimises the production process from Bill of Materials to Work Orders and Job Cards.</p>

<h2>Bill of Materials (BOM)</h2>
<p>Define the recipe for manufacturing finished goods. List raw materials with quantities and operations.</p>
<ul>
<li>Multi-level BOM for sub-assemblies</li>
<li>Scrap/waste percentage</li>
<li>BOM versioning and approval workflow</li>
</ul>

<h2>Work Order</h2>
<p>A Work Order is a signal to manufacture a certain quantity of an Item. It generates material requirements from the BOM.</p>
<ol>
<li>Go to Work Order → New</li>
<li>Select Item to manufacture</li>
<li>Default BOM auto-fetches</li>
<li>Enter quantity and planned start date</li>
<li>Set source, WIP, target, and scrap warehouses</li>
<li>Submit</li>
<li>Click Start to transfer materials and create Job Cards</li>
<li>Click Finish to complete and receive finished goods</li>
</ol>

<h2>Job Card</h2>
<p>Record time and operations during manufacturing. Assign to workers/workstations. Track completion quantity and scrap.</p>

<h2>Production Plan</h2>
<p>Plan production against Sales Orders or Material Requests. Generate Work Orders and Material Requests automatically.</p>

<h2>Routing & Workstations</h2>
<p>Define manufacturing routing (sequence of operations) with workstation types, time, and cost per operation.</p>""")

    # ── Assets ──
    update_article("assets-module", """<h1>Assets Module</h1>
<p>Manage fixed assets from acquisition through depreciation to disposal.</p>

<h2>Asset Master</h2>
<ul>
<li>Register fixed assets: equipment, vehicles, buildings, furniture</li>
<li>Asset category, location, and custodian</li>
<li>Purchase date, cost, and supplier</li>
<li>Attach images and documents</li>
</ul>

<h2>Creating an Asset</h2>
<ol>
<li>Create an Item with Is Fixed Asset enabled</li>
<li>Optionally enable Auto Create Assets on Purchase</li>
<li>On Purchase Receipt/Purchase Invoice submission, assets are automatically or manually created</li>
<li>Set Available-for-Use Date – depreciation starts from this date</li>
<li>Save and Submit</li>
</ol>

<h2>Depreciation</h2>
<ul>
<li>Straight-line or declining balance methods</li>
<li>Auto-generated depreciation schedule</li>
<li>Monthly or yearly entries</li>
<li>Pro-rata for partial-year assets</li>
</ul>

<h2>Asset Movements & Maintenance</h2>
<ul>
<li>Transfer assets between employees or locations</li>
<li>Schedule preventive maintenance</li>
<li>Track maintenance tasks, teams, and costs</li>
<li>Log asset repairs</li>
</ul>""")

    # ── Projects ──
    update_article("projects-module", """<h1>Projects Module</h1>
<p>Project management in CosmOS is task-driven. Create a Project and divide it into multiple Tasks with timesheets and costing.</p>

<h2>Creating a Project</h2>
<ol>
<li>Go to Project → New</li>
<li>Enter Project Name</li>
<li>Set Expected Start and End Dates</li>
<li>Select Project Type (Internal, External)</li>
<li>Set Priority</li>
<li>Link to Customer and Sales Order if applicable</li>
<li>Save</li>
</ol>

<h2>Tasks</h2>
<ul>
<li>Break projects into tasks with assignees and deadlines</li>
<li>Task dependencies and priority</li>
<li>Track completion percentage</li>
<li>Gantt chart view</li>
</ul>

<h2>Timesheets</h2>
<ul>
<li>Log hours worked per task/project</li>
<li>Billable vs non-billable hours</li>
<li>Link to payroll if enabled</li>
<li>Generate invoices from billable timesheets</li>
</ul>

<h2>Project Costing</h2>
<ul>
<li>Estimated cost vs actual cost tracking</li>
<li>Total expense claims, purchase costs, and material costs</li>
<li>Gross margin calculation</li>
<li>Budget vs actual variance</li>
</ul>

<h2>Completion Tracking</h2>
<p>Four methods: Manual, Task Completion, Task Progress, and Task Weight. The system auto-calculates percentage complete.</p>""")

    # ── Support ──
    update_article("support-module", """<h1>Support Module</h1>
<p>The Support module manages customer support requests, service level agreements, and warranty claims.</p>

<h2>Issues</h2>
<ul>
<li>Track support requests from creation to resolution</li>
<li>Capture description, priority, and type</li>
<li>Assign to support agents</li>
<li>Communication thread within the ticket</li>
<li>Resolution and closure tracking</li>
</ul>

<h2>Service Level Agreements (SLA)</h2>
<ul>
<li>Define response and resolution SLAs per priority</li>
<li>Auto-assign SLA on ticket creation</li>
<li>Track SLA breach and escalation</li>
<li>Reports on SLA compliance</li>
</ul>

<h2>Warranty Claims</h2>
<ul>
<li>Link claims to serial numbers</li>
<li>Track claim status and resolution</li>
<li>Replace/repair decision logging</li>
</ul>

<h2>Maintenance</h2>
<ul>
<li>Maintenance schedules and visits</li>
<li>Track recurring maintenance activities</li>
</ul>""")

    # ── Settings ──
    update_article("company-setup", """<h1>Company Setup</h1>

<h2>Creating a Company</h2>
<ol>
<li>Go to Company → New</li>
<li>Enter Company Name, Abbreviation, and Domain</li>
<li>Select Country (sets default currency, date format, and tax rules)</li>
<li>Set Default Currency</li>
<li>Provide Registration ID (e.g., Trade License Number)</li>
<li>Set Fiscal Year start and end dates</li>
<li>Upload company logo (optional)</li>
<li>Save</li>
</ol>

<h2>Company Settings</h2>
<ul>
<li>Default accounts for different transaction types</li>
<li>Holiday list for attendance calculations</li>
<li>Default bank account for payments</li>
<li>Default terms and tax templates</li>
</ul>""")

    update_article("users-and-permissions", """<h1>Users & Permissions</h1>

<h2>Creating Users</h2>
<ol>
<li>Go to User → New</li>
<li>Enter Email, Full Name, and a temporary password</li>
<li>Assign one or more Roles (e.g., Accounts User, HR Manager, System Manager)</li>
<li>Optionally set module profile for workspace access</li>
<li>Save – user receives login credentials</li>
</ol>

<h2>Pre-defined Roles</h2>
<ul>
<li><strong>System Manager</strong> – Full system access</li>
<li><strong>Accounts Manager/User</strong> – Finance module</li>
<li><strong>HR Manager/User</strong> – HR and payroll</li>
<li><strong>Sales Manager/User</strong> – CRM and sales</li>
<li><strong>Purchase Manager/User</strong> – Buying and procurement</li>
<li><strong>Stock Manager/User</strong> – Inventory</li>
<li><strong>Employee</strong> – Self-service (leave, attendance, timesheets)</li>
</ul>

<h2>Permission Rules</h2>
<ul>
<li><strong>Role-based</strong> – Users inherit permissions from roles</li>
<li><strong>Document-level</strong> – Create/read/write/delete/amend/submit per DocType</li>
<li><strong>Row-level</strong> – Restrict access to specific records (e.g., own department)</li>
<li>Permissions can be set per Company for multi-company setups</li>
</ul>""")

    print("\nAll articles updated with official documentation content!")
    frappe.db.commit()

if __name__ == "__main__":
    run()
