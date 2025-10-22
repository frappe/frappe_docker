# Zerops Deployment Guide: Managed Services + Docker Compose

This configuration leverages Zerops' managed services for databases while using Docker Compose for application containers, providing the best of both worlds:
- **Managed MariaDB and Redis** for reliability, backups, and performance
- **Docker Compose applications** for flexibility and familiar workflows
- **Automated site installation** with custom apps included

## Architecture Overview

### Zerops Managed Services:
- ✅ **MariaDB 11** - Database service with automatic backups and monitoring
- ✅ **Valkey 7.2 (Redis)** - Cache service for high-performance caching
- ✅ **Valkey 7.2 (Redis)** - Queue service for background job processing

### Docker Compose Application Services:
- ✅ **Backend** - Main Frappe/ERPNext application server
- ✅ **Frontend** - Nginx reverse proxy for web serving
- ✅ **WebSocket** - Real-time communication service
- ✅ **Queue Workers** - Background job processing (short & long tasks)
- ✅ **Scheduler** - Cron job management

### Automated Site Setup:
- ✅ Site creation and configuration
- ✅ ERPNext application installation
- ✅ Custom XML Importer app installation
- ✅ Database migrations and setup
- ✅ Application logs

## Deployment Steps

### 1. Create Zerops Services

Create these services in your Zerops project:

```yaml
# Database service
- Service Name: db
- Type: MariaDB 11
- Mode: Default (or HA for production)

# Redis Cache service  
- Service Name: redis-cache
- Type: Valkey 7.2
- Mode: NON_HA (or HA for production)

# Redis Queue service
- Service Name: redis-queue  
- Type: Valkey 7.2
- Mode: NON_HA (or HA for production)
```

### 2. Set Environment Secrets

In Zerops Dashboard > Project > Environment Variables:

```bash
dbPassword=YourSecureDbPassword123
adminPassword=YourAdminPassword123  
siteName=your-domain.com
```

### 3. Deploy the Application

1. Connect your GitHub repository to Zerops
2. Set branch to `zerops`
3. Zerops will automatically find and deploy using `zerops.yml`
4. The deployment will:
   - Create managed database and Redis services
   - Pull and start Docker Compose services
   - Run site installation script
   - Configure all service connections

### 4. Automatic Site Installation

During deployment, the installation script will:

1. **Service Verification**:
   - Wait for database connection to be ready
   - Verify Redis cache and queue services are available
   - Pull required Docker images

2. **Site Setup**:
   - Check if site already exists
   - Create new site if needed (with database and admin user)
   - Install ERPNext application
   - Install custom XML Importer app from GitHub
   - Run database migrations

2. **Runtime Phase** (runs on every container start):
3. **Service Startup**:
   - Start all Docker Compose services
   - Services connect to managed databases using service names
   - Site becomes available at the app service URL

## Benefits of This Architecture

### ✅ **Managed Database Reliability**
- Automatic backups and point-in-time recovery
- Built-in monitoring and alerting
- High availability options
- No database container overhead

### ✅ **Docker Compose Flexibility**
- Familiar development workflow
- Easy service management and scaling
- Shared volumes for site data
- Service dependencies handled automatically

### ✅ **Automated Setup**
- Zero-touch deployment
- Custom apps automatically installed
- Site creation and configuration handled
- No manual intervention required

### ✅ **Service Discovery**
- Internal service communication via names
- No hardcoded IPs or complex networking
- Zerops handles internal DNS resolution

### ✅ **Scalability & Performance**
- Database services can be scaled independently  
- Application services can be horizontally scaled
- Redis services optimized for their use case
- No database performance impact from containerization
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

## Access Your ERPNext Instance

After successful deployment:

1. **Find your app service URL** in Zerops Dashboard > Services > app
2. **Access ERPNext** at `https://your-app-service-url` 
3. **Login credentials**:
   - Username: `Administrator`
   - Password: `[value you set for adminPassword]`

## Common Operations

### Adding New Custom Apps

1. **Update the installation script** `scripts/install-site.sh`:
   ```bash
   # Add your custom app
   bench get-app https://github.com/user/custom_app.git
   bench --site "$FRAPPE_SITE_NAME_HEADER" install-app custom_app
   ```

2. **Redeploy the application** - Zerops will run the updated script

### Updating Frappe/ERPNext Version

1. **Update version in `zerops.yml`**:
   ```yaml
   CUSTOM_TAG: v16.0.0
   ERPNEXT_VERSION: v16.0.0
   ```

2. **Redeploy** - migrations run automatically during site setup

### Manual Site Operations

Access the app service terminal in Zerops dashboard:

```bash
# Navigate to bench directory  
cd /home/frappe/frappe-bench

# Run migrations
bench --site your-domain.com migrate

# Install additional apps
bench --site your-domain.com install-app custom_app

# Backup site
bench --site your-domain.com backup --with-files

# Console access
bench --site your-domain.com console
```

## Troubleshooting

### Site Installation Issues
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