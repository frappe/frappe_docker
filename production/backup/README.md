# ERPNext Backup System - Complete Guide

Automated backup system with Digital Ocean Spaces (S3) for ERPNext production.

---

## 🚀 Quick Production Setup (5 minutes)

### Option 1: Interactive Setup

```bash
cd production/backup
./manage-backups.sh setup    # Interactive wizard
chmod 600 backup.env
./manage-backups.sh start
./manage-backups.sh test
```

### Option 2: Manual Configuration

**Edit `backup/backup.env`:**
```bash
ENV_PREFIX=production              # Change from 'development'
BACKUP_SITES=your-domain.com       # Change from 'erp.localhost'
S3_BACKUP_RETENTION_DAYS=30        # Increase from 5
S3_ACCESS_KEY_ID=your-key
S3_SECRET_ACCESS_KEY=your-secret
```

**Deploy:**
```bash
chmod 600 backup/backup.env
./manage-backups.sh restart
./manage-backups.sh test
./manage-backups.sh list-s3 | grep "production/"
```

**Verify automated backups:**
- Hourly DB backup runs every hour from container start time
- Daily full backup runs at 3:00 AM
- Check status: `./manage-backups.sh status`
- Monitor logs: `./manage-backups.sh logs`

---

## 📦 What Gets Backed Up?

### Always Included
✅ **Database** - All data, doctypes, settings (compressed SQL)

### Backup Modes

**Full Backup** (recommended for daily):
```bash
BACKUP_WITH_FILES=1    # Everything: DB + all files + site_config
```

**Database Only** (recommended for frequent/hourly):
```bash
BACKUP_WITH_FILES=0    # Database + site_config only
```

**What's in site_config.json:**
```json
{
  "db_name": "_73c82ec6d255ebe3",
  "db_password": "Dp0yVfnoBvwYpR0y",
  "db_type": "mariadb"
}
```
*Note: production.env and other secrets are NOT included*

---

## ⏰ Backup Schedules

### Single Schedule (Simple)
```bash
# Note: For dual-schedule setup, see compose.backup-s3.yaml
# Single schedule is not commonly used in production
BACKUP_CRON_SCHEDULE=@every 1h    # Every hour
```

### Dual Schedule (Recommended for Your Use Case)

**Frequent DB backups + Occasional full backups:**

Edit `compose.backup-s3.yaml` to add two jobs:

```yaml
scheduler:
  labels:
    # Job 1: Hourly database-only backup (official @every syntax)
    ofelia.job-exec.backup-db.schedule: "@every 1h"
    ofelia.job-exec.backup-db.command: "bash -c 'export BACKUP_WITH_FILES=0 && /bin/bash /usr/local/bin/backup-to-s3.sh'"
    ofelia.job-exec.backup-db.user: "frappe"
    ofelia.job-exec.backup-db.no-overlap: "true"
    
    # Job 2: Daily full backup at 3 AM (standard cron)
    ofelia.job-exec.backup-full.schedule: "0 3 * * *"
    ofelia.job-exec.backup-full.command: "bash -c 'export BACKUP_WITH_FILES=1 && /bin/bash /usr/local/bin/backup-to-s3.sh'"
    ofelia.job-exec.backup-full.user: "frappe"
    ofelia.job-exec.backup-full.no-overlap: "true"
```

### Common Schedules
```bash
# Interval syntax (recommended for sub-daily)
@every 1h        # Every hour
@every 2h        # Every 2 hours
@every 30m       # Every 30 minutes

# Standard cron format (for specific times)
0 3 * * *        # Daily at 3 AM
0 3 * * 0        # Weekly on Sunday at 3 AM
0 0,12 * * *     # Twice daily (midnight and noon)
```

