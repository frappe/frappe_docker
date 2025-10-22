# Hybrid Deployment Guide: Apps in Image + Persistent Volumes

This configuration implements the best of both worlds:
- **Apps baked into Docker image** for consistency and fast deployments
- **Site data in persistent volumes** for data safety and persistence

## Architecture Overview

### What's in the Image (Built once, reusable):
- ✅ Frappe and ERPNext applications
- ✅ All Python dependencies  
- ✅ Custom apps (if configured)
- ✅ Basic directory structure

### What's in Persistent Volumes:
- ✅ Site configurations (`sites/[site-name]/site_config.json`)
- ✅ Uploaded files (`sites/[site-name]/public/files/`)
- ✅ Private files (`sites/[site-name]/private/files/`)
- ✅ Site-specific customizations
- ✅ Database backups
- ✅ Application logs

## Deployment Steps

### 1. Set Required Environment Secrets in Zerops

```bash
# In Zerops Dashboard > Project > Environment Variables
db_password=YourSecureDbPassword123
admin_password=YourAdminPassword123
site_name=your-domain.com
```

### 2. Deploy the Configuration

1. Import the `zerops.yml` file to Zerops
2. Zerops will build all services using `Dockerfile.zerops`
3. Each service will run the initialization script on startup
4. Site will be automatically created if it doesn't exist

### 3. Automatic Initialization Process

On first deployment, each container will:

1. **Build Phase** (runs once during image creation):
   - Install Frappe/ERPNext apps into image
   - Copy initialization scripts
   - Set proper permissions

2. **Runtime Phase** (runs on every container start):
   - **Backend service**: Full site initialization (creates site, installs ERPNext)
   - **Other services**: Light initialization (just checks if site exists)
   - Configure database and Redis connections
   - Wait for database to be ready (backend only)
   - Set proper permissions and configurations

## Benefits of This Approach

### ✅ **Container Restart Resilience**
- Site data survives container restarts/crashes
- No manual intervention required
- Fast recovery times

### ✅ **Consistent App Deployments**
- Apps are identical across all containers
- No version drift between services
- Easy to update apps (rebuild image)

### ✅ **Zero-Downtime Updates**
- App updates: rebuild image, rolling update
- Site data preserved during updates
- Database migrations handled automatically

### ✅ **Backup & Recovery**
- Simple volume snapshots for site data
- Database backups work seamlessly
- Easy disaster recovery

### ✅ **Scalability**
- New containers start with same apps
- Shared persistent volume for site data
- Auto-scaling works out of the box

## File Structure

```
/home/frappe/frappe-bench/
├── apps/                    # Apps (in image)
│   ├── frappe/             # Frappe framework
│   └── erpnext/            # ERPNext app
├── sites/                  # Site data (persistent volume)
│   ├── apps.txt            # List of installed apps
│   ├── common_site_config.json
│   └── your-domain.com/    # Your site directory
│       ├── site_config.json
│       ├── public/files/   # Uploaded files
│       └── private/files/  # Private files
└── logs/                   # Application logs (persistent volume)
```

## Common Operations

### Adding New Custom Apps

1. **Update `Dockerfile.zerops`**:
   ```dockerfile
   RUN bench get-app --branch main custom_app https://github.com/user/custom_app.git
   ```

2. **Redeploy services** (Zerops will rebuild image)

3. **Install app on site** (automatic or manual):
   ```bash
   bench --site your-domain.com install-app custom_app
   ```

### Updating Frappe/ERPNext Version

1. **Update version in `Dockerfile.zerops`**:
   ```dockerfile
   FROM frappe/erpnext:v16.0.0
   ```

2. **Update `zerops.yml` environment**:
   ```yaml
   ERPNEXT_VERSION: v16.0.0
   ```

3. **Redeploy** - migrations run automatically

### Manual Site Operations

Access any service terminal in Zerops dashboard:

```bash
# Navigate to bench directory
cd /home/frappe/frappe-bench

# Run migrations
bench --site your-domain.com migrate

# Create new site
bench new-site newsite.com --install-app erpnext

# Install custom app
bench --site your-domain.com install-app custom_app

# Backup site
bench --site your-domain.com backup --with-files

# Console access
bench --site your-domain.com console
```

## Troubleshooting

### Site Not Created Automatically
- Check environment variables are set correctly
- Check database connectivity
- Review container logs in Zerops dashboard
- Manually run: `/home/frappe/init-site.sh`

### Permission Issues
- Persistent volumes should be owned by `frappe:frappe`
- Run: `chown -R frappe:frappe /home/frappe/frappe-bench/sites`

### App Installation Issues
- Verify apps are in the image: `ls /home/frappe/frappe-bench/apps`
- Check apps.txt: `cat /home/frappe/frappe-bench/sites/apps.txt`
- Manually install: `bench --site [site] install-app [app]`

### Database Connection Issues
- Verify database service is running
- Check environment variables
- Test connection: `mysql -h$DB_HOST -P$DB_PORT -uroot -p$DB_PASSWORD`

## Monitoring

### Health Checks
- All services have health checks configured
- Monitor in Zerops dashboard
- Backend: `/api/method/ping`
- WebSocket: `/socket.io/`

### Logs
- Application logs in persistent volume: `/home/frappe/frappe-bench/logs`
- Container logs in Zerops dashboard
- Database logs in MariaDB service logs

### Performance
- Monitor resource usage in Zerops dashboard
- Auto-scaling configured based on CPU/memory
- Adjust container limits as needed

This hybrid approach gives you the reliability of persistent data with the consistency of containerized applications!