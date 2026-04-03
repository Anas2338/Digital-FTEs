#!/bin/bash
# Cloud VM Setup Script for Platinum Tier
# Initializes Ubuntu 22.04 VM for cloud agent deployment
#
# Usage: sudo bash setup_cloud_vm.sh
# Based on quickstart.md Phase 1

set -e

echo "=== Cloud VM Setup for Platinum Tier ==="
echo "This script will:"
echo "  - Update system packages"
echo "  - Create cloudagent user"
echo "  - Configure firewall"
echo "  - Create directory structure"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "Step 1: Updating system packages..."
apt update && apt upgrade -y

echo "Step 2: Installing essential tools..."
apt install -y git curl wget build-essential python3.11 python3.11-venv \
    python3-pip nginx certbot python3-certbot-nginx postgresql \
    postgresql-contrib monit ufw

echo "Step 3: Installing uv (Python package manager)..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "Step 4: Creating cloudagent user..."
if ! id -u cloudagent &> /dev/null; then
    useradd -r -m -s /bin/bash cloudagent
    echo "Created cloudagent user"
else
    echo "cloudagent user already exists"
fi

echo "Step 5: Creating directory structure..."
mkdir -p /opt/cloud-agent/{cloud,sync,coordination,config,data,logs}
chown -R cloudagent:cloudagent /opt/cloud-agent

echo "Step 6: Configuring firewall (UFW)..."
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8069/tcp  # Odoo
ufw status

echo "Step 7: Setting up log rotation..."
cat > /etc/logrotate.d/cloud-agent << 'EOF'
/opt/cloud-agent/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 cloudagent cloudagent
    sharedscripts
    postrotate
        systemctl reload cloud-agent > /dev/null 2>&1 || true
    endscript
}
EOF

echo ""
echo "=== Cloud VM Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Run install_dependencies.sh to install Python dependencies"
echo "  2. Copy agent code to /opt/cloud-agent/"
echo "  3. Configure /opt/cloud-agent/config/agent-config.json"
echo "  4. Create /opt/cloud-agent/.env.cloud with read-only credentials"
echo "  5. Run configure_systemd.sh to enable cloud-agent service"
echo ""
