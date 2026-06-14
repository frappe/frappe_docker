# ERPNext On-Premises Deployment Guide
### Windows + WSL2 · Cloudflare Tunnel · Zero Trust · S3 Backup

> **Use case:** Self-hosted ERPNext on an office/home Windows machine, accessible
> only to internal team via Cloudflare WARP, with automated S3 backups.
> **Monthly cost: ~₹200–300 (electricity only)**

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites Checklist](#2-prerequisites-checklist)
3. [Windows Machine Preparation](#3-windows-machine-preparation)
4. [WSL2 Setup](#4-wsl2-setup)
5. [Install Docker in WSL2](#5-install-docker-in-wsl2)
6. [Deploy ERPNext](#6-deploy-erpnext)
7. [Create Your Site](#7-create-your-site)
8. [Cloudflare Setup](#8-cloudflare-setup)
   - [8a. Move DNS from GoDaddy → Cloudflare](#8a-move-dns-from-godaddy--cloudflare)
   - [8b. Cloudflare Tunnel](#8b-cloudflare-tunnel)
   - [8c. Zero Trust Access + WARP](#8c-zero-trust-access--warp)
9. [Auto-Start on Windows Boot](#9-auto-start-on-windows-boot)
10. [Backup Policy — S3 Every 3 Days](#10-backup-policy--s3-every-3-days)
11. [Restore Process](#11-restore-process)
12. [Upgrading ERPNext Version](#12-upgrading-erpnext-version)
13. [Useful Day-to-Day Commands](#13-useful-day-to-day-commands)
14. [Quick Reference](#14-quick-reference)

---

## 1. Architecture Overview

```
Windows Machine (office/home — stays ON 24/7)
│
└── WSL2 (Ubuntu — real Linux kernel)
      │
      ├── Docker Engine
      │     └── ERPNext Stack
      │           ├── MariaDB 11.8        (database)
      │           ├── Redis ×2            (cache + queue)
      │           ├── backend             (Gunicorn / ERPNext)
      │           ├── frontend            (Nginx)
      │           ├── websocket           (Socket.IO)
      │           ├── queue-short/long    (background jobs)
      │           └── scheduler           (scheduled tasks)
      │
      ├── cloudflared (systemd service — always running)
      │     └── outbound HTTPS tunnel → Cloudflare Edge
      │                                       │
      │                              inventory.macrobalance.in
      │                         (private — WARP users only)
      │
      └── crontab
            └── every 3 days at 2 AM
                  └── bench backup → push_backup.py → S3

GoDaddy
└── Domain registrar only (macrobalance.in renewal)

Cloudflare (free)
├── DNS management for macrobalance.in       (moved from GoDaddy)
├── macrobalance.in main site → EC2          (unchanged, auto-imported)
├── Cloudflare Tunnel                (private route to office machine)
├── Zero Trust Access                (identity policy — @macrobalance.in only)
└── WARP app                         (employee device client)

AWS S3
└── macrobalance-db-backups/
      └── inventory-backups/
            └── backups (auto-deleted after 30 days)
```

**What outside world sees:**
```
Anyone types inventory.macrobalance.in → "This site can't be reached" ❌
Employee with WARP ON → inventory.macrobalance.in → ERPNext ✅
```

---

## 2. Prerequisites Checklist

Before starting, have these ready:

- [ ] Windows machine (min 4 GB RAM, 50 GB free disk, 64-bit CPU)
- [ ] Docker Desktop installed on Windows (with WSL2 backend)
- [ ] GoDaddy account — `macrobalance.in` domain registered here
- [ ] Cloudflare account — free signup at cloudflare.com
- [ ] AWS account — for S3 backups
- [ ] AWS S3 bucket created (`macrobalance-db-backups`)
- [ ] AWS IAM user with S3 write access (Access Key + Secret Key saved)
- [ ] Stable internet connection (broadband recommended)
- [ ] UPS recommended (keeps machine alive during power cuts)

### Minimum Hardware

| Spec | Minimum | Comfortable |
|---|---|---|
| RAM | 4 GB | 8 GB |
| CPU | Any 64-bit (x86 or ARM) | 4+ cores |
| Disk | 50 GB free | 100 GB |
| OS | Windows 10 (21H2+) | Windows 11 |
| Internet | 10 Mbps | 50 Mbps+ |

---

## 3. Windows Machine Preparation

### Disable Sleep (Critical — machine must stay ON)

```
Control Panel → Power Options → Change plan settings
→ "Turn off the display": 1 hour (or Never)
→ "Put the computer to sleep": Never ← important
→ Save changes
```

Or via PowerShell (run as Administrator):
```powershell
# Never sleep when plugged in
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 60
```

### Disable Automatic Restarts from Windows Update

```
Settings → Windows Update → Advanced Options
→ "Restart this device as soon as possible": OFF
→ Set Active Hours: your business hours (e.g. 8 AM – 10 PM)
  Windows will only restart outside these hours
```

### Add Docker Volume Folder to Antivirus Exclusions

Antivirus scanning Docker volumes causes MariaDB slowness.

```
Windows Security → Virus & Threat Protection
→ Manage Settings → Exclusions → Add an exclusion → Folder
→ Add: C:\Users\<you>\AppData\Local\Docker\
→ Add: \\wsl$\Ubuntu\   (WSL2 filesystem)
```

---

## 4. WSL2 Setup

### Enable Systemd in WSL2

> Systemd allows services (cloudflared, Docker) to run permanently
> even when no terminal window is open.

Create or edit `C:\Users\<you>\.wslconfig` on Windows:

```ini
[wsl2]
systemd=true
memory=3GB      # limit WSL2 RAM usage (adjust based on your total RAM)
processors=2    # limit CPU cores
```

> Set `memory` to ~75% of your total RAM.
> e.g. 8 GB machine → set `memory=6GB`

### Install WSL2 with Ubuntu

```powershell
# In Windows PowerShell (as Administrator)
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2

# Restart Windows after installation
# Then open Ubuntu from Start Menu — set username and password
```

### Verify WSL2 is Working

```bash
# Inside WSL2 terminal (Ubuntu)
uname -r                # should show Linux kernel version
systemctl --version     # should show systemd if enabled
```

---

## 5. Install Docker in WSL2

```bash
# Inside WSL2 terminal

# Install Docker Engine (native Linux — better performance than Docker Desktop)
curl -fsSL https://get.docker.com | bash

# Allow your user to run Docker without sudo
sudo usermod -aG docker $USER
newgrp docker

# Enable Docker to start automatically with WSL2
sudo systemctl enable docker
sudo systemctl start docker

# Verify
docker --version           # Docker 24.x or higher
docker compose version     # Docker Compose v2.x
```

---

## 6. Deploy ERPNext

```bash
# Inside WSL2

# Clone frappe_docker repository
git clone https://github.com/frappe/frappe_docker
cd frappe_docker

# Create config directory
mkdir -p ~/gitops

# Copy and edit environment file
cp example.env ./gitops/erpnext.env
nano ./gitops/erpnext.env
```

Set these values in `~/gitops/erpnext.env`:

```env
# ── ERPNext Version ──────────────────────────────────────────────
# Check latest: https://github.com/frappe/erpnext/releases
ERPNEXT_VERSION=v16.22.0

# ── Database ─────────────────────────────────────────────────────
DB_PASSWORD=your_very_secure_db_password

# ── Gunicorn Performance ─────────────────────────────────────────
# Reduce workers for lower-spec machines
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
GUNICORN_TIMEOUT=120
```

> ⚠️ **No LETSENCRYPT_EMAIL or SITES_RULE needed.**
> Cloudflare Tunnel handles SSL and routing — we use `compose.noproxy.yaml`
> instead of `compose.https.yaml`.

### Merge Compose Files

```bash
cd ~/frappe_docker

docker compose \
  --env-file ~/gitops/erpnext.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > ./gitops/docker-compose.yml
```

### Start ERPNext

```bash
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  up -d

# Verify all containers are running
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  ps
```

All these containers should show `running`:

```
erpnext-db-1           MariaDB 11.8
erpnext-redis-cache-1  Redis
erpnext-redis-queue-1  Redis
erpnext-backend-1      Gunicorn
erpnext-frontend-1     Nginx (port 8080)
erpnext-websocket-1    Socket.IO
erpnext-queue-short-1  RQ Worker
erpnext-queue-long-1   RQ Worker
erpnext-scheduler-1    Scheduler
```

---

## 7. Create Your Site

> ⏳ Wait 15 seconds after `up -d` — MariaDB needs to initialize first.

```bash
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  exec backend bench new-site \
  --mariadb-user-host-login-scope=% \
  --db-root-password Root@1234 \
  --install-app erpnext \
  --admin-password Root@1234 \
  inventory.macrobalance.in
```

This takes **3–8 minutes**. Once complete, ERPNext is running on `localhost:8080` inside WSL2.

Test it locally:
```bash
curl http://localhost:8080
# Should return HTML (Frappe login page)
```

---

## 8. Cloudflare Setup

### 8a. Move DNS from GoDaddy → Cloudflare

> **What changes on GoDaddy:** Only the nameservers.
> Domain stays registered at GoDaddy. Your existing macrobalance.in website on EC2 is unaffected.

#### Step 1 — Add macrobalance.in to Cloudflare

```
cloudflare.com → Log in → Add a Site → type: macrobalance.in
→ Select Free plan ($0)
→ Cloudflare scans and imports all GoDaddy DNS records automatically
→ Review imported records:
    A    macrobalance.in → <EC2 IP>      ✅ (your main site — keep this)
    A    www     → <EC2 IP>      ✅
    MX   ...     → ...           ✅ (email records — keep all)
→ Note the 2 Cloudflare nameservers shown:
    e.g.  chad.ns.cloudflare.com
          lola.ns.cloudflare.com
```

#### Step 2 — Change Nameservers on GoDaddy

```
GoDaddy → My Products → macrobalance.in
→ DNS → Nameservers → Change → Custom
→ Enter the 2 Cloudflare nameserver addresses from Step 1
→ Save

Propagation: 5 minutes – 2 hours
Cloudflare Dashboard shows "Active" when complete ✅
```

**Impact check:**
```
macrobalance.in website  → still works ✅ (same A record, now served via Cloudflare CDN)
Email MX records → still work ✅ (auto-imported)
inventory.macrobalance.in → does NOT exist yet (we add it via Tunnel next)
```

---

### 8b. Cloudflare Tunnel

The Tunnel connects your WSL2 machine to Cloudflare privately.
No open ports. No public IP needed.

#### Install cloudflared in WSL2

```bash
# Inside WSL2
curl -L \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
  -o cloudflared.deb

sudo dpkg -i cloudflared.deb
cloudflared --version    # verify install
```

#### Create and Configure the Tunnel

```bash
# Authenticate with your Cloudflare account
# This opens a browser window — log in and authorize
cloudflared tunnel login

# Create a tunnel
cloudflared tunnel create erpnext-tunnel

# Note the Tunnel ID shown (looks like: a1b2c3d4-...)
# A credentials file is created at: ~/.cloudflared/<tunnel-id>.json
```

#### Create Tunnel Config File

```bash
nano ~/.cloudflared/config.yml
```

```yaml
tunnel: erpnext-tunnel
credentials-file: /home/<your-wsl-username>/.cloudflared/<tunnel-id>.json
protocol: http2

ingress:
  - hostname: inventory.macrobalance.in
    service: http://localhost:8080    # ERPNext Nginx port
  - service: http_status:404         # catch-all (required)
```

Replace `<your-wsl-username>` and `<tunnel-id>` with your actual values.

#### Route Domain Through Tunnel

```bash
# Creates a CNAME record in Cloudflare DNS (not a public A record)
cloudflared tunnel route dns erpnext-tunnel inventory.macrobalance.in
```

> This creates `inventory.macrobalance.in → <tunnel-id>.cfargotunnel.com`
> in Cloudflare DNS. It is proxied through Cloudflare — not a direct IP.
> Outside world cannot reach it without WARP.

#### Run Tunnel as Systemd Service

```bash
# Install cloudflared as a system service
sudo cloudflared --config /home/<username>/.cloudflared/config.yml service install

# Enable and start
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Verify it's running
sudo systemctl status cloudflared
```

Test the tunnel:
```bash
# From any device on Cloudflare WARP, visit https://inventory.macrobalance.in
# Should load ERPNext login page ✅
```

---

### 8c. Zero Trust Access + WARP

This ensures `inventory.macrobalance.in` is **completely inaccessible** to anyone
not connected via Cloudflare WARP — no login page, no content, nothing.

> **Approach used:** Public hostname in Cloudflare Tunnel + WARP Device Posture
> check on the Access Policy. The site URL exists publicly, but Cloudflare
> blocks all traffic at the edge unless the device is actively connected to WARP
> and enrolled in your Zero Trust organization.

#### Set Up Zero Trust Organization

```
Cloudflare Dashboard → Zero Trust
→ First time: choose organization name
  e.g. "macrobalance"
  → Creates: macrobalance.cloudflareaccess.com
```

#### Step 1 — Create Device Enrollment Policy

```
Zero Trust → Settings → WARP Client
→ Device enrollment permissions → Manage
→ Add a rule:
    Rule name:  Allow Enrollment
    Action:     Allow
    Include:
      Selector: Emails ending in
      Value:    macrobalance.in
→ Save
```

This controls who is allowed to enroll their device into your Zero Trust org.

#### Step 2 — Create Access Application

```
Zero Trust → Access → Applications → Add an Application
→ Type: Self-hosted
→ Application name: Inventory ERPNext
→ Session Duration: 24 hours (or your preference)
→ Application domain: inventory.macrobalance.in

→ Next
```

#### Step 3 — Create Access Policy with WARP Posture Check

> ⚠️ This is the critical step that makes the site inaccessible without WARP.

```
Policy name: Allow Company Staff
Action:      Allow

── Include rule (WHO can access) ──────────────────────────────────────
  Selector: Emails ending in
  Value:    macrobalance.in

── Require rule (HOW they must connect) ───────────────────────────────
  Selector: WARP
  Value:    Connected

→ Save policy
→ Save application
```

**What this means:**
- ✅ Enrolled device + WARP ON + company email → Access granted
- ❌ WARP OFF (disconnected) → Cloudflare blocks at edge (HTTP 403)
- ❌ WARP ON but wrong email (outsider) → Blocked
- ❌ WARP ON but not enrolled → Blocked

#### Step 4 — Employee One-Time Enrollment Steps

```
1. Download WARP app:  https://1.1.1.1/
   (Windows, Mac, iOS, Android — all supported)

2. Open Cloudflare One Client
   → Click "Continue" under "Cloudflare One Client" (right option)

3. Enter team name: macrobalance
   (or click the enrollment link sent by admin)

4. Browser opens → sign in with company email → receive OTP → enter it

5. WARP enrolls and connects automatically ✅
```

#### Daily Use

```
WARP ON  (connected + enrolled) → inventory.macrobalance.in → ERPNext ✅
WARP OFF (disconnected)         → inventory.macrobalance.in → 403 Blocked ❌
No WARP installed               → inventory.macrobalance.in → 403 Blocked ❌
```

> **Note:** The domain technically exists publicly (it resolves via Cloudflare
> Tunnel), but Cloudflare's edge server returns a block page — no application
> content is ever served. For a site that is completely invisible (doesn't even
> resolve) to non-WARP users, you would need to use Private Network routing
> instead, which requires a static server IP.

#### Verify Access Control Works

```
Test 1: Disconnect WARP on any device
→ Visit https://inventory.macrobalance.in
→ Expected: Cloudflare "403 Forbidden / Access Denied" page ✅

Test 2: Connect WARP (enrolled device, company email)
→ Visit https://inventory.macrobalance.in
→ Expected: ERPNext login page loads ✅

Test 3: WARP connected but using personal email (not @macrobalance.in)
→ Visit https://inventory.macrobalance.in
→ Expected: Cloudflare "Access Denied" page ✅

Test 4: macrobalance.in (main site)
→ WARP ON or OFF — site loads normally for everyone ✅
```

---

## 9. Auto-Start on Windows Boot (Optional)

All services must restart automatically when Windows reboots.

### Step 1 — ERPNext as Systemd Service in WSL2

```bash
# Inside WSL2
sudo nano /etc/systemd/system/erpnext.service
```

```ini
[Unit]
Description=ERPNext Docker Stack
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=<your-wsl-username>
WorkingDirectory=/home/<your-wsl-username>/frappe_docker
ExecStart=docker compose --project-name erpnext \
  -f /home/<your-wsl-username>/gitops/docker-compose.yml up -d
ExecStop=docker compose --project-name erpnext \
  -f /home/<your-wsl-username>/gitops/docker-compose.yml down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable erpnext
sudo systemctl start erpnext
```

### Step 2 — Auto-start WSL2 on Windows Login

```powershell
# In Windows PowerShell (as Administrator)
# Creates a task that starts WSL2 silently at Windows login

$action = New-ScheduledTaskAction `
    -Execute "wsl.exe" `
    -Argument "-d Ubuntu-22.04 --exec sleep infinity"

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit 0 `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName  "Start-WSL2-ERPNext" `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -RunLevel  Highest `
    -Force

Write-Host "WSL2 auto-start configured ✅"
```

### Boot Sequence After Setup

```
Windows powers on
        │
        ▼
Windows Task Scheduler starts WSL2
        │
        ▼
WSL2 systemd starts services:
  ├── docker.service          ✅
  ├── erpnext.service         ✅ (ERPNext containers start)
  └── cloudflared.service     ✅ (Tunnel connects to Cloudflare)
        │
        ▼
~60 seconds after boot:
  inventory.macrobalance.in is live for WARP users ✅
```

---

## 10. Backup Policy — S3 Every 3 Days

### AWS Setup

#### Create S3 Bucket
```
AWS Console → S3 → Create bucket
  Name:   macrobalance-db-backups
  Region: ap-south-1
  Block all public access: ON ✅
```

#### Create IAM User
```
AWS Console → IAM → Users → Create user
  Username: erpnext-backup-user
```

Attach this scoped IAM policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ],
    "Resource": [
      "arn:aws:s3:::macrobalance-db-backups",
      "arn:aws:s3:::macrobalance-db-backups/*"
    ]
  }]
}
```

Save the **Access Key ID** and **Secret Access Key**.

### Create Backup Script

```bash
# Inside WSL2
nano ~/backup-erpnext.sh
```

```bash
#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# ERPNext Backup to S3 — On-Premises WSL2 Setup
# ─────────────────────────────────────────────────────────────────

# ── CONFIG ───────────────────────────────────────────────────────
PROJECT="erpnext"
SITE="inventory.macrobalance.in"
COMPOSE_FILE="$HOME/gitops/docker-compose.yml"
S3_BUCKET="macrobalance-db-backups"
S3_REGION="ap-south-1"
AWS_KEY="your-aws-access-key-id"
AWS_SECRET="your-aws-secret-access-key"
LOG="$HOME/gitops/backup.log"
# ─────────────────────────────────────────────────────────────────

echo "" >> $LOG
echo "==========================================" >> $LOG
echo "Backup started: $(date)" >> $LOG
echo "==========================================" >> $LOG

# Step 1: Local backup (DB + files)
echo "[1/2] Creating local backup..." >> $LOG
docker compose --project-name $PROJECT \
  -f $COMPOSE_FILE \
  exec -T backend \
  bench --site $SITE backup --with-files >> $LOG 2>&1

if [ $? -ne 0 ]; then
  echo "ERROR: bench backup failed!" >> $LOG
  exit 1
fi

echo "[1/2] Local backup created OK." >> $LOG

# Step 2: Push to S3
echo "[2/2] Uploading to S3..." >> $LOG
docker compose --project-name $PROJECT \
  -f $COMPOSE_FILE \
  exec -T backend \
  push_backup.py \
  --site-name $SITE \
  --bucket $S3_BUCKET \
  --region-name $S3_REGION \
  --aws-access-key-id $AWS_KEY \
  --aws-secret-access-key $AWS_SECRET >> $LOG 2>&1

if [ $? -ne 0 ]; then
  echo "ERROR: S3 upload failed!" >> $LOG
  exit 1
fi

echo "[2/2] S3 upload completed OK." >> $LOG
echo "Backup finished: $(date)" >> $LOG
```

```bash
chmod +x ~/backup-erpnext.sh

# Create log file
touch ~/gitops/backup.log
```

### Test Backup Manually

```bash
~/backup-erpnext.sh

# Watch live
tail -f ~/gitops/backup.log
```

Expected output:
```
==========================================
Backup started: Sat Jun 14 02:00:01 IST 2026
==========================================
[1/2] Creating local backup...
[1/2] Local backup created OK.
[2/2] Uploading to S3...
[2/2] S3 upload completed OK.
Backup finished: Sat Jun 14 02:03:22 IST 2026
```

### Schedule via Crontab (Every 3 Days at 2 AM)

```bash
crontab -e
```

Add this line:
```cron
# ERPNext backup every 3 days at 2:00 AM
0 2 */3 * * /home/<your-wsl-username>/backup-erpnext.sh
```

Verify:
```bash
crontab -l
```

### S3 Lifecycle Policy (Auto-delete After 30 Days)

```bash
# Install AWS CLI in WSL2
sudo apt install -y awscli

# Configure
aws configure
# Enter Access Key, Secret Key, Region (ap-south-1), output format (json)

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket macrobalance-db-backups \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "delete-old-backups",
      "Status": "Enabled",
      "Filter": {"Prefix": "inventory-backups/"},
      "Expiration": {"Days": 30}
    }]
  }'

# Verify backups exist
aws s3 ls s3://macrobalance-db-backups/ --recursive
```

### Backup File Structure in S3

```
s3://macrobalance-db-backups/
└── inventory-backups/
      ├── 20260614_020001-inventory.macrobalance.in-database.sql.gz   ← MariaDB dump
      ├── 20260614_020001-inventory.macrobalance.in-files.tar          ← public uploads
      └── 20260614_020001-inventory.macrobalance.in-private-files.tar  ← private uploads
```

---

## 11. Restore Process

Use when: data corruption, accidental deletion, migrating to a new machine.

### Step 1 — Download Backup from S3

```bash
# List available backups
aws s3 ls s3://macrobalance-db-backups/inventory-backups/

# Download the backup you want to restore
aws s3 cp \
  s3://macrobalance-db-backups/inventory-backups/20260614_020001-inventory.macrobalance.in-database.sql.gz \
  /tmp/

aws s3 cp \
  s3://macrobalance-db-backups/inventory-backups/20260614_020001-inventory.macrobalance.in-files.tar \
  /tmp/

aws s3 cp \
  s3://macrobalance-db-backups/inventory-backups/20260614_020001-inventory.macrobalance.in-private-files.tar \
  /tmp/
```

### Step 2 — Copy Files Into Container

```bash
BACKUP_DIR="/home/frappe/frappe-bench/sites/inventory.macrobalance.in/private/backups"

# Create backup directory inside container
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  exec backend mkdir -p $BACKUP_DIR

# Copy backup files into container
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  cp /tmp/20260614_020001-inventory.macrobalance.in-database.sql.gz \
  backend:$BACKUP_DIR/

docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  cp /tmp/20260614_020001-inventory.macrobalance.in-files.tar \
  backend:$BACKUP_DIR/

docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  cp /tmp/20260614_020001-inventory.macrobalance.in-private-files.tar \
  backend:$BACKUP_DIR/
```

### Step 3 — Restore Database + Files

```bash
BACKUP_DIR="/home/frappe/frappe-bench/sites/inventory.macrobalance.in/private/backups"

docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  exec backend bench --site inventory.macrobalance.in restore \
  $BACKUP_DIR/20260614_020001-inventory.macrobalance.in-database.sql.gz \
  --with-public-files $BACKUP_DIR/20260614_020001-inventory.macrobalance.in-files.tar \
  --with-private-files $BACKUP_DIR/20260614_020001-inventory.macrobalance.in-private-files.tar \
  --db-root-password your_very_secure_db_password
```

### Step 4 — Run Migrations + Clear Cache

```bash
# Always run after restore
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  exec backend bench --site inventory.macrobalance.in migrate

# Clear cache
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  exec backend bench --site inventory.macrobalance.in clear-cache
```

### Restore on a Brand New Machine (Disaster Recovery)

```bash
# 1. Set up WSL2 + Docker (Sections 4–5)
# 2. Deploy ERPNext (Section 6)
# 3. Create empty site first:
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  exec backend bench new-site \
  --mariadb-user-host-login-scope=% \
  --db-root-password your_db_password \
  --install-app erpnext \
  --admin-password temp_password \
  inventory.macrobalance.in

# 4. Then follow Steps 1–4 above to restore from S3
#    (restore overwrites the empty site with your backup data)
```

---

## 12. Upgrading ERPNext Version

When Frappe releases a new version (e.g. `v16.23.0`):

```bash
# 1. ALWAYS backup first
~/backup-erpnext.sh

# 2. Update version in env file
nano ~/gitops/erpnext.env
# Change: ERPNEXT_VERSION=v16.23.0

# 3. Regenerate merged compose file
cd ~/frappe_docker
docker compose \
  --env-file ~/gitops/erpnext.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > ./gitops/docker-compose.yml

# 4. Pull new images
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml pull

# 5. Restart with new images
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml up -d

# 6. Run DB migrations (required after every version upgrade)
docker compose --project-name erpnext \
  -f ./gitops/docker-compose.yml \
  exec backend bench --site inventory.macrobalance.in migrate
```

---

## 13. Useful Day-to-Day Commands

### Add Alias to ~/.bashrc

```bash
echo "alias dc='docker compose --project-name erpnext -f ./gitops/docker-compose.yml'" >> ~/.bashrc
source ~/.bashrc
```

### Common Operations

```bash
# ── Status ────────────────────────────────────────────────────────
dc ps                                     # all containers + status
dc logs -f backend                        # tail backend logs
dc logs -f proxy                          # tail tunnel/proxy logs
sudo systemctl status cloudflared         # Cloudflare Tunnel status
sudo systemctl status erpnext             # ERPNext service status

# ── Start / Stop ─────────────────────────────────────────────────
dc up -d                                  # start all containers
dc down                                   # stop all containers
dc restart backend                        # restart only backend

# ── Site management ───────────────────────────────────────────────
dc exec backend bench list-sites
dc exec backend bench --site inventory.macrobalance.in list-apps
dc exec backend bench --site inventory.macrobalance.in console
dc exec backend bench --site inventory.macrobalance.in migrate
dc exec backend bench --site inventory.macrobalance.in clear-cache

# ── Manual backup ─────────────────────────────────────────────────
~/backup-erpnext.sh                       # full backup + S3 push
tail -50 ~/gitops/backup.log              # check backup history

# ── Database access ───────────────────────────────────────────────
dc exec db mariadb -u root -pyour_db_password

# ── Cloudflare Tunnel ─────────────────────────────────────────────
sudo systemctl restart cloudflared
cloudflared tunnel info erpnext-tunnel
cloudflared tunnel list

# ── Disk usage ────────────────────────────────────────────────────
df -h                                     # WSL2 disk usage
docker system df                          # Docker volumes size
```

---

## 14. Quick Reference

### File Locations

| File | Path | Purpose |
|---|---|---|
| Environment config | `~/gitops/erpnext.env` | All env variables |
| Merged compose YAML | `./gitops/docker-compose.yml` | Deployed config |
| Backup script | `~/backup-erpnext.sh` | Runs backup + S3 push |
| Backup log | `~/gitops/backup.log` | Backup history |
| Cloudflare config | `~/.cloudflared/config.yml` | Tunnel config |
| WSL2 config | `C:\Users\<you>\.wslconfig` | WSL2 memory/CPU limits |

### Cost Breakdown

| Item | Cost |
|---|---|
| Windows machine (existing) | ₹0 |
| WSL2 + Docker | ₹0 |
| Cloudflare (DNS + Tunnel + Zero Trust + WARP) | ₹0 |
| AWS S3 backup storage (~5 GB/month) | ~₹35/month |
| Electricity (desktop 24/7) | ~₹200–400/month |
| Domain renewal (macrobalance.in via GoDaddy) | ~₹100/month |
| **Total** | **~₹335–535/month** |

### Service Comparison

| | AWS EC2 Setup | On-Premises WSL2 Setup |
|---|---|---|
| Server cost | ~₹1,850/month | ₹0 (existing machine) |
| Public IP | AWS Elastic IP | Not needed (Cloudflare Tunnel) |
| SSL/HTTPS | Traefik + Let's Encrypt | Cloudflare (automatic) |
| Access control | Cloudflare WARP | Cloudflare WARP |
| Backup | S3 via crontab | S3 via crontab |
| Uptime risk | Low (AWS managed) | Medium (depends on your power/internet) |
| Best for | Production scale | Early-stage startup |

### Recommended UPS

For power cut protection — keep machine running during 30–60 min outages:

```
APC Back-UPS 600VA / 1000VA
Cost: ₹3,000–6,000 (one-time)
Protects: Desktop + Router + Switch
Runtime: 30–60 minutes at full load
```

---

*Generated for: `inventory.macrobalance.in` · ERPNext v16 · Windows WSL2 · On-Premises · Cloudflare Free*
