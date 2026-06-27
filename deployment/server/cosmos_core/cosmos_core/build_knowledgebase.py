import frappe

def create_category(name, desc):
    if not frappe.db.exists("Help Category", name):
        cat = frappe.get_doc({"doctype": "Help Category", "category_name": name, "category_description": desc})
        cat.insert(ignore_permissions=True)
        print(f"  Created Category: {name}")

def upsert_article(title, category, content, route=None):
    if not route:
        route = title.lower().replace(" ", "-").replace("&", "and")
    route = route.replace("--", "-")
    existing = frappe.db.get_value("Help Article", {"route": route})
    if existing:
        frappe.db.set_value("Help Article", existing, "content", content)
        frappe.db.set_value("Help Article", existing, "category", category)
        print(f"  Updated Article: {title}")
    else:
        doc = frappe.get_doc({
            "doctype": "Help Article",
            "title": title,
            "route": route,
            "category": category,
            "content": content,
            "published": 1,
            "author": "CosmOS"
        })
        doc.insert(ignore_permissions=True)
        print(f"  Created Article: {title}")

def build():
    print("=== Building CosmOS Knowledge Base ===\n")
    
    # ── Categories ──
    print("Creating categories...")
    create_category("Getting Started", "Introduction, basics, and overview of the CosmOS system")
    create_category("Accounts & Finance", "Complete financial management: chart of accounts, journals, payments, invoices, VAT, budgeting, and financial reports")
    create_category("HR & Payroll", "Employee lifecycle, leave, attendance, payroll processing, WPS, gratuity, and visa management")
    create_category("CRM & Sales", "Leads, opportunities, customers, quotations, and sales orders")
    create_category("Buying & Procurement", "Suppliers, purchase orders, purchase receipts, and supplier management")
    create_category("Stock & Inventory", "Items, warehouses, stock transactions, serial/batch tracking, and inventory reports")
    create_category("Manufacturing", "BOM, work orders, job cards, production planning, and routing")
    create_category("Assets", "Fixed asset management, depreciation, maintenance, and movement")
    create_category("Projects", "Project planning, tasks, timesheets, and cost tracking")
    create_category("Support", "Issue tracking, SLA management, and warranty claims")
    create_category("Settings & Setup", "System configuration, users, permissions, and company setup")
    print("Categories done.\n")

    # ── Getting Started ──
    print("Writing Getting Started articles...")
    upsert_article("About CosmOS", "Getting Started", """<h1>About CosmOS</h1>
<p>CosmOS is a comprehensive Enterprise Resource Planning (ERP) system designed to streamline your business operations. Built on a powerful open-source framework, CosmOS provides end-to-end solutions across all business functions.</p>

<h2>Key Features</h2>
<ul>
<li><strong>Integrated Modules</strong> – Accounts, HR, Payroll, CRM, Sales, Purchasing, Inventory, Manufacturing, Projects, Assets, and Support – all in one platform</li>
<li><strong>Real-time Reporting</strong> – Dashboards, financial statements, and live operational reports</li>
<li><strong>Multi-Company</strong> – Manage multiple legal entities from a single installation</li>
<li><strong>Role-Based Access Control</strong> – Granular permissions per user, role, and document</li>
<li><strong>UAE Compliant</strong> – WPS salary file generation, VAT returns, and end-of-service gratuity calculation</li>
<li><strong>Workflow Automation</strong> – Approvals, alerts, and automated email notifications</li>
<li><strong>Cloud & On-Premise</strong> – Deploy on your own infrastructure or in the cloud</li>
</ul>

<h2>Navigating CosmOS</h2>
<ul>
<li><strong>Awesome Bar</strong> – Press Ctrl+G or Cmd+G to quickly search and navigate to any module, document, or report</li>
<li><strong>Workspace</strong> – Role-based landing pages with shortcuts to frequently used features</li>
<li><strong>Module Menu</strong> – Grid icon (9 dots) in the top-right corner lists all installed modules</li>
<li><strong>Sidebar</strong> – Tree view of modules on the left side of the screen</li>
</ul>

<h2>Getting Help</h2>
<ul>
<li>Refer to this User Manual for detailed module guides</li>
<li>Contact support at <strong>support@cosmoserp.com</strong></li>
<li>Report issues via the GitHub issues page</li>
</ul>""")

    upsert_article("User Manual Index", "Getting Started", """<h1>CosmOS User Manual Index</h1>
<p>Welcome to the complete CosmOS User Manual. Select a module below for detailed guidance.</p>

<h2>Getting Started</h2>
<ul>
<li><a href="/app/help-article/about-cosmos">About CosmOS</a> – Introduction, navigation, and key features</li>
<li><a href="/app/help-article/user-manual-index">User Manual Index</a> – You are here</li>
</ul>

<h2>Core Business Modules</h2>
<ul>
<li><strong>Accounts & Finance</strong> – Chart of accounts, journal entries, payments, sales/purchase invoices, VAT, budgets, financial reports</li>
<li><strong>HR & Payroll</strong> – Employee master, leaves, attendance, payroll, WPS salary files, gratuity, visa expiry alerts</li>
<li><strong>CRM & Sales</strong> – Leads, opportunities, customers, quotations, sales orders</li>
<li><strong>Buying & Procurement</strong> – Suppliers, material requests, purchase orders, purchase receipts</li>
<li><strong>Stock & Inventory</strong> – Items, warehouses, stock entries, delivery notes, serial/batch tracking</li>
<li><strong>Manufacturing</strong> – BOM, work orders, job cards, production planning</li>
<li><strong>Assets</strong> – Fixed asset registers, depreciation, maintenance, transfers</li>
<li><strong>Projects</strong> – Tasks, timesheets, project costing, and tracking</li>
<li><strong>Support</strong> – Issue tracking, SLA, warranty claims</li>
</ul>

<h2>Administration</h2>
<ul>
<li><strong>Settings & Setup</strong> – Company setup, users, roles, permissions, system configuration</li>
</ul>""")

    # ── Accounts & Finance ──
    print("Writing Accounts & Finance articles...")
    upsert_article("Chart of Accounts", "Accounts & Finance", """<h1>Chart of Accounts</h1>
<p>The Chart of Accounts is the backbone of your financial system. It organises all financial transactions into a hierarchical structure of groups and ledgers.</p>

<h2>Account Types</h2>
<ul>
<li><strong>Assets</strong> – Current Assets (cash, bank, receivables) and Fixed Assets (property, equipment)</li>
<li><strong>Liabilities</strong> – Current Liabilities (payables, taxes) and Long-term Liabilities (loans)</li>
<li><strong>Equity</strong> – Owner's capital, retained earnings</li>
<li><strong>Income</strong> – Revenue from sales, services, and other income</li>
<li><strong>Expenses</strong> – Operating expenses, cost of goods sold, administrative costs</li>
</ul>

<h2>Managing Accounts</h2>
<ul>
<li><strong>Group Accounts</strong> – Parent accounts that summarise child ledgers (e.g., "Current Assets" groups "Cash" and "Bank")</li>
<li><strong>Ledger Accounts</strong> – Leaf-level accounts where transactions are posted</li>
<li>Accounts can be <strong>frozen</strong> to prevent further postings</li>
<li>Set <strong>account currency</strong> for multi-currency ledgers</li>
</ul>

<h2>How to Create an Account</h2>
<ol>
<li>Go to <strong>Chart of Accounts</strong> (via Awesome Bar)</li>
<li>Click <strong>Add New Account</strong></li>
<li>Select the parent account and set the account name</li>
<li>Choose the account type (Asset, Liability, etc.)</li>
<li>Save – the account is ready for transactions</li>
</ol>""")

    upsert_article("Journal Entries", "Accounts & Finance", """<h1>Journal Entries</h1>
<p>Journal Entries (JV) are the fundamental method for recording financial transactions. Every transaction must have equal debits and credits.</p>

<h2>When to Use Journal Entries</h2>
<ul>
<li>Opening balances</li>
<li>Adjustments and corrections</li>
<li>Inter-account transfers</li>
<li>Accruals and prepayments</li>
<li>Depreciation entries (if not automated)</li>
</ul>

<h2>Creating a Journal Entry</h2>
<ol>
<li>Go to <strong>Journal Entry</strong> via Awesome Bar</li>
<li>Set the <strong>Posting Date</strong></li>
<li>In the Accounting Entries table, add one or more rows:</li>
<li>Each row: select <strong>Account</strong>, enter <strong>Debit</strong> or <strong>Credit</strong> amount</li>
<li>Optionally set <strong>Party Type</strong> and <strong>Party</strong> for customer/supplier entries</li>
<li>Total debits must equal total credits</li>
<li><strong>Save</strong> and <strong>Submit</strong> to post</li>
</ol>

<h2>Multi-Currency Entries</h2>
<p>If the account has a different currency, CosmOS automatically applies the exchange rate. You can override the rate manually.</p>""")

    upsert_article("Payments", "Accounts & Finance", """<h1>Payments</h1>
<p>Payment Entries record money received from customers or paid to suppliers.</p>

<h2>Payment Types</h2>
<ul>
<li><strong>Receive</strong> – Customer payments against sales invoices</li>
<li><strong>Pay</strong> – Supplier payments against purchase invoices</li>
<li><strong>Internal Transfer</strong> – Move money between your own bank accounts</li>
</ul>

<h2>Payment Modes</h2>
<ul>
<li><strong>Cash</strong> – Physical cash transactions</li>
<li><strong>Cheque</strong> – Cheque payments with reference number and date</li>
<li><strong>Bank Transfer</strong> – Electronic funds transfer</li>
<li><strong>Credit Card</strong> – Card payment processing</li>
</ul>

<h2>Creating a Payment Entry</h2>
<ol>
<li>Go to <strong>Payment Entry</strong> via Awesome Bar</li>
<li>Select <strong>Payment Type</strong> (Receive/Pay/Internal Transfer)</li>
<li>Choose the <strong>Party</strong> (Customer or Supplier)</li>
<li>Select <strong>Mode of Payment</strong></li>
<li>Enter the <strong>Amount</strong></li>
<li>Optionally allocate against specific invoices in the References table</li>
<li>Select the <strong>Bank Account</strong> or <strong>Cash Account</strong></li>
<li><strong>Save</strong> and <strong>Submit</strong></li>
</ol>""")

    upsert_article("Sales and Purchase Invoices", "Accounts & Finance", """<h1>Sales & Purchase Invoices</h1>

<h2>Sales Invoice</h2>
<p>A Sales Invoice is raised against a customer for goods or services provided. It updates accounts receivable and income.</p>
<ul>
<li>Can be created directly or from a <strong>Delivery Note</strong> or <strong>Sales Order</strong></li>
<li>Items are populated from the source document</li>
<li>Taxes and charges are applied automatically based on the <strong>Tax Template</strong></li>
<li>Update <strong>Stock</strong> (if applicable) to reduce inventory on submission</li>
<li>Print and email directly from the document</li>
</ul>

<h2>Purchase Invoice</h2>
<p>A Purchase Invoice is received from a supplier for goods or services purchased. It updates accounts payable and expenses.</p>
<ul>
<li>Can be created from a <strong>Purchase Receipt</strong> or <strong>Purchase Order</strong></li>
<li>Set <strong>Bill Date</strong> and <strong>Due Date</strong> for payment terms</li>
<li>Taxes are applied from the purchase tax template</li>
<li>Credit and debit notes are available via the <strong>Is Return</strong> checkbox</li>
</ul>

<h2>Invoice Workflow</h2>
<ol>
<li><strong>Draft</strong> – Enter details, no accounting impact</li>
<li><strong>Submit</strong> – Posts to GL, updates stock (if enabled), sends email</li>
<li><strong>Cancel</strong> – Reverses all accounting and stock entries</li>
</ol>""")

    upsert_article("VAT", "Accounts & Finance", """<h1>VAT (UAE)</h1>
<p>CosmOS supports UAE VAT at the standard rate of 5% with full compliance reporting.</p>

<h2>VAT Setup</h2>
<ul>
<li>Configure VAT accounts in the Chart of Accounts (Output VAT, Input VAT, etc.)</li>
<li>Create <strong>Item Tax Templates</strong> with VAT rate for each item</li>
<li>Set up <strong>Sales Taxes and Charges Templates</strong> and <strong>Purchase Taxes and Charges Templates</strong></li>
<li>Assign templates to customers/suppliers or items</li>
</ul>

<h2>VAT Returns</h2>
<ul>
<li>Go to <strong>VAT Return</strong> under Accounts module</li>
<li>Select the period (monthly/quarterly)</li>
<li>CosmOS auto-calculates:
  <ul>
  <li>Output VAT (sales)</li>
  <li>Input VAT (purchases)</li>
  <li>Net VAT payable/receivable</li>
  </ul>
</li>
<li>Generate the return and export for FTA filing</li>
</ul>""")

    upsert_article("Financial Reports", "Accounts & Finance", """<h1>Financial Reports</h1>
<p>CosmOS provides a complete suite of financial reports for management and compliance.</p>

<h2>Standard Reports</h2>
<ul>
<li><strong>Profit and Loss Statement</strong> – Revenue, cost of goods sold, and expenses over a period</li>
<li><strong>Balance Sheet</strong> – Assets, liabilities, and equity as at a date</li>
<li><strong>Cash Flow Statement</strong> – Operating, investing, and financing cash flows</li>
<li><strong>Accounts Receivable</strong> – Outstanding customer invoices by ageing</li>
<li><strong>Accounts Payable</strong> – Outstanding supplier bills by ageing</li>
<li><strong>General Ledger</strong> – All transactions sorted by account and date</li>
<li><strong>Trial Balance</strong> – Debit/credit totals for every account</li>
<li><strong>Bank Reconciliation</strong> – Match bank statements with system entries</li>
</ul>

<h2>Running Reports</h2>
<ol>
<li>Navigate to the report via Awesome Bar or the Accounts workspace</li>
<li>Set the <strong>Company</strong>, <strong>From Date</strong>, and <strong>To Date</strong></li>
<li>Click <strong>Show</strong> to generate</li>
<li>Export to <strong>Excel</strong> or <strong>print</strong> the report</li>
</ol>

<h2>Budgeting</h2>
<ul>
<li>Create <strong>Budgets</strong> per account/cost center for a fiscal year</li>
<li>Monitor actual vs. budget variance in real time</li>
<li>Optional budget control blocks overspending on submission</li>
</ul>""")

    # ── HR & Payroll ──
    print("Writing HR & Payroll articles...")
    upsert_article("HR Module Overview", "HR & Payroll", """<h1>HR Module Overview</h1>
<p>The HR module manages the complete employee lifecycle: from hiring through payroll and separation.</p>

<h2>Key Features</h2>
<ul>
<li><strong>Employee Master</strong> – Personal details, employment history, documents, visa tracking</li>
<li><strong>Leave Management</strong> – Leave types, allocations, applications, and balances</li>
<li><strong>Attendance</strong> – Daily check-in/out, monthly attendance, shift management</li>
<li><strong>Payroll</strong> – Salary structures, payroll processing, salary slips, WPS file generation</li>
<li><strong>Recruitment</strong> – Job openings, job applicants, interviews, and offers</li>
<li><strong>Performance</strong> – Appraisals, goals, feedback, and KRA tracking</li>
<li><strong>Employee Lifecycle</strong> – Onboarding, promotions, transfers, and separation</li>
<li><strong>Visa Management</strong> – Multi-visa tracking per employee with 30-day expiry alerts</li>
<li><strong>Gratuity</strong> – Automated UAE end-of-service gratuity calculation</li>
</ul>""")

    upsert_article("Employee Master", "HR & Payroll", """<h1>Employee Master</h1>
<p>The Employee doctype is the central record for every staff member.</p>

<h2>Employee Information Sections</h1>
<ul>
<li><strong>Personal Details</strong> – Name, date of birth, gender, marital status, nationality</li>
<li><strong>Contact</strong> – Email, phone, address, emergency contact</li>
<li><strong>Employment</strong> – Employee ID, joining date, employment type, grade, department, designation, reports to</li>
<li><strong>Visa Details</strong> – Table of visa records (passport number, visa type, issue/expiry dates, visa documents)</li>
<li><strong>Documents</strong> – ID proof, passport, visa, education certificates</li>
<li><strong>Education & Experience</strong> – Academic qualifications and work history</li>
<li><strong>Bank Details</strong> – Bank name, account number, IBAN for salary transfers</li>
<li><strong>Salary Info</strong> – Current salary structure, components, and effective dates</li>
</ul>

<h2>Creating an Employee</h2>
<ol>
<li>Go to <strong>Employee</strong> via Awesome Bar → <strong>New</strong></li>
<li>Fill in the required fields (Employee Name, Company, Date of Joining)</li>
<li>Navigate through the tabs to add all relevant information</li>
<li><strong>Save</strong></li>
</ol>

<h2>Visa Management</h2>
<p>Each employee can have multiple visa records (employment visa, dependent visa, visit visa). The <strong>Visa Expiry Alerts</strong> run daily at 6:00 AM and notify HR Managers of visas expiring within 30 days.</p>""")

    upsert_article("Leave Management", "HR & Payroll", """<h1>Leave Management</h1>

<h2>Leave Types</h2>
<p>Define leave types such as Annual Leave, Sick Leave, Casual Leave, and more. Each type has:</p>
<ul>
<li><strong>Max Days</strong> per year</li>
<li><strong>Carry Forward</strong> rules (if unused leave rolls over)</li>
<li><strong>Encashment</strong> rules (if leave can be cashed out)</li>
<li><strong>Earned Leave</strong> auto-accrual per month</li>
</ul>

<h2>Leave Allocation</h2>
<p>Allocate leave balances to employees for a specific period. Allocations can be done:</p>
<ul>
<li>Manually per employee</li>
<li>Via <strong>Leave Policy Assignment</strong> (bulk allocation using Leave Policies)</li>
<li>Auto-allocated on employee creation (based on policy)</li>
</ul>

<h2>Leave Application</h2>
<ol>
<li>Employee applies via <strong>Leave Application</strong></li>
<li>Selects Leave Type, From/To dates, and reason</li>
<li>Optional: attach supporting documents</li>
<li><strong>Save</strong> – triggers approval workflow</li>
<li>Manager <strong>Approves</strong> or <strong>Rejects</strong></li>
<li>Approved leave deducts from the employee's balance</li>
</ol>

<h2>Leave Control Panel</h2>
<p>HR users can manage all leave applications, view calendar, and process bulk actions from the Leave Control Panel.</p>""")

    upsert_article("Attendance", "HR & Payroll", """<h1>Attendance</h1>

<h2>Marking Attendance</h2>
<ul>
<li><strong>Manual</strong> – Create individual Attendance records</li>
<li><strong>Attendance Tool</strong> – Bulk mark attendance for multiple employees in a date range</li>
<li><strong>Employee Checkin</strong> – Biometric/device integration or manual check-in/out logs</li>
<li><strong>Shift Management</strong> – Assign shifts to employees; auto-calculate early/late arrivals and overtime</li>
</ul>

<h2>Attendance Reports</h2>
<ul>
<li><strong>Monthly Attendance Sheet</strong> – Summary of present/absent/leave/holiday per employee</li>
<li><strong>Attendance Summary</strong> – Aggregate view for payroll processing</li>
<li><strong>Overtime Slip</strong> – Computed overtime based on shift schedules</li>
</ul>""")

    upsert_article("Payroll Processing", "HR & Payroll", """<h1>Payroll Processing</h1>

<h2>Salary Structure</h2>
<p>Each employee is assigned a Salary Structure that defines earning and deduction components:</p>
<ul>
<li><strong>Earnings</strong> – Basic, Housing Allowance, Transport Allowance, Overtime, and other allowances</li>
<li><strong>Deductions</strong> – Income Tax, Social Security, Loan repayments, and other deductions</li>
<li>Components can be fixed amounts or formulas based on other components</li>
</ul>

<h2>Payroll Entry</h2>
<ol>
<li>Go to <strong>Payroll Entry</strong> → <strong>New</strong></li>
<li>Select the <strong>Company</strong>, <strong>Payroll Period</strong>, and <strong>Posting Date</strong></li>
<li>Click <strong>Get Employees</strong> to fetch employees assigned to the selected salary structure</li>
<li><strong>Process Payroll</strong> – CosmOS calculates each employee's salary based on attendance, leave, and salary structure</li>
<li>Review the generated Salary Slips</li>
<li><strong>Submit</strong> to finalise payroll</li>
</ol>

<h2>Salary Slip</h2>
<p>Each employee receives a Salary Slip showing:</p>
<ul>
<li>Earnings breakdown with amounts</li>
<li>Deductions breakdown with amounts</li>
<li>Net pay (total earnings minus total deductions)</li>
<li>Year-to-date totals</li>
</ul>

<h2>Additional Salary</h2>
<p>Used for one-time payments or deductions outside the standard salary structure (e.g., bonuses, penalties). Added to the next payroll run.</p>""")

    upsert_article("WPS Salary File", "HR & Payroll", """<h1>WPS Salary File (UAE)</h1>
<p>The WPS (Wage Protection System) Salary File generates a text file in UAE Central Bank format for salary disbursement through the banking system.</p>

<h2>Prerequisites</h2>
<ul>
<li><strong>Company Bank Account</strong> marked as <strong>Is Company Account</strong> with IBAN and bank code</li>
<li><strong>Employee Bank Details</strong> – Each employee must have Bank Name, IBAN, and Account Number in their Employee record</li>
<li>Payroll processed for the relevant period (or salary amounts known)</li>
</ul>

<h2>Creating a WPS Salary File</h2>
<ol>
<li>Go to <strong>WPS Salary File</strong> → <strong>New</strong></li>
<li>Select <strong>Company</strong> and <strong>Pay Period</strong></li>
<li>In the <strong>WPS Salary Detail</strong> child table, add rows:
  <ul>
  <li>Select <strong>Employee</strong> – name and bank details auto-fill</li>
  <li>Enter the <strong>Salary Amount</strong></li>
  </ul>
</li>
<li>Set the <strong>Posting Date</strong></li>
<li><strong>Submit</strong> – The UAE format text file is automatically generated and attached</li>
<li>Download the file from the <strong>Attachments</strong> section</li>
<li>Upload the file to your bank or the EWPS portal</li>
</ol>

<h2>WPS File Format</h2>
<p>The generated file follows the UAE Central Bank format:</p>
<ul>
<li><strong>Header Record</strong> – File type, company code, bank code, total count, total amount</li>
<li><strong>Detail Records</strong> – One per employee: employee ID, name, IBAN, bank code, amount</li>
<li><strong>Trailer Record</strong> – Total record count, total amount, checksum</li>
</ul>""")

    upsert_article("Gratuity", "HR & Payroll", """<h1>Gratuity (UAE)</h1>
<p>CosmOS automatically calculates UAE end-of-service gratuity based on the applicable Labour Law rules.</p>

<h2>Gratuity Rules</h2>
<ul>
<li><strong>Limited Contract</strong> – Fixed-term contract termination</li>
<li><strong>Unlimited Contract (Termination by Employer)</strong></li>
<li><strong>Unlimited Contract (Resignation by Employee)</strong></li>
</ul>

<h2>Calculation Basis</h2>
<ul>
<li>Basic salary as the calculation base</li>
<li>Service period computed from the employee's date of joining</li>
<li>Different slabs: first 5 years vs. subsequent years</li>
<li>Daily wage = Basic Salary / 30</li>
</ul>

<h2>Generating Gratuity</h2>
<ol>
<li>Go to <strong>Gratuity</strong> → <strong>New</strong></li>
<li>Select the <strong>Employee</strong> – service period and basic salary auto-populate</li>
<li>Choose the <strong>Gratuity Rule</strong> based on contract type</li>
<li>CosmOS calculates the gratuity amount</li>
<li><strong>Save</strong> and <strong>Submit</strong></li>
</ol>""")

    upsert_article("Recruitment", "HR & Payroll", """<h1>Recruitment</h1>

<h2>Job Opening</h2>
<p>Create job postings with:</p>
<ul>
<li>Job title, description, and requirements</li>
<li>Designation, department, and vacancies count</li>
<li>Publish on the website careers page</li>
</ul>

<h2>Job Applicant</h2>
<ul>
<li>Applicants can apply via the website or be added manually</li>
<li>Upload CV/resume and cover letter</li>
<li>Track applicant status: Open, Replied, Interview Scheduled, Rejected, Selected</li>
</ul>

<h2>Interview</h2>
<ul>
<li>Schedule interviews for shortlisted candidates</li>
<li>Multiple rounds with different interviewers</li>
<li>Record interview feedback and ratings</li>
<li>Make hiring decisions (Select/Reject)</li>
</ul>

<h2>Job Offer</h2>
<ul>
<li>Extend offers to selected candidates</li>
<li>Define offer terms: salary, start date, benefits</li>
<li>Track acceptance/rejection</li>
<li>Convert accepted offers to Employee records</li>
</ul>""")

    # ── CRM & Sales ──
    print("Writing CRM & Sales articles...")
    upsert_article("CRM Module Overview", "CRM & Sales", """<h1>CRM Module Overview</h1>
<p>The CRM module manages the complete sales pipeline from lead generation to order confirmation.</p>

<h2>Pipeline Stages</h2>
<ol>
<li><strong>Lead</strong> – Initial inquiry or contact</li>
<li><strong>Opportunity</strong> – Qualified lead with potential value</li>
<li><strong>Customer</strong> – Converted and onboarded</li>
<li><strong>Quotation</strong> – Price proposal sent</li>
<li><strong>Sales Order</strong> – Order confirmed</li>
</ol>""")

    upsert_article("Leads and Opportunities", "CRM & Sales", """<h1>Leads & Opportunities</h1>

<h2>Leads</h2>
<ul>
<li>Capture leads from website forms, events, or manual entry</li>
<li>Store contact details, source, and notes</li>
<li>Qualify leads: add meeting notes, follow-up schedules</li>
<li>Convert to <strong>Customer</strong>, <strong>Opportunity</strong>, or both</li>
<li>Track lead sources via <strong>Campaigns</strong></li>
</ul>

<h2>Opportunities</h2>
<ul>
<li>Track deals through defined <strong>Sales Stages</strong> (Prospecting → Negotiation → Closed Won/Lost)</li>
<li>Set expected revenue and probability</li>
<li>Link to customer, contacts, and quotations</li>
<li>Forecasted revenue feeds into sales analytics</li>
<li>Lost reasons are logged for analysis</li>
</ul>""")

    upsert_article("Customers and Quotations", "CRM & Sales", """<h1>Customers & Quotations</h1>

<h2>Customers</h2>
<ul>
<li>Customer master with addresses, contacts, and payment terms</li>
<li>Group by territory, industry, or customer group</li>
<li>Set credit limits and applicable taxes</li>
<li>View account balance, ageing, and sales history</li>
</ul>

<h2>Quotations</h2>
<ul>
<li>Create quotes for customers with items, quantities, and pricing</li>
<li>Apply discounts, taxes, and shipping charges</li>
<li>Print or email quotation PDF directly</li>
<li>Track validity period</li>
<li>Convert accepted quotations to <strong>Sales Orders</strong></li>
</ul>

<h2>Sales Orders</h2>
<ul>
<li>Confirm customer order with delivery schedule</li>
<li>Reserve stock (if enabled)</li>
<li>Partial deliveries allowed</li>
<li>Link to delivery notes and sales invoices</li>
<li>Item-wise fulfilment tracking</li>
</ul>""")

    # ── Buying & Procurement ──
    print("Writing Buying & Procurement articles...")
    upsert_article("Buying Module Overview", "Buying & Procurement", """<h1>Buying & Procurement</h1>

<h2>Suppliers</h2>
<ul>
<li>Supplier master with contact details, addresses, and payment terms</li>
<li>Supplier grouping by type and industry</li>
<li>Scorecard for performance evaluation</li>
<li>View outstanding bills and payment history</li>
</ul>

<h2>Material Request</h2>
<ul>
<li>Raise requests for materials needed</li>
<li>Set required date and priority</li>
<li>Auto-create Purchase Orders from approved requests</li>
</ul>

<h2>Request for Quotation (RFQ)</h2>
<ul>
<li>Send RFQs to multiple suppliers</li>
<li>Collect and compare quotations</li>
<li>Select the best offer and create Purchase Order</li>
</ul>

<h2>Purchase Order</h2>
<ul>
<li>Formal order to supplier with items, quantities, prices, and delivery date</li>
<li>Taxes, shipping, and discounts applied</li>
<li>Track receipt against order (partial/full)</li>
<li>Create Purchase Receipt and Purchase Invoice from PO</li>
</ul>

<h2>Purchase Receipt</h2>
<ul>
<li>Record goods received from suppliers</li>
<li>Updates stock quantities and valuation</li>
<li>Quality inspection can be triggered on receipt</li>
<li>Serial/batch numbers captured</li>
</ul>""")

    # ── Stock & Inventory ──
    print("Writing Stock & Inventory articles...")
    upsert_article("Stock Module Overview", "Stock & Inventory", """<h1>Stock & Inventory Overview</h1>
<p>Complete inventory management for goods and materials.</p>

<h2>Key Features</h2>
<ul>
<li><strong>Items</strong> – Product master with descriptions, UOM, pricing, and inventory tracking</li>
<li><strong>Warehouses</strong> – Multiple locations with hierarchical structure</li>
<li><strong>Stock Transactions</strong> – Receipts, issues, transfers, and adjustments</li>
<li><strong>Serial & Batch Tracking</strong> – Individual item traceability</li>
<li><strong>Inventory Reports</strong> – Stock balance, ledger, ageing, and valuation</li>
</ul>""")

    upsert_article("Items and Warehouses", "Stock & Inventory", """<h1>Items & Warehouses</h1>

<h2>Items</h2>
<ul>
<li>Create items with name, description, and UOM (Unit of Measure)</li>
<li>Define item type: <strong>Product</strong> (stocked), <strong>Service</strong>, <strong>Consumable</strong></li>
<li>Set default warehouse, valuation method (FIFO/Moving Average)</li>
<li>Enable serial or batch tracking per item</li>
<li>Define multiple prices (selling, buying) per UOM</li>
<li>Item variants for size/colour/configurable attributes</li>
<li>Attach images and barcodes</li>
</ul>

<h2>Warehouses</h2>
<ul>
<li>Create warehouses by location (e.g., Main Store, Warehouse A, Showroom)</li>
<li>Parent-child hierarchy (e.g., "UAE → Dubai → Main Store")</li>
<li>Each warehouse tracks its own stock balance</li>
<li>Store address and contact information</li>
<li>Warehouse-specific inventory reports</li>
</ul>""")

    upsert_article("Stock Transactions", "Stock & Inventory", """<h1>Stock Transactions</h1>

<h2>Stock Entry</h2>
<p>Used for internal stock movements:</p>
<ul>
<li><strong>Material Receipt</strong> – Receive stock from supplier (or use Purchase Receipt)</li>
<li><strong>Material Issue</strong> – Issue stock for consumption or internal use</li>
<li><strong>Material Transfer</strong> – Move stock between warehouses</li>
<li><strong>Manufacture</strong> – Finished goods from raw materials (or use Work Order)</li>
<li><strong>Repack</strong> – Change item composition or packaging</li>
<li><strong>Send to Subcontractor</strong> – Issue raw materials to subcontractor</li>
</ul>

<h2>Delivery Note</h2>
<ul>
<li>Dispatch goods to customers against Sales Orders</li>
<li>Updates stock and accounts (Cost of Goods Sold)</li>
<li>Create Sales Invoice from Delivery Note</li>
<li>Packing list for logistics</li>
</ul>

<h2>Purchase Receipt</h2>
<ul>
<li>Receive goods from suppliers against Purchase Orders</li>
<li>Quality inspection can be conducted at receipt</li>
<li>Updates stock quantity and valuation</li>
</ul>

<h2>Stock Reconciliation</h2>
<ul>
<li>Adjust physical stock vs system stock</li>
<li>Used for initial stock setup or periodic counting</li>
<li>Post positive or negative adjustments</li>
</ul>""")

    upsert_article("Serial and Batch Tracking", "Stock & Inventory", """<h1>Serial & Batch Tracking</h1>

<h2>Serial Numbers</h2>
<ul>
<li>Track individual items through their lifecycle</li>
<li>Each serial number is unique per item</li>
<li>Capture serials on purchase receipt, delivery note, stock entry</li>
<li>View serial history: received, transferred, delivered, returned</li>
<li>Ideal for electronics, machinery, high-value items</li>
</ul>

<h2>Batch Numbers</h2>
<ul>
<li>Track groups of items sharing the same batch/lot</li>
<li>Capture batch number, manufacturing date, expiry date</li>
<li>Auto-assign batches from supplier and date</li>
<li>Ideal for pharmaceuticals, food, chemicals</li>
</ul>""")

    # ── Manufacturing ──
    print("Writing Manufacturing articles...")
    upsert_article("Manufacturing Module", "Manufacturing", """<h1>Manufacturing Module</h1>

<h2>Bill of Materials (BOM)</h2>
<ul>
<li>Define the recipe for manufacturing finished goods</li>
<li>List raw materials with quantities and operations</li>
<li>BOM can have multiple levels (sub-assemblies)</li>
<li>Set scrap/waste percentage</li>
<li>BOM versioning and approval workflow</li>
</ul>

<h2>Work Order</h2>
<ul>
<li>Create a production order for a specific quantity of finished item</li>
<li>Reserve raw materials from warehouse</li>
<li>Track production status: Not Started, In Progress, Completed, Stopped</li>
<li>Multiple Work Orders can reference the same BOM</li>
</ul>

<h2>Job Card</h2>
<ul>
<li>Record time and operations performed during manufacturing</li>
<li>Assign to workers/workstations</li>
<li>Track completion quantity and scrap</li>
<li>Auto-create from Work Order</li>
</ul>

<h2>Production Planning</h2>
<ul>
<li>Plan production based on sales orders and forecasts</li>
<li>Generate Material Requirements Plan (MRP)</li>
<li>Create Production Plan from Master Production Schedule</li>
</ul>

<h2>Routing & Workstations</h2>
<ul>
<li>Define manufacturing routing (sequence of operations)</li>
<li>Each operation has a workstation type, time, and cost</li>
<li>Track machine downtime and efficiency</li>
</ul>""")

    # ── Assets ──
    print("Writing Assets articles...")
    upsert_article("Assets Module", "Assets", """<h1>Assets Module</h1>

<h2>Asset Master</h2>
<ul>
<li>Register fixed assets: equipment, vehicles, buildings, furniture</li>
<li>Asset category, location, and custodian</li>
<li>Purchase date, cost, and supplier</li>
<li>Attach asset images and documents</li>
</ul>

<h2>Depreciation</h2>
<ul>
<li>Straight-line or declining balance methods</li>
<li>Auto-generated depreciation schedule on submission</li>
<li>Monthly or yearly depreciation entries</li>
<li>Pro-rata for partial-year assets</li>
</ul>

<h2>Asset Movements</h2>
<ul>
<li>Transfer assets between employees or locations</li>
<li>Record asset status (Operational, Under Maintenance, Scrapped)</li>
<li>Asset Repair log with costs</li>
</ul>

<h2>Asset Maintenance</h2>
<ul>
<li>Schedule preventive maintenance</li>
<li>Track maintenance tasks and costs</li>
<li>Assign maintenance teams</li>
</ul>""")

    # ── Projects ──
    print("Writing Projects articles...")
    upsert_article("Projects Module", "Projects", """<h1>Projects Module</h1>

<h2>Projects</h2>
<ul>
<li>Create projects with name, start/end dates, and status</li>
<li>Set project budget and expected revenue</li>
<li>Assign project manager and team members</li>
<li>Cost tracking against budget</li>
</ul>

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
<li>Link timesheets to salary (if payroll-enabled)</li>
<li>Generate invoices from billable timesheets</li>
</ul>

<h2>Project Reports</h2>
<ul>
<li>Project profitability</li>
<li>Task completion status</li>
<li>Timesheet summary by employee</li>
<li>Budget vs actual cost variance</li>
</ul>""")

    # ── Support ──
    print("Writing Support articles...")
    upsert_article("Support Module", "Support", """<h1>Support Module</h1>

<h2>Issues</h2>
<ul>
<li>Track customer support requests from creation to resolution</li>
<li>Capture issue description, priority, and type</li>
<li>Assign to support agents</li>
<li>Communication thread within the ticket</li>
<li>Resolution and closure tracking</li>
</ul>

<h2>Service Level Agreements (SLA)</h2>
<ul>
<li>Define response and resolution SLAs per priority</li>
<li>Auto-assign SLA on ticket creation</li>
<li>Track SLA breach/escalation</li>
<li>Reports on SLA compliance</li>
</ul>

<h2>Warranty Claims</h2>
<ul>
<li>Link warranty claims to serial numbers</li>
<li>Track claim status and resolution</li>
<li>Replace/repair decision logging</li>
</ul>""")

    # ── Settings & Setup ──
    print("Writing Settings & Setup articles...")
    upsert_article("Company Setup", "Settings & Setup", """<h1>Company Setup</h1>

<h2>Creating a Company</h2>
<ol>
<li>Go to <strong>Company</strong> via Awesome Bar → <strong>New</strong></li>
<li>Enter Company Name, Abbreviation, and Domain</li>
<li>Select <strong>Country</strong> – this sets default currency, date format, and tax rules</li>
<li>Set <strong>Default Currency</strong></li>
<li>Provide <strong>Registration ID</strong> (e.g., Trade License Number)</li>
<li>Set <strong>Fiscal Year</strong> start and end dates</li>
<li>Optionally upload company logo</li>
<li><strong>Save</strong></li>
</ol>

<h2>Company Settings</h2>
<ul>
<li>Default accounts for different transaction types</li>
<li>Holiday list for attendance calculations</li>
<li>Default bank account for payments</li>
<li>Default terms and tax templates</li>
</ul>""")

    upsert_article("Users and Permissions", "Settings & Setup", """<h1>Users & Permissions</h1>

<h2>Creating Users</h2>
<ol>
<li>Go to <strong>User</strong> via Awesome Bar → <strong>New</strong></li>
<li>Enter Email, Full Name, and temporary password</li>
<li>Assign one or more <strong>Roles</strong> (e.g., Accounts User, HR Manager, System Manager)</li>
<li>Optionally set module profile for workspace access</li>
<li><strong>Save</strong> – user will receive login credentials</li>
</ol>

<h2>Roles</h2>
<p>CosmOS ships with pre-defined roles:</p>
<ul>
<li><strong>System Manager</strong> – Full system access, all modules</li>
<li><strong>Accounts Manager / User</strong> – Finance module access</li>
<li><strong>HR Manager / User</strong> – HR and payroll access</li>
<li><strong>Sales Manager / User</strong> – CRM and sales access</li>
<li><strong>Purchase Manager / User</strong> – Buying and procurement access</li>
<li><strong>Stock Manager / User</strong> – Inventory access</li>
<li><strong>Employee</strong> – Self-service (leave, attendance, timesheets)</li>
</ul>

<h2>Permission Rules</h2>
<ul>
<li><strong>Role-based</strong> – Users inherit permissions from their roles</li>
<li><strong>Document-level</strong> – Define create/read/write/delete/amend/submit per DocType</li>
<li><strong>Row-level</strong> – Restrict access to specific records (e.g., only own department)</li>
<li>Permissions can be set per Company for multi-company setups</li>
</ul>""")

    # ── Update workspace ──
    print("\nUpdating workspace...")
    import json
    ws = frappe.get_doc("Workspace", "CosmOS User Manual")
    ws.content = json.dumps([
        {"type": "card", "card_name": "Getting Started", "card_label": "Getting Started", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "About CosmOS", "shortcut_label": "About CosmOS", "url": "/app/help-article/about-cosmos", "icon": "info", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "User Manual Index", "shortcut_label": "User Manual Index", "url": "/app/help-article/user-manual-index", "icon": "list", "format": "Side"},
        {"type": "card", "card_name": "Accounts & Finance", "card_label": "Accounts & Finance", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "Chart of Accounts", "shortcut_label": "Chart of Accounts", "url": "/app/help-article/chart-of-accounts", "icon": "chart", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Journal Entries", "shortcut_label": "Journal Entries", "url": "/app/help-article/journal-entries", "icon": "edit", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Payments", "shortcut_label": "Payments", "url": "/app/help-article/payments", "icon": "credit-card", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Sales and Purchase Invoices", "shortcut_label": "Sales & Purchase Invoices", "url": "/app/help-article/sales-and-purchase-invoices", "icon": "file-text", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "VAT Guide", "shortcut_label": "VAT (UAE)", "url": "/app/help-article/vat", "icon": "tax", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Financial Reports", "shortcut_label": "Financial Reports", "url": "/app/help-article/financial-reports", "icon": "report", "format": "Side"},
        {"type": "card", "card_name": "HR & Payroll", "card_label": "HR & Payroll", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "HR Module Overview", "shortcut_label": "HR Overview", "url": "/app/help-article/hr-module-overview", "icon": "employees", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Employee Master", "shortcut_label": "Employee Master", "url": "/app/help-article/employee-master", "icon": "user", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Leave Management", "shortcut_label": "Leave Management", "url": "/app/help-article/leave-management", "icon": "calendar", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Attendance", "shortcut_label": "Attendance", "url": "/app/help-article/attendance", "icon": "fingerprint", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Payroll Processing", "shortcut_label": "Payroll Processing", "url": "/app/help-article/payroll-processing", "icon": "bank", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "WPS Salary File", "shortcut_label": "WPS Salary File", "url": "/app/help-article/wps-salary-file", "icon": "download", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Gratuity", "shortcut_label": "Gratuity (UAE)", "url": "/app/help-article/gratuity", "icon": "briefcase", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Recruitment", "shortcut_label": "Recruitment", "url": "/app/help-article/recruitment", "icon": "recruit", "format": "Side"},
        {"type": "card", "card_name": "CRM & Sales", "card_label": "CRM & Sales", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "CRM Overview", "shortcut_label": "CRM Overview", "url": "/app/help-article/crm-module-overview", "icon": "customer", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Leads and Opportunities", "shortcut_label": "Leads & Opportunities", "url": "/app/help-article/leads-and-opportunities", "icon": "lead", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Customers and Quotations", "shortcut_label": "Customers & Quotations", "url": "/app/help-article/customers-and-quotations", "icon": "file-signature", "format": "Side"},
        {"type": "card", "card_name": "Buying & Procurement", "card_label": "Buying & Procurement", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "Buying Overview", "shortcut_label": "Buying Overview", "url": "/app/help-article/buying-module-overview", "icon": "purchase", "format": "Side"},
        {"type": "card", "card_name": "Stock & Inventory", "card_label": "Stock & Inventory", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "Stock Overview", "shortcut_label": "Stock Overview", "url": "/app/help-article/stock-module-overview", "icon": "warehouse", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Items and Warehouses", "shortcut_label": "Items & Warehouses", "url": "/app/help-article/items-and-warehouses", "icon": "stock", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Stock Transactions", "shortcut_label": "Stock Transactions", "url": "/app/help-article/stock-transactions", "icon": "transfer", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Serial and Batch Tracking", "shortcut_label": "Serial & Batch", "url": "/app/help-article/serial-and-batch-tracking", "icon": "barcode", "format": "Side"},
        {"type": "card", "card_name": "Manufacturing & Assets", "card_label": "Manufacturing & Assets", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "Manufacturing", "shortcut_label": "Manufacturing", "url": "/app/help-article/manufacturing-module", "icon": "manufacturing", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Assets", "shortcut_label": "Assets", "url": "/app/help-article/assets-module", "icon": "assets", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Projects", "shortcut_label": "Projects", "url": "/app/help-article/projects-module", "icon": "project", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Support Module", "shortcut_label": "Support", "url": "/app/help-article/support-module", "icon": "support", "format": "Side"},
        {"type": "card", "card_name": "Settings & Setup", "card_label": "Settings & Setup", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "Company Setup", "shortcut_label": "Company Setup", "url": "/app/help-article/company-setup", "icon": "building", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Users and Permissions", "shortcut_label": "Users & Permissions", "url": "/app/help-article/users-and-permissions", "icon": "lock", "format": "Side"},
        {"type": "card", "card_name": "PDF Download", "card_label": "Download", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "Download PDF", "shortcut_label": "Download User Manual (PDF)", "url": "/files/CosmOS_User_Manual_2026-06-23.pdf", "icon": "download", "format": "Side"},
        {"type": "card", "card_name": "Support", "card_label": "Support", "card_type": "Card Break"},
        {"type": "shortcut", "shortcut_name": "Contact Support", "shortcut_label": "Contact Support", "url": "mailto:support@cosmoserp.com", "icon": "email", "format": "Side"},
        {"type": "shortcut", "shortcut_name": "Report an Issue", "shortcut_label": "Report an Issue", "url": "https://github.com/saleelhussain-design/cosmos_docker/issues", "icon": "bug", "format": "Side"}
    ])
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workspace updated.\n")

if __name__ == "__main__":
    build()
