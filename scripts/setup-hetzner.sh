#!/bin/bash
# Initial setup script for Hetzner server

set -e

echo "🚀 Starting Academy LMS Hetzner setup..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run this script with sudo or as root"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Add frappe user to docker group
    usermod -aG docker frappe
else
    echo "✅ Docker is already installed"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "✅ Docker Compose is already installed"
fi

# Create deployment directory
echo "📁 Creating deployment directory..."
mkdir -p /opt/frappe-deployment
chown frappe:frappe /opt/frappe-deployment

# Create required networks
echo "🌐 Creating Docker networks..."
docker network create langchain-network 2>/dev/null || echo "Network langchain-network already exists"

# Setup firewall rules
echo "🔥 Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8001/tcp  # LangChain service (if needed for debugging)
ufw --force enable

# Create backup directory
echo "💾 Creating backup directory..."
mkdir -p /opt/frappe-deployment/backups
chown frappe:frappe /opt/frappe-deployment/backups

# Setup cron for automated backups (optional)
echo "⏰ Setting up automated backup cron job..."
cat > /etc/cron.d/frappe-backup << EOF
# Backup Frappe sites daily at 2 AM
0 2 * * * frappe cd /opt/frappe-deployment && docker compose exec -T backend bench --site all backup --with-files >> /opt/frappe-deployment/backups/backup.log 2>&1
# Clean old backups (keep last 7 days)
0 3 * * * frappe find /opt/frappe-deployment/backups -name "*.sql.gz" -mtime +7 -delete
EOF

# Install monitoring tools (optional)
echo "📊 Installing monitoring tools..."
apt-get install -y htop iotop ncdu

# Create systemd service for auto-start
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/academy-lms.service << EOF
[Unit]
Description=Academy LMS Docker Compose Application
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=frappe
Group=frappe
WorkingDirectory=/opt/frappe-deployment
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable academy-lms.service

echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Switch to frappe user: su - frappe"
echo "2. Go to deployment directory: cd /opt/frappe-deployment"
echo "3. Copy your deployment files there"
echo "4. Create .env file from .env.example and configure it"
echo "5. Start services: docker compose up -d"
echo ""
echo "🔐 Security reminder:"
echo "- Change all default passwords in .env file"
echo "- Configure SSL certificates for production"
echo "- Review firewall rules for your specific needs"