**References:**
- [Go cron intervals](https://pkg.go.dev/github.com/robfig/cron/v3#hdr-Intervals)
- [Cron format generator](https://crontab.guru/)

---

## 🗂️ S3 Structure & Environment Segregation

```
s3://erp-is-backup/
├── production/              ← ENV_PREFIX=production
│   └── erp.example.com/
│       └── 2025-11-20/      ← Single date folder
│           ├── 20251120_120000-database.sql.gz
│           ├── 20251120_120000-files.tar
│           └── 20251120_120000-site_config_backup.json
├── staging/                 ← ENV_PREFIX=staging
├── development/             ← ENV_PREFIX=development
└── local/                   ← ENV_PREFIX=local
```

**Set environment:**
```bash
ENV_PREFIX=production    # For production
ENV_PREFIX=staging       # For staging
ENV_PREFIX=local         # For local dev
```

---

## ⚙️ Configuration

**File:** `backup/backup.env`

### Essential Settings
```bash
# Credentials (MUST CHANGE)
S3_ACCESS_KEY_ID=your_key_here
S3_SECRET_ACCESS_KEY=your_secret_here

# S3 Config
S3_ENDPOINT_URL=https://blr1.digitaloceanspaces.com
S3_BUCKET_NAME=erp-is-backup
S3_REGION=blr1

# Environment
ENV_PREFIX=production

# Schedule (configured in compose.backup-s3.yaml)
# See "Dual Schedule" section for details

# What to backup
BACKUP_WITH_FILES=1              # 1=DB+files, 0=DB only
BACKUP_COMPRESS=1                # Compress SQL (recommended)

# Sites
BACKUP_SITES=erp.localhost

# Retention
BACKUP_RETENTION_DAYS=7          # Local retention
S3_BACKUP_RETENTION_DAYS=30      # S3 retention
```

---

## 🛠️ Management Commands

```bash
cd production/backup

# Service control
./manage-backups.sh start        # Start backup services
./manage-backups.sh stop         # Stop backup services
./manage-backups.sh restart      # Restart services

# Operations
./manage-backups.sh test         # Run backup now
./manage-backups.sh status       # Check status
./manage-backups.sh logs         # View logs
./manage-backups.sh list-s3      # List S3 backups
./manage-backups.sh validate     # Validate config

# Interactive setup
./manage-backups.sh setup        # Configuration wizard
```

---

## 📋 Example Configurations

### Dual Schedule: Hourly DB + Daily Full (Recommended)
```bash
# backup.env
ENV_PREFIX=production
BACKUP_SITES=erp.localhost
BACKUP_WITH_FILES=0              # Default (overridden by cron)
BACKUP_COMPRESS=1
BACKUP_RETENTION_DAYS=1          # Keep local 1 day
S3_BACKUP_RETENTION_DAYS=5       # Keep S3 5 days

# Schedules are in compose.backup-s3.yaml:
# - Hourly: BACKUP_WITH_FILES=0 (DB only)
# - Daily 3AM: BACKUP_WITH_FILES=1 (Full)
```

### High-Traffic Production
```bash
# Note: Schedule is set in compose.backup-s3.yaml, not in backup.env
ENV_PREFIX=production
BACKUP_WITH_FILES=1
S3_BACKUP_RETENTION_DAYS=90

# In compose.backup-s3.yaml:
# ofelia.job-exec.backup-db.schedule: "@every 2h"
```

### Staging/Dev
```bash
ENV_PREFIX=staging
BACKUP_WITH_FILES=0              # DB only
S3_BACKUP_RETENTION_DAYS=14

# In compose.backup-s3.yaml:
# ofelia.job-exec.backup-daily.schedule: "0 3 * * *"
```

---

## 🔄 Restore Process

### Download from S3
```bash
# List backups
aws s3 ls s3://erp-is-backup/production/erp.localhost/ --recursive \
    --endpoint-url=https://blr1.digitaloceanspaces.com

# Download specific backup
aws s3 cp s3://erp-is-backup/production/erp.localhost/2025-11-20/backup.sql.gz . \
    --endpoint-url=https://blr1.digitaloceanspaces.com
```

### Restore Database
```bash
# Copy to container
docker cp backup.sql.gz erpnext-production-backend:/tmp/

# Restore
docker compose -p erpnext-production exec backend \
    bench --site erp.localhost --force restore /tmp/backup.sql.gz
```

### Restore with Files
```bash
docker compose -p erpnext-production exec backend \
    bench --site erp.localhost --force restore \
    --with-public-files /tmp/files.tar \
    --with-private-files /tmp/private-files.tar \
    /tmp/backup.sql.gz
```

---

## 🔍 Monitoring

### Check Status
```bash
./manage-backups.sh status

# Or manually
docker ps | grep backup
docker compose -p erpnext-production logs -f backup-cron
```

### View Recent Backups
```bash
# Local backups
docker compose -p erpnext-production exec scheduler \
    ls -lht /home/frappe/frappe-bench/sites/*/private/backups/ | head -10

# S3 backups
./manage-backups.sh list-s3
```

---

## 📁 File Structure

```
production/
├── backup/                          ← All backup configs here
│   ├── backup.env                   ← Main configuration
│   ├── compose.backup-s3.yaml       ← Docker compose override
│   ├── backup-to-s3.sh             ← S3 backup script
│   ├── backup-site.sh              ← Local backup script
│   └── manage-backups.sh           ← Management helper
│
├── backups/                         ← Local backup storage
│   └── {timestamp}-{site}-*.{sql.gz|tar|json}
│
├── scripts/                         ← Other scripts
└── docs/                           ← This documentation
```

---

## 🚨 Troubleshooting

### Services Not Running
```bash
./manage-backups.sh restart
docker ps -a | grep backup
```

### S3 Upload Fails
- Check credentials in `backup.env`
- Verify bucket exists in Digital Ocean
- Test connection: `./manage-backups.sh validate`

### No Backups Created
```bash
# Verify site name
docker compose -p erpnext-production exec backend bench list-apps

# Check site in backup.env matches actual site
grep BACKUP_SITES backup.env

# Run with debug
docker compose -p erpnext-production exec scheduler bash -c "
    export BACKUP_DEBUG=1
    /bin/bash /usr/local/bin/backup-to-s3.sh
"
```

### AWS CLI Missing
Script auto-installs, but if issues:
```bash
docker compose -p erpnext-production exec scheduler bash -c "
    pip3 install --user awscli --upgrade
    export PATH=\"\$HOME/.local/bin:\$PATH\"
    aws --version
"
```

---

## 🔐 Security

```bash
# Protect credentials
chmod 600 backup/backup.env

# Gitignore
echo "production/backup/backup.env" >> .gitignore

# Use Digital Ocean IAM
# Create dedicated API keys with bucket-only access
```

---

## 💡 Best Practices

1. **Test Restores** - Regularly test restore in staging
2. **Monitor Sizes** - Check backup sizes, adjust file inclusion
3. **Environment Prefix** - Always use for clarity
4. **Start Conservative** - Begin with less frequent, increase as needed
5. **Document Changes** - Note when you modify backup config

---

## Storage Estimates

| Frequency | With Files | DB Only | Monthly (30d) |
|-----------|-----------|---------|---------------|
| Hourly | ~200MB × 24 = 4.8GB/day | ~50MB × 24 = 1.2GB/day | 144GB / 36GB |
| Every 6h | ~200MB × 4 = 800MB/day | ~50MB × 4 = 200MB/day | 24GB / 6GB |
| Daily | ~200MB × 1 = 200MB/day | ~50MB × 1 = 50MB/day | 6GB / 1.5GB |

**Your Config (Hourly DB + Daily Full):**
- Hourly DB: ~50MB × 24 = 1.2GB/day
- Daily Full: ~200MB × 1 = 200MB/day
- **Total: ~1.4GB/day = ~42GB/month** (30 day retention)

---

## Support & Resources

- [Digital Ocean Spaces Docs](https://docs.digitalocean.com/products/spaces/)
- [Ofelia Cron Scheduler](https://github.com/mcuadros/ofelia)
- [ERPNext Backup Docs](https://frappeframework.com/docs/user/en/bench/reference/backup)
- [Cron Schedule Generator](https://crontab.guru/)

**Management Script:**
```bash
./manage-backups.sh help
```
