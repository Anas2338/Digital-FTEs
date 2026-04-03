#!/bin/bash
# System Validation Script for Platinum Tier
# Validates all components are working correctly after deployment
#
# Usage: bash validate_system.sh
# Based on tasks.md T076 and T080

set -e

echo "=========================================="
echo "Digital FTE System Validation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARNINGS++))
}

# Check if running on cloud VM
if [ ! -d "/opt/digital-fte" ]; then
    echo "Error: This script must be run on the cloud VM"
    exit 1
fi

echo "Starting validation..."
echo ""

# ============================================
# 1. Service Status Checks
# ============================================
echo "1. Checking Service Status..."

# Cloud Agent
if systemctl is-active --quiet cloud-agent.service; then
    pass "Cloud agent service is running"
else
    fail "Cloud agent service is not running"
fi

# Odoo
if systemctl is-active --quiet odoo.service; then
    pass "Odoo service is running"
else
    fail "Odoo service is not running"
fi

# Vault Sync Timer
if systemctl is-active --quiet vault-sync.timer; then
    pass "Vault sync timer is active"
else
    fail "Vault sync timer is not active"
fi

# Monit
if systemctl is-active --quiet monit; then
    pass "Monit service is running"
else
    fail "Monit service is not running"
fi

echo ""

# ============================================
# 2. Vault Synchronization
# ============================================
echo "2. Checking Vault Synchronization..."

cd /opt/digital-fte/obsidian-vault

# Check git status
if git status &>/dev/null; then
    pass "Vault is a valid git repository"
else
    fail "Vault is not a valid git repository"
fi

# Check for uncommitted changes
if [ -z "$(git status --porcelain)" ]; then
    pass "Vault has no uncommitted changes"
else
    warn "Vault has uncommitted changes"
fi

# Check sync status file
if [ -f ".sync-status/cloud.json" ]; then
    pass "Sync status file exists"

    # Check sync lag
    LAST_SYNC=$(jq -r '.last_sync_at' .sync-status/cloud.json 2>/dev/null || echo "")
    if [ -n "$LAST_SYNC" ]; then
        SYNC_LAG=$(python3 -c "from datetime import datetime; import sys; last=datetime.fromisoformat('$LAST_SYNC'); now=datetime.now(); print(int((now-last).total_seconds()))" 2>/dev/null || echo "999")

        if [ "$SYNC_LAG" -lt 300 ]; then
            pass "Vault sync lag is acceptable ($SYNC_LAG seconds)"
        else
            fail "Vault sync lag is too high ($SYNC_LAG seconds)"
        fi
    fi
else
    warn "Sync status file not found"
fi

# Check coordination directories exist
for dir in "In_Progress/cloud" "In_Progress/local" "Pending_Approval/email" "Pending_Approval/social" "Pending_Approval/accounting" "Updates"; do
    if [ -d "$dir" ]; then
        pass "Directory exists: $dir"
    else
        fail "Directory missing: $dir"
    fi
done

echo ""

# ============================================
# 3. Odoo Health Check
# ============================================
echo "3. Checking Odoo Health..."

# Check Odoo health endpoint
ODOO_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8069/web/health 2>/dev/null || echo "000")

if [ "$ODOO_HEALTH" = "200" ]; then
    pass "Odoo health endpoint responding (HTTP 200)"
else
    fail "Odoo health endpoint not responding (HTTP $ODOO_HEALTH)"
fi

# Check Odoo HTTPS (if domain configured)
if [ -f "/etc/nginx/sites-enabled/odoo" ]; then
    DOMAIN=$(grep server_name /etc/nginx/sites-enabled/odoo | head -1 | awk '{print $2}' | tr -d ';')
    if [ -n "$DOMAIN" ]; then
        HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/web/health" 2>/dev/null || echo "000")
        if [ "$HTTPS_STATUS" = "200" ]; then
            pass "Odoo HTTPS accessible at $DOMAIN"
        else
            fail "Odoo HTTPS not accessible at $DOMAIN (HTTP $HTTPS_STATUS)"
        fi
    fi
fi

# Check PostgreSQL
if systemctl is-active --quiet postgresql; then
    pass "PostgreSQL service is running"
else
    fail "PostgreSQL service is not running"
fi

echo ""

# ============================================
# 4. Health Monitoring
# ============================================
echo "4. Checking Health Monitoring..."

# Check Monit status
MONIT_STATUS=$(monit status 2>/dev/null | grep -c "status.*Running" || echo "0")
if [ "$MONIT_STATUS" -gt 0 ]; then
    pass "Monit is monitoring $MONIT_STATUS services"
else
    warn "Monit is not monitoring any services"
fi

