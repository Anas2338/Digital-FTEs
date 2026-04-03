#!/bin/bash
# Odoo Installation Script for Cloud VM
# Installs PostgreSQL and Odoo 17.0 Community Edition
#
# Usage: sudo bash setup_odoo.sh
# Based on quickstart.md Phase 3

set -e

echo "=== Installing Odoo Community Edition 17.0 ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "Step 1: Installing PostgreSQL..."
apt install -y postgresql postgresql-contrib

echo "Step 2: Creating Odoo database user..."
sudo -u postgres createuser -s odoo 2>/dev/null || echo "User 'odoo' already exists"

# Prompt for database password
read -sp "Enter password for Odoo database user: " DB_PASSWORD
echo

sudo -u postgres psql -c "ALTER USER odoo WITH PASSWORD '$DB_PASSWORD';"

echo "Step 3: Creating Odoo database..."
sudo -u postgres createdb -O odoo odoo 2>/dev/null || echo "Database 'odoo' already exists"

echo "Step 4: Installing Odoo dependencies..."
apt install -y python3-pip python3-dev libxml2-dev libxslt1-dev \
    libldap2-dev libsasl2-dev libjpeg-dev libpq-dev \
    python3-pypdf2 python3-dateutil python3-psycopg2 \
    python3-ldap python3-werkzeug python3-requests \
    python3-pil python3-passlib python3-decorator

echo "Step 5: Downloading Odoo 17.0..."
cd /tmp
wget -q https://nightly.odoo.com/17.0/nightly/deb/odoo_17.0.latest_all.deb

echo "Step 6: Installing Odoo package..."
dpkg -i odoo_17.0.latest_all.deb || apt-get install -f -y

echo "Step 7: Configuring Odoo..."
# Prompt for admin password
read -sp "Enter Odoo admin password: " ADMIN_PASSWORD
echo

cat > /etc/odoo/odoo.conf << EOF
[options]
admin_passwd = $ADMIN_PASSWORD
db_host = localhost
db_port = 5432
db_user = odoo
db_password = $DB_PASSWORD
addons_path = /usr/lib/python3/dist-packages/odoo/addons
workers = 2
max_cron_threads = 1
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200
log_level = info
logfile = /var/log/odoo/odoo-server.log
EOF

echo "Step 8: Setting up log directory..."
mkdir -p /var/log/odoo
chown odoo:odoo /var/log/odoo

echo "Step 9: Enabling and starting Odoo service..."
systemctl enable odoo
systemctl start odoo

echo "Step 10: Checking Odoo status..."
sleep 5
systemctl status odoo --no-pager

echo ""
echo "=== Odoo Installation Complete ==="
echo ""
echo "Odoo is now running on http://localhost:8069"
echo ""
echo "Next steps:"
echo "  1. Configure nginx reverse proxy (run configure_ssl.sh)"
echo "  2. Setup automated backups (run odoo-backup.sh)"
echo "  3. Access Odoo at http://your-domain.com after SSL setup"
echo ""
echo "Database credentials stored in /etc/odoo/odoo.conf"
echo "Logs available at /var/log/odoo/odoo-server.log"
echo ""
