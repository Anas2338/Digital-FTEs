#!/bin/bash
# Install Odoo Backup Cron Job
# Configures daily automated backups for Odoo
#
# Usage: sudo bash install-odoo-backup-cron.sh
# Based on spec.md FR-027 and tasks.md T053

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "=== Installing Odoo Backup Cron Job ==="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/odoo-backup.sh"

# Verify backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "Error: Backup script not found at $BACKUP_SCRIPT"
    exit 1
fi

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"

# Copy to /etc/cron.daily/ (files in this directory run daily at ~6:25 AM)
echo "Installing backup script to /etc/cron.daily/..."
cp "$BACKUP_SCRIPT" /etc/cron.daily/odoo-backup

# Ensure it's executable
chmod +x /etc/cron.daily/odoo-backup

# Verify installation
if [ -f /etc/cron.daily/odoo-backup ]; then
    echo "✓ Backup cron job installed successfully"
    echo ""
    echo "Backup schedule: Daily at ~6:25 AM (via cron.daily)"
    echo "Backup location: /backups/odoo/"
    echo "Retention: 30 days"
    echo ""
    echo "To test the backup manually, run:"
    echo "  sudo /etc/cron.daily/odoo-backup"
    echo ""
    echo "To view backup logs, check:"
    echo "  sudo journalctl -u cron | grep odoo-backup"
else
    echo "✗ Installation failed"
    exit 1
fi

exit 0