# Check health check database
if [ -f "/opt/digital-fte/cloud/health/health_checks.db" ]; then
    pass "Health check database exists"

    # Check if database has records
    RECORD_COUNT=$(sqlite3 /opt/digital-fte/cloud/health/health_checks.db "SELECT COUNT(*) FROM health_checks" 2>/dev/null || echo "0")
    if [ "$RECORD_COUNT" -gt 0 ]; then
        pass "Health check database has $RECORD_COUNT records"
    else
        warn "Health check database is empty"
    fi
else
    warn "Health check database not found"
fi

# Check alert script
if [ -x "/opt/digital-fte/alert.sh" ]; then
    pass "Alert script is executable"
else
    warn "Alert script not found or not executable"
fi

echo ""

# ============================================
# 5. Cloud Agent Logs
# ============================================
echo "5. Checking Cloud Agent Logs..."

# Check for recent log entries
RECENT_LOGS=$(journalctl -u cloud-agent.service --since "5 minutes ago" 2>/dev/null | wc -l)
if [ "$RECENT_LOGS" -gt 0 ]; then
    pass "Cloud agent has recent log entries ($RECENT_LOGS lines)"
else
    warn "Cloud agent has no recent log entries"
fi

# Check for errors in last 100 lines
ERROR_COUNT=$(journalctl -u cloud-agent.service -n 100 2>/dev/null | grep -ci "error" || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    pass "No errors in recent cloud agent logs"
else
    warn "Found $ERROR_COUNT errors in recent cloud agent logs"
fi

# Check for watcher cycles
WATCHER_CYCLES=$(journalctl -u cloud-agent.service --since "30 minutes ago" 2>/dev/null | grep -c "Starting watcher cycle" || echo "0")
if [ "$WATCHER_CYCLES" -gt 0 ]; then
    pass "Cloud agent watcher cycles running ($WATCHER_CYCLES in last 30 min)"
else
    fail "No watcher cycles detected in last 30 minutes"
fi

echo ""

# ============================================
# 6. Backups
# ============================================
echo "6. Checking Backups..."

# Check backup directory
if [ -d "/backups/odoo" ]; then
    pass "Backup directory exists"

    # Check for recent backups
    BACKUP_COUNT=$(find /backups/odoo -name "*.sql.gz" -mtime -2 | wc -l)
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        pass "Found $BACKUP_COUNT recent backups (last 2 days)"
    else
        warn "No recent backups found"
    fi
else
    fail "Backup directory not found"
fi

# Check backup cron job
if [ -f "/etc/cron.daily/odoo-backup" ]; then
    pass "Backup cron job installed"
else
    warn "Backup cron job not found"
fi

echo ""

# ============================================
# 7. Resource Usage
# ============================================
echo "7. Checking Resource Usage..."

# CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE < 80" | bc -l) )); then
    pass "CPU usage is acceptable (${CPU_USAGE}%)"
else
    warn "CPU usage is high (${CPU_USAGE}%)"
fi

# Memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEM_USAGE" -lt 90 ]; then
    pass "Memory usage is acceptable (${MEM_USAGE}%)"
else
    warn "Memory usage is high (${MEM_USAGE}%)"
fi

# Disk usage
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
if [ "$DISK_USAGE" -lt 80 ]; then
    pass "Disk usage is acceptable (${DISK_USAGE}%)"
else
    warn "Disk usage is high (${DISK_USAGE}%)"
fi

echo ""

# ============================================
# 8. Configuration Files
# ============================================
echo "8. Checking Configuration Files..."

# Check .env.cloud
if [ -f "/opt/digital-fte/.env.cloud" ]; then
    pass "Cloud credentials file exists"
else
    fail "Cloud credentials file not found"
fi

# Check agent config
if [ -f "/opt/digital-fte/obsidian-vault/config/agent-config.json" ]; then
    pass "Agent configuration file exists"

    # Verify cloud agent has read_only scope
    SCOPE=$(jq -r '.credential_scope' /opt/digital-fte/obsidian-vault/config/agent-config.json 2>/dev/null || echo "")
    if [ "$SCOPE" = "read_only" ]; then
        pass "Cloud agent has read_only credential scope"
    else
        fail "Cloud agent does not have read_only credential scope"
    fi
else
    fail "Agent configuration file not found"
fi

echo ""

# ============================================
# Summary
# ============================================
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ System validation PASSED${NC}"
    echo "All critical checks passed. System is operational."
    exit 0
elif [ "$FAILED" -lt 3 ]; then
    echo -e "${YELLOW}⚠ System validation PASSED with warnings${NC}"
    echo "Some checks failed but system may still be operational."
    echo "Review failed checks and address issues."
    exit 0
else
    echo -e "${RED}✗ System validation FAILED${NC}"
    echo "Multiple critical checks failed. System may not be operational."
    echo "Review failed checks and troubleshoot before proceeding."
    exit 1
fi
