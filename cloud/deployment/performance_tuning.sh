#!/bin/bash
# Performance Tuning Script for Platinum Tier
# Analyzes performance metrics and suggests optimizations
#
# Usage: bash performance_tuning.sh
# Based on tasks.md T078

set -e

echo "=========================================="
echo "Digital FTE Performance Analysis"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Analyzing system performance..."
echo ""

# ============================================
# 1. Resource Usage Analysis
# ============================================
echo "1. Resource Usage Analysis"
echo "-------------------------------------------"

# CPU Usage
echo -e "${BLUE}CPU Usage:${NC}"
CPU_IDLE=$(top -bn1 | grep "Cpu(s)" | awk '{print $8}' | cut -d'%' -f1)
CPU_USED=$(echo "100 - $CPU_IDLE" | bc)
echo "  Current: ${CPU_USED}%"

if (( $(echo "$CPU_USED < 50" | bc -l) )); then
    echo -e "  ${GREEN}✓ CPU usage is healthy${NC}"
elif (( $(echo "$CPU_USED < 80" | bc -l) )); then
    echo -e "  ${YELLOW}⚠ CPU usage is moderate${NC}"
    echo "  Recommendation: Monitor for sustained high usage"
else
    echo -e "  ${RED}✗ CPU usage is high${NC}"
    echo "  Recommendations:"
    echo "    - Increase watcher cycle interval (5min → 10min)"
    echo "    - Reduce Odoo workers (current: 2)"
    echo "    - Check for runaway processes: ps aux --sort=-%cpu | head -10"
fi

echo ""

# Memory Usage
echo -e "${BLUE}Memory Usage:${NC}"
MEM_TOTAL=$(free -m | grep Mem | awk '{print $2}')
MEM_USED=$(free -m | grep Mem | awk '{print $3}')
MEM_PERCENT=$(echo "scale=1; $MEM_USED * 100 / $MEM_TOTAL" | bc)
echo "  Used: ${MEM_USED}MB / ${MEM_TOTAL}MB (${MEM_PERCENT}%)"

if (( $(echo "$MEM_PERCENT < 70" | bc -l) )); then
    echo -e "  ${GREEN}✓ Memory usage is healthy${NC}"
elif (( $(echo "$MEM_PERCENT < 85" | bc -l) )); then
    echo -e "  ${YELLOW}⚠ Memory usage is moderate${NC}"
    echo "  Recommendation: Monitor for memory leaks"
else
    echo -e "  ${RED}✗ Memory usage is high${NC}"
    echo "  Recommendations:"
    echo "    - Reduce Odoo memory limit (2GB → 1.5GB)"
    echo "    - Add daily cloud agent restart: RuntimeMaxSec=86400"
    echo "    - Check memory hogs: ps aux --sort=-%mem | head -10"
fi

echo ""

