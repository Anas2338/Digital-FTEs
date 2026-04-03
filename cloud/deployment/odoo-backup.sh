#!/bin/bash
# Odoo Backup Script
# Creates daily backups of Odoo database and filestore
#
# Usage: sudo bash odoo-backup.sh
# Install as cron job: sudo cp odoo-backup.sh /etc/cron.daily/
# Based on quickstart.md Phase 3

set -e

BACKUP_DIR="/backups/odoo"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d)

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting Odoo backup..."

# Step 1: Backup PostgreSQL database
echo "Backing up database..."
sudo -u postgres pg_dump odoo | gzip > "$BACKUP_DIR/odoo-db-$DATE.sql.gz"

if [ $? -eq 0 ]; then
    echo "Database backup successful: odoo-db-$DATE.sql.gz"
else
    echo "ERROR: Database backup failed"
    exit 1
fi

# Step 2: Backup filestore
echo "Backing up filestore..."
if [ -d "/var/lib/odoo/filestore" ]; then
    tar -czf "$BACKUP_DIR/odoo-filestore-$DATE.tar.gz" -C /var/lib/odoo filestore

    if [ $? -eq 0 ]; then
        echo "Filestore backup successful: odoo-filestore-$DATE.tar.gz"
    else
        echo "ERROR: Filestore backup failed"
        exit 1
    fi
else
    echo "WARNING: Filestore directory not found, skipping"
fi

# Step 3: Backup configuration
echo "Backing up configuration..."
if [ -f "/etc/odoo/odoo.conf" ]; then
    cp /etc/odoo/odoo.conf "$BACKUP_DIR/odoo-conf-$DATE.conf"
    echo "Configuration backup successful: odoo-conf-$DATE.conf"
fi

# Step 4: Clean up old backups (retain last 30 days)
echo "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "odoo-*.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "odoo-*.conf" -mtime +$RETENTION_DAYS -delete

# Step 5: Calculate backup sizes
DB_SIZE=$(du -h "$BACKUP_DIR/odoo-db-$DATE.sql.gz" | cut -f1)
if [ -f "$BACKUP_DIR/odoo-filestore-$DATE.tar.gz" ]; then
    FS_SIZE=$(du -h "$BACKUP_DIR/odoo-filestore-$DATE.tar.gz" | cut -f1)
else
    FS_SIZE="N/A"
fi

echo ""
echo "=== Backup Complete ==="
echo "Date: $(date)"
echo "Database size: $DB_SIZE"
echo "Filestore size: $FS_SIZE"
echo "Backup location: $BACKUP_DIR"
echo ""

# Optional: Send backup notification
# curl -X POST https://your-monitoring-service.com/backup-complete \
#   -d "service=odoo&date=$DATE&status=success"

exit 0
