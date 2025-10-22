# Deploying Frappe/ERPNext on Zerops

This repository contains the Zerops configuration file (`zerops.yml`) to deploy Frappe/ERPNext on the Zerops platform.

## Architecture Overview

The deployment consists of the following services:

- **MariaDB** (`db`) - Database service (HA mode)
- **Redis Cache** (`redis-cache`) - Caching layer  
- **Redis Queue** (`redis-queue`) - Background job queue
- **Backend** (`backend`) - Main Frappe application server
- **Frontend** (`frontend`) - Nginx reverse proxy
- **WebSocket** (`websocket`) - Real-time communication server
- **Queue Workers** (`queue-short`, `queue-long`) - Background job processors
- **Scheduler** (`scheduler`) - Cron job scheduler

## Prerequisites

1. A Zerops account - [Sign up here](https://zerops.io)
2. Access to this GitHub repository
3. Basic knowledge of Frappe/ERPNext

## Deployment Steps

### 1. Import Project to Zerops

1. Log into your Zerops dashboard
2. Click "Import project" 
3. Select "Import from Git repository"
4. Enter the repository URL: `https://github.com/UhrinDavid/frappe_docker`
5. Select the `zerops.yml` file
6. Click "Import project"

### 2. Configure Environment Secrets

Before deployment, you need to set the following environment secrets in Zerops:

#### Required Secrets:
- `db_password` - Password for MariaDB database (choose a strong password)
- `site_name` - Your site domain name (e.g., `mycompany.example.com`)

#### Optional Secrets:
- `ERPNEXT_VERSION` - ERPNext version (default: v15.84.0)

To set secrets:
1. Go to your project in Zerops dashboard
2. Navigate to each service  
3. Go to "Environment variables" section
4. Add the required secrets

### 3. Deploy the Services

1. Zerops will automatically start building and deploying all services
2. Monitor the build progress in the Zerops dashboard
3. Wait for all services to reach "Running" status

### 4. Post-Deployment Setup

Once all services are running, you need to initialize your Frappe site:

1. Access the backend service terminal in Zerops dashboard
2. Create your first site:
   ```bash
   bench new-site your-site-name --db-root-password <db_password>
   ```

3. Install ERPNext:
   ```bash
   bench --site your-site-name install-app erpnext
   ```

4. Set the site as default:
   ```bash
   bench use your-site-name
   ```

5. Create an admin user:
   ```bash
   bench --site your-site-name add-user admin administrator --password <admin-password>
   ```

### 5. Access Your Application

Your Frappe/ERPNext instance will be available at the domain provided by Zerops for the `frontend` service.

## Configuration Details

### Resource Allocation

- **Backend**: 1-3 containers, autoscaling enabled
- **Frontend**: 1-2 containers  
- **WebSocket**: 1-2 containers
- **Queue Workers**: 1-3 containers (short), 1-2 containers (long)
- **Scheduler**: 1 container (fixed)
- **Databases**: HA mode for production reliability

### Health Checks

All services include health checks to ensure proper operation:
- Backend: `/api/method/ping`
- Frontend: `/api/method/ping` 
- WebSocket: `/socket.io/`

### Autoscaling

Backend and queue workers have autoscaling configured based on:
- CPU usage threshold: 70%
- Memory usage threshold: 80%

## Troubleshooting

### Common Issues

1. **Services not starting**: Check environment variables are set correctly
2. **Database connection errors**: Verify `db_password` secret is set
3. **Site access issues**: Ensure `site_name` matches your domain

### Logs

Access service logs through the Zerops dashboard:
1. Go to your project
2. Select the service
3. Navigate to "Runtime logs"

### Manual Commands

To run manual bench commands:
1. Access the backend service terminal
2. Navigate to `/home/frappe/frappe-bench`
3. Run your bench commands

## Customization

### Custom Apps

To add custom Frappe apps:
1. Modify the Dockerfile to include your apps
2. Update the `zerops.yml` build configuration
3. Redeploy the services

### Environment Variables

Additional environment variables can be added in the `zerops.yml` file under the `envSecrets` section for each service.

### Scaling

Adjust the `minContainers` and `maxContainers` values in `zerops.yml` based on your traffic requirements.

## Support

For issues specific to:
- Zerops platform: [Zerops Documentation](https://docs.zerops.io)
- Frappe/ERPNext: [Frappe Documentation](https://docs.frappe.io)
- This deployment setup: Create an issue in this repository

## License

This configuration is provided under the same license as the original frappe_docker repository.