# Disk Usage
echo -e "${BLUE}Disk Usage:${NC}"
DISK_USED=$(df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')
echo "  Used: ${DISK_USED}% (${DISK_AVAIL} available)"

if [ "$DISK_USED" -lt 60 ]; then
    echo -e "  ${GREEN}✓ Disk usage is healthy${NC}"
elif [ "$DISK_USED" -lt 80 ]; then
    echo -e "  ${YELLOW}⚠ Disk usage is moderate${NC}"
    echo "  Recommendation: Plan for cleanup or expansion"
else
    echo -e "  ${RED}✗ Disk usage is high${NC}"
    echo "  Recommendations:"
    echo "    - Clean old backups: find /backups -mtime +30 -delete"
    echo "    - Clean old logs: journalctl --vacuum-time=7d"
    echo "    - Check large files: du -sh /* | sort -h | tail -10"
fi

echo ""

# ============================================
# 2. Service Performance
# ============================================
echo "2. Service Performance"
echo "-------------------------------------------"

# Cloud Agent Performance
echo -e "${BLUE}Cloud Agent:${NC}"
if systemctl is-active --quiet cloud-agent.service; then
    # Check restart count
    RESTART_COUNT=$(systemctl show cloud-agent.service -p NRestarts --value)
    echo "  Restarts (since boot): $RESTART_COUNT"

    if [ "$RESTART_COUNT" -eq 0 ]; then
        echo -e "  ${GREEN}✓ No restarts - stable${NC}"
    elif [ "$RESTART_COUNT" -lt 5 ]; then
        echo -e "  ${YELLOW}⚠ Some restarts - monitor${NC}"
    else
        echo -e "  ${RED}✗ Frequent restarts - investigate${NC}"
        echo "  Check logs: journalctl -u cloud-agent.service -n 100"
    fi

    # Check memory usage
    AGENT_MEM=$(ps aux | grep cloud_agent | grep -v grep | awk '{print $6}' | head -1)
    if [ -n "$AGENT_MEM" ]; then
        AGENT_MEM_MB=$((AGENT_MEM / 1024))
        echo "  Memory: ${AGENT_MEM_MB}MB"

        if [ "$AGENT_MEM_MB" -lt 200 ]; then
            echo -e "  ${GREEN}✓ Memory usage is healthy${NC}"
        elif [ "$AGENT_MEM_MB" -lt 400 ]; then
            echo -e "  ${YELLOW}⚠ Memory usage is moderate${NC}"
        else
            echo -e "  ${RED}✗ Memory usage is high${NC}"
            echo "  Recommendation: Add daily restart to prevent memory leaks"
        fi
    fi
fi

echo ""

# Odoo Performance
echo -e "${BLUE}Odoo:${NC}"
if systemctl is-active --quiet odoo.service; then
    # Check response time
    START=$(date +%s%N)
    curl -s -o /dev/null http://localhost:8069/web/health
    END=$(date +%s%N)
    RESPONSE_TIME=$(( ($END - $START) / 1000000 ))
    echo "  Health endpoint response: ${RESPONSE_TIME}ms"

    if [ "$RESPONSE_TIME" -lt 200 ]; then
        echo -e "  ${GREEN}✓ Response time is excellent${NC}"
    elif [ "$RESPONSE_TIME" -lt 1000 ]; then
        echo -e "  ${YELLOW}⚠ Response time is acceptable${NC}"
    else
        echo -e "  ${RED}✗ Response time is slow${NC}"
        echo "  Recommendations:"
        echo "    - Increase Odoo workers (2 → 3)"
        echo "    - Optimize PostgreSQL: VACUUM ANALYZE"
        echo "    - Check slow queries in PostgreSQL logs"
    fi

    # Check worker count
    WORKER_COUNT=$(ps aux | grep odoo | grep -v grep | wc -l)
    echo "  Worker processes: $WORKER_COUNT"

    if [ "$WORKER_COUNT" -lt 2 ]; then
        echo -e "  ${YELLOW}⚠ Low worker count${NC}"
        echo "  Recommendation: Increase workers in /etc/odoo/odoo.conf"
    fi
fi

echo ""

# Vault Sync Performance
echo -e "${BLUE}Vault Sync:${NC}"
if [ -f "/opt/digital-fte/obsidian-vault/.sync-status/cloud.json" ]; then
    SYNC_LAG=$(jq -r '.sync_lag_seconds' /opt/digital-fte/obsidian-vault/.sync-status/cloud.json 2>/dev/null || echo "0")
    echo "  Current lag: ${SYNC_LAG}s"

    if [ "$SYNC_LAG" -lt 60 ]; then
        echo -e "  ${GREEN}✓ Sync lag is minimal${NC}"
    elif [ "$SYNC_LAG" -lt 300 ]; then
        echo -e "  ${YELLOW}⚠ Sync lag is moderate${NC}"
        echo "  Recommendation: Check network connectivity"
    else
        echo -e "  ${RED}✗ Sync lag is high${NC}"
        echo "  Recommendations:"
        echo "    - Check git remote connectivity"
        echo "    - Reduce sync frequency (30s → 60s)"
        echo "    - Check for large files in vault"
    fi
fi

echo ""

# ============================================
# 3. Database Performance
# ============================================
echo "3. Database Performance"
echo "-------------------------------------------"

if systemctl is-active --quiet postgresql; then
    echo -e "${BLUE}PostgreSQL:${NC}"

    # Check database size
    DB_SIZE=$(sudo -u postgres psql -t -c "SELECT pg_size_pretty(pg_database_size('odoo'))" 2>/dev/null | tr -d ' ')
    echo "  Database size: $DB_SIZE"

    # Check connection count
    CONN_COUNT=$(sudo -u postgres psql -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='odoo'" 2>/dev/null | tr -d ' ')
    echo "  Active connections: $CONN_COUNT"

    if [ "$CONN_COUNT" -lt 10 ]; then
        echo -e "  ${GREEN}✓ Connection count is healthy${NC}"
    elif [ "$CONN_COUNT" -lt 50 ]; then
        echo -e "  ${YELLOW}⚠ Connection count is moderate${NC}"
    else
        echo -e "  ${RED}✗ Connection count is high${NC}"
        echo "  Recommendation: Check for connection leaks"
    fi

    # Suggest VACUUM if database is large
    DB_SIZE_MB=$(sudo -u postgres psql -t -c "SELECT pg_database_size('odoo')/1024/1024" 2>/dev/null | tr -d ' ')
    if [ "$DB_SIZE_MB" -gt 1000 ]; then
        echo -e "  ${YELLOW}⚠ Large database${NC}"
        echo "  Recommendation: Run VACUUM ANALYZE regularly"
        echo "    sudo -u postgres psql odoo -c 'VACUUM ANALYZE;'"
    fi
fi

echo ""

# ============================================
# 4. Network Performance
# ============================================
echo "4. Network Performance"
echo "-------------------------------------------"

echo -e "${BLUE}Network Latency:${NC}"

# Test git remote latency
if [ -d "/opt/digital-fte/obsidian-vault/.git" ]; then
    cd /opt/digital-fte/obsidian-vault
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

    if [ -n "$REMOTE_URL" ]; then
        START=$(date +%s%N)
        git ls-remote origin HEAD &>/dev/null
        END=$(date +%s%N)
        GIT_LATENCY=$(( ($END - $START) / 1000000 ))
        echo "  Git remote: ${GIT_LATENCY}ms"

        if [ "$GIT_LATENCY" -lt 500 ]; then
            echo -e "  ${GREEN}✓ Git latency is excellent${NC}"
        elif [ "$GIT_LATENCY" -lt 2000 ]; then
            echo -e "  ${YELLOW}⚠ Git latency is acceptable${NC}"
        else
            echo -e "  ${RED}✗ Git latency is high${NC}"
            echo "  Recommendation: Check network connectivity or use closer git server"
        fi
    fi
fi

echo ""

# ============================================
# 5. Optimization Recommendations
# ============================================
echo "5. Optimization Recommendations"
echo "-------------------------------------------"

echo -e "${BLUE}Suggested Optimizations:${NC}"
echo ""

# Check if optimizations are already applied
OPTIMIZATIONS_NEEDED=0

# Check watcher cycle interval
WATCHER_INTERVAL=$(grep -o "sleep([0-9]*)" /opt/digital-fte/cloud/agent/cloud_agent.py 2>/dev/null | grep -o "[0-9]*" || echo "300")
if [ "$WATCHER_INTERVAL" -eq 300 ] && (( $(echo "$CPU_USED > 60" | bc -l) )); then
    echo "1. Increase watcher cycle interval:"
    echo "   Edit cloud/agent/cloud_agent.py: sleep(300) → sleep(600)"
    echo "   Benefit: Reduce CPU usage by 50%"
    echo ""
    ((OPTIMIZATIONS_NEEDED++))
fi

# Check sync interval
if [ -f "/etc/systemd/system/vault-sync.timer" ]; then
    SYNC_INTERVAL=$(grep "OnUnitActiveSec" /etc/systemd/system/vault-sync.timer | grep -o "[0-9]*" || echo "30")
    if [ "$SYNC_INTERVAL" -eq 30 ] && [ "$SYNC_LAG" -lt 30 ]; then
        echo "2. Increase vault sync interval:"
        echo "   Edit /etc/systemd/system/vault-sync.timer: OnUnitActiveSec=30s → 60s"
        echo "   Benefit: Reduce network traffic and CPU usage"
        echo ""
        ((OPTIMIZATIONS_NEEDED++))
    fi
fi

# Check Odoo workers
if [ -f "/etc/odoo/odoo.conf" ]; then
    ODOO_WORKERS=$(grep "^workers" /etc/odoo/odoo.conf | grep -o "[0-9]*" || echo "2")
    if [ "$ODOO_WORKERS" -eq 2 ] && [ "$RESPONSE_TIME" -gt 500 ]; then
        echo "3. Increase Odoo workers:"
        echo "   Edit /etc/odoo/odoo.conf: workers = 3"
        echo "   Benefit: Improve Odoo response time"
        echo ""
        ((OPTIMIZATIONS_NEEDED++))
    fi
fi

# Check for daily restart
if ! systemctl show cloud-agent.service | grep -q "RuntimeMaxSec"; then
    echo "4. Add daily cloud agent restart:"
    echo "   sudo systemctl edit cloud-agent.service"
    echo "   Add: [Service]"
    echo "        RuntimeMaxSec=86400"
    echo "   Benefit: Prevent memory leaks"
    echo ""
    ((OPTIMIZATIONS_NEEDED++))
fi

# Check PostgreSQL tuning
if [ -f "/etc/postgresql/*/main/postgresql.conf" ]; then
    SHARED_BUFFERS=$(grep "^shared_buffers" /etc/postgresql/*/main/postgresql.conf | grep -o "[0-9]*" || echo "128")
    if [ "$SHARED_BUFFERS" -lt 256 ]; then
        echo "5. Tune PostgreSQL:"
        echo "   Edit postgresql.conf: shared_buffers = 256MB"
        echo "   Benefit: Improve database performance"
        echo ""
        ((OPTIMIZATIONS_NEEDED++))
    fi
fi

if [ "$OPTIMIZATIONS_NEEDED" -eq 0 ]; then
    echo -e "${GREEN}✓ No optimizations needed - system is well-tuned${NC}"
fi

echo ""

# ============================================
# Summary
# ============================================
echo "=========================================="
echo "Performance Summary"
echo "=========================================="
echo ""
echo "CPU Usage: ${CPU_USED}%"
echo "Memory Usage: ${MEM_PERCENT}%"
echo "Disk Usage: ${DISK_USED}%"
echo "Optimizations Suggested: $OPTIMIZATIONS_NEEDED"
echo ""

if [ "$OPTIMIZATIONS_NEEDED" -eq 0 ]; then
    echo -e "${GREEN}✓ System performance is optimal${NC}"
elif [ "$OPTIMIZATIONS_NEEDED" -lt 3 ]; then
    echo -e "${YELLOW}⚠ Minor optimizations recommended${NC}"
else
    echo -e "${RED}✗ Multiple optimizations recommended${NC}"
fi

echo ""
echo "For detailed performance monitoring, check:"
echo "  - Cloud agent logs: journalctl -u cloud-agent.service"
echo "  - Odoo logs: journalctl -u odoo.service"
echo "  - System metrics: htop or top"
echo "  - Database stats: sudo -u postgres psql odoo -c 'SELECT * FROM pg_stat_activity;'"
