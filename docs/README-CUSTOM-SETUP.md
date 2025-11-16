# Custom Frappe Setup with ERPNext and HRMS

This setup includes a custom Docker image with two officially supported Frappe applications:
- **ERPNext** - Complete ERP solution (includes built-in CRM, Sales, Accounting, Inventory, and more)
- **HRMS** - Human Resource Management System

## Prerequisites

- Docker Desktop (for Mac/Windows) or Docker Engine (for Linux)
- At least 4GB of free RAM
- 10GB of free disk space

## Quick Start

### Step 1: Build the Custom Image

Run the build script to create a custom Docker image with all three apps:

```bash
./build-custom-image.sh
```

**Note:** This will take 15-30 minutes depending on your system. The script will:
- Read the `apps.json` file containing ERPNext and HRMS
- Build a custom Docker image tagged as `frappe-custom:v15`
- Configure it for ARM64 architecture (Apple Silicon)

### Step 2: Start the Services

Once the build is complete, start all services:

```bash
docker compose -f pwd.yml up -d
```

### Step 3: Wait for Initialization

The first startup takes 2-3 minutes as it:
- Initializes the database
- Creates a new site called "frontend"
- Installs ERPNext and HRMS apps

You can monitor the progress with:

```bash
docker compose -f pwd.yml logs -f create-site
```

Wait until you see a message indicating the site has been created successfully.

### Step 4: Access the System

Once ready, access the system at:

**URL:** http://localhost:8080

**Login Credentials:**
- Username: `Administrator`
- Password: `admin`

## What's Included

### ERPNext
Full-featured ERP with modules for:
- **CRM** - Lead Management, Opportunities, Sales Pipeline
- **Sales & Purchase** - Quotations, Orders, Invoices
- **Accounting** - General Ledger, Accounts Payable/Receivable, Financial Reports
- **Inventory Management** - Stock, Warehouses, Serial/Batch Numbers
- **Manufacturing** - BOM, Work Orders, Production Planning
- **Projects** - Project Management, Tasks, Timesheets
- **Assets** - Asset Management, Maintenance
- And much more...

### HRMS
Human Resource Management with:
- **Employee Management** - Employee Records, Organizational Chart
- **Attendance & Leave** - Attendance Tracking, Leave Management
- **Payroll** - Salary Structure, Payroll Processing
- **Recruitment** - Job Openings, Job Applications
- **Performance Management** - Appraisals, Goals
- **Expense Claims** - Employee Advances, Expense Claims

## Managing the Setup

### Stop Services
```bash
docker compose -f pwd.yml down
```

### View Logs
```bash
# All services
docker compose -f pwd.yml logs -f

# Specific service
docker compose -f pwd.yml logs -f backend
```

### Restart Services
```bash
docker compose -f pwd.yml restart
```

### Remove Everything (including data)
```bash
docker compose -f pwd.yml down -v
```

## Troubleshooting

### Build Fails
- Ensure you have a stable internet connection
- Check that Docker has enough resources allocated (4GB+ RAM)
- Try running the build script again

### Services Won't Start
- Check if ports 8080 is already in use: `lsof -i :8080`
- Ensure Docker is running: `docker ps`
- Check logs: `docker compose -f pwd.yml logs`

### Can't Access at localhost:8080
- Wait 2-3 minutes after starting services
- Check if the create-site service completed: `docker compose -f pwd.yml ps`
- Verify the frontend service is running: `docker compose -f pwd.yml logs frontend`

## Architecture Notes

This setup uses:
- **MariaDB 10.6** for the database
- **Redis** for caching and job queues
- **Nginx** as the web server
- **Node.js** for real-time websockets
- **Python** for the backend application

All services run in separate containers and communicate over a Docker network.

## Customization

To add or remove apps, edit the `apps.json` file and rebuild:

```bash
# Edit apps.json to add more Frappe apps
nano apps.json

# Rebuild the image
./build-custom-image.sh

# Restart services
docker compose -f pwd.yml down
docker compose -f pwd.yml up -d
```

**Note:** ERPNext already includes comprehensive CRM functionality. If you need a standalone modern CRM, consider using Frappe CRM separately instead of with ERPNext to avoid feature overlap.

## Support

For issues specific to:
- **Frappe Framework:** https://github.com/frappe/frappe
- **ERPNext:** https://github.com/frappe/erpnext
- **HRMS:** https://github.com/frappe/hrms
- **Docker Setup:** https://github.com/frappe/frappe_docker

