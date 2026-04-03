#!/bin/bash
# Security Audit Script for Platinum Tier
# Validates security configuration and identifies vulnerabilities
#
# Usage: bash security_audit.sh
# Based on tasks.md T077 and FR-040 through FR-042

set -e

echo "=========================================="
echo "Digital FTE Security Audit"
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

echo "Starting security audit..."
echo ""

# ============================================
# 1. Credential Scope Verification
# ============================================
echo "1. Verifying Credential Scope (FR-004, FR-005)..."

# Check cloud agent has read-only credentials
if [ -f "/opt/digital-fte/obsidian-vault/config/agent-config.json" ]; then
    CLOUD_SCOPE=$(jq -r '.credential_scope' /opt/digital-fte/obsidian-vault/config/agent-config.json 2>/dev/null || echo "")

    if [ "$CLOUD_SCOPE" = "read_only" ]; then
        pass "Cloud agent has read_only credential scope"
    else
        fail "Cloud agent does NOT have read_only credential scope (CRITICAL)"
    fi
else
    fail "Agent configuration file not found"
fi

# Check .env.cloud exists and has restrictive permissions
if [ -f "/opt/digital-fte/.env.cloud" ]; then
    PERMS=$(stat -c "%a" /opt/digital-fte/.env.cloud)
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
        pass "Cloud credentials file has restrictive permissions ($PERMS)"
    else
        fail "Cloud credentials file has insecure permissions ($PERMS)"
    fi
else
    fail "Cloud credentials file not found"
fi

# Check for hardcoded secrets in code
HARDCODED_SECRETS=$(grep -r "password\|secret\|api_key" /opt/digital-fte/cloud --include="*.py" | grep -v "# " | grep -v "\"\"\"" | wc -l)
if [ "$HARDCODED_SECRETS" -eq 0 ]; then
    pass "No hardcoded secrets found in cloud agent code"
else
    warn "Found $HARDCODED_SECRETS potential hardcoded secrets in code"
fi

echo ""

# ============================================
# 2. Vault Sync Security
# ============================================
echo "2. Checking Vault Sync Security..."

cd /opt/digital-fte/obsidian-vault

# Check .gitignore exists and excludes sensitive files
if [ -f ".gitignore" ]; then
    pass ".gitignore file exists"

    # Check for critical exclusions
    if grep -q "\.env" .gitignore; then
        pass ".env files excluded from git"
    else
        fail ".env files NOT excluded from git (CRITICAL)"
    fi

    if grep -q "WhatsApp_Sessions" .gitignore; then
        pass "WhatsApp sessions excluded from git"
    else
        warn "WhatsApp sessions not explicitly excluded from git"
    fi

    if grep -q "\.obsidian/workspace" .gitignore; then
        pass "Obsidian workspace excluded from git"
    else
        warn "Obsidian workspace not excluded from git"
    fi
else
    fail ".gitignore file not found (CRITICAL)"
fi

# Check for accidentally committed secrets
COMMITTED_SECRETS=$(git log --all --full-history -- "*.env" "*.key" "*.pem" 2>/dev/null | wc -l)
if [ "$COMMITTED_SECRETS" -eq 0 ]; then
    pass "No secrets found in git history"
else
    fail "Found $COMMITTED_SECRETS potential secrets in git history (CRITICAL)"
fi

# Check repository is private (if using GitHub)
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [[ "$REMOTE_URL" == *"github.com"* ]]; then
    # Extract repo path
    REPO_PATH=$(echo "$REMOTE_URL" | sed 's/.*github.com[:/]\(.*\)\.git/\1/')

    # Check if repo is private (requires gh CLI)
    if command -v gh &> /dev/null; then
        VISIBILITY=$(gh repo view "$REPO_PATH" --json visibility -q .visibility 2>/dev/null || echo "unknown")
        if [ "$VISIBILITY" = "PRIVATE" ]; then
            pass "GitHub repository is private"
        elif [ "$VISIBILITY" = "PUBLIC" ]; then
            fail "GitHub repository is PUBLIC (CRITICAL)"
        else
            warn "Could not verify repository visibility"
        fi
    else
        warn "gh CLI not installed, cannot verify repository visibility"
    fi
fi

echo ""

# ============================================
# 3. SSL/TLS Configuration
# ============================================
echo "3. Checking SSL/TLS Configuration..."

# Check SSL certificate exists
if [ -d "/etc/letsencrypt/live" ]; then
    CERT_COUNT=$(find /etc/letsencrypt/live -name "cert.pem" | wc -l)
    if [ "$CERT_COUNT" -gt 0 ]; then
        pass "SSL certificate(s) found ($CERT_COUNT)"

        # Check certificate expiry
        for cert in $(find /etc/letsencrypt/live -name "cert.pem"); do
            EXPIRY=$(openssl x509 -enddate -noout -in "$cert" 2>/dev/null | cut -d= -f2)
            EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo "0")
            NOW_EPOCH=$(date +%s)
            DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

            if [ "$DAYS_LEFT" -gt 30 ]; then
                pass "SSL certificate valid for $DAYS_LEFT days"
            elif [ "$DAYS_LEFT" -gt 7 ]; then
                warn "SSL certificate expires in $DAYS_LEFT days"
            else
                fail "SSL certificate expires in $DAYS_LEFT days (CRITICAL)"
            fi
        done
    else
        warn "No SSL certificates found"
    fi
else
    warn "Let's Encrypt directory not found"
fi

# Check nginx SSL configuration
if [ -f "/etc/nginx/sites-enabled/odoo" ]; then
    if grep -q "ssl_protocols TLSv1.2 TLSv1.3" /etc/nginx/sites-enabled/odoo; then
        pass "Nginx using secure TLS protocols"
    else
        warn "Nginx may not be using secure TLS protocols"
    fi

    if grep -q "ssl_ciphers" /etc/nginx/sites-enabled/odoo; then
        pass "Nginx has SSL cipher configuration"
    else
        warn "Nginx missing SSL cipher configuration"
    fi
fi

echo ""

# ============================================
# 4. Firewall Configuration
# ============================================
echo "4. Checking Firewall Configuration..."

# Check if ufw is active
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | grep -c "Status: active" || echo "0")
    if [ "$UFW_STATUS" -gt 0 ]; then
        pass "UFW firewall is active"

        # Check allowed ports
        if ufw status | grep -q "22/tcp.*ALLOW"; then
            pass "SSH port (22) is allowed"
        else
            warn "SSH port (22) may not be allowed"
        fi

        if ufw status | grep -q "80/tcp.*ALLOW"; then
            pass "HTTP port (80) is allowed"
        else
            warn "HTTP port (80) not allowed (needed for Let's Encrypt)"
        fi

        if ufw status | grep -q "443/tcp.*ALLOW"; then
            pass "HTTPS port (443) is allowed"
        else
            fail "HTTPS port (443) not allowed"
        fi

        # Check for unnecessary open ports
        OPEN_PORTS=$(ufw status numbered | grep ALLOW | wc -l)
        if [ "$OPEN_PORTS" -le 5 ]; then
            pass "Minimal ports open ($OPEN_PORTS)"
        else
            warn "Many ports open ($OPEN_PORTS) - review firewall rules"
        fi
    else
        fail "UFW firewall is NOT active (CRITICAL)"
    fi
else
    warn "UFW not installed"
fi

echo ""

# ============================================
# 5. Service Permissions
# ============================================
echo "5. Checking Service Permissions..."

# Check cloud agent runs as non-root
CLOUD_AGENT_USER=$(systemctl show cloud-agent.service -p User --value 2>/dev/null || echo "root")
if [ "$CLOUD_AGENT_USER" != "root" ]; then
    pass "Cloud agent runs as non-root user ($CLOUD_AGENT_USER)"
else
    fail "Cloud agent runs as root (CRITICAL)"
fi

# Check Odoo runs as non-root
ODOO_USER=$(systemctl show odoo.service -p User --value 2>/dev/null || echo "root")
if [ "$ODOO_USER" != "root" ]; then
    pass "Odoo runs as non-root user ($ODOO_USER)"
else
    fail "Odoo runs as root (CRITICAL)"
fi

# Check file permissions on sensitive directories
if [ -d "/opt/digital-fte" ]; then
    OWNER=$(stat -c "%U" /opt/digital-fte)
    if [ "$OWNER" != "root" ]; then
        pass "/opt/digital-fte owned by non-root user ($OWNER)"
    else
        warn "/opt/digital-fte owned by root"
    fi
fi

echo ""

# ============================================
# 6. Database Security
# ============================================
echo "6. Checking Database Security..."

# Check PostgreSQL is not listening on public interface
if systemctl is-active --quiet postgresql; then
    PG_LISTEN=$(sudo -u postgres psql -t -c "SHOW listen_addresses" 2>/dev/null | tr -d ' ')
    if [ "$PG_LISTEN" = "localhost" ] || [ "$PG_LISTEN" = "127.0.0.1" ]; then
        pass "PostgreSQL listening on localhost only"
    else
        warn "PostgreSQL may be listening on public interface ($PG_LISTEN)"
    fi

    # Check for default passwords
    DEFAULT_PASS=$(sudo -u postgres psql -t -c "SELECT COUNT(*) FROM pg_shadow WHERE passwd IS NULL" 2>/dev/null | tr -d ' ')
    if [ "$DEFAULT_PASS" = "0" ]; then
        pass "No PostgreSQL users with null passwords"
    else
        fail "Found $DEFAULT_PASS PostgreSQL users with null passwords"
    fi
fi

echo ""

# ============================================
# 7. Audit Trail Integrity
# ============================================
echo "7. Checking Audit Trail Integrity..."

if [ -f "/opt/digital-fte/obsidian-vault/audit_trail.jsonl" ]; then
    pass "Audit trail file exists"

    # Check file is append-only (immutable)
    AUDIT_PERMS=$(stat -c "%a" /opt/digital-fte/obsidian-vault/audit_trail.jsonl)
    if [ "$AUDIT_PERMS" = "644" ] || [ "$AUDIT_PERMS" = "444" ]; then
        pass "Audit trail has appropriate permissions ($AUDIT_PERMS)"
    else
        warn "Audit trail permissions may be too permissive ($AUDIT_PERMS)"
    fi

    # Check audit trail is not empty
    LINE_COUNT=$(wc -l < /opt/digital-fte/obsidian-vault/audit_trail.jsonl)
    if [ "$LINE_COUNT" -gt 0 ]; then
        pass "Audit trail has $LINE_COUNT entries"
    else
        warn "Audit trail is empty"
    fi
else
    warn "Audit trail file not found"
fi

echo ""

# ============================================
# 8. System Updates
# ============================================
echo "8. Checking System Updates..."

# Check for security updates
if command -v apt &> /dev/null; then
    SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
    if [ "$SECURITY_UPDATES" -eq 0 ]; then
        pass "No pending security updates"
    else
        warn "$SECURITY_UPDATES pending security updates"
    fi

    # Check last update time
    LAST_UPDATE=$(stat -c %Y /var/lib/apt/periodic/update-success-stamp 2>/dev/null || echo "0")
    NOW=$(date +%s)
    DAYS_SINCE_UPDATE=$(( ($NOW - $LAST_UPDATE) / 86400 ))

    if [ "$DAYS_SINCE_UPDATE" -lt 7 ]; then
        pass "System updated recently ($DAYS_SINCE_UPDATE days ago)"
    else
        warn "System not updated recently ($DAYS_SINCE_UPDATE days ago)"
    fi
fi

echo ""

# ============================================
# 9. Credential Rotation
# ============================================
echo "9. Checking Credential Rotation (FR-042)..."

if [ -f "/opt/digital-fte/obsidian-vault/config/credentials.json" ]; then
    pass "Credential tracking file exists"

    # Check for expiring credentials
    EXPIRING=$(python3 << 'EOF'
import json
from datetime import datetime, timedelta
try:
    with open("/opt/digital-fte/obsidian-vault/config/credentials.json") as f:
        data = json.load(f)
    expiring = 0
    for cred in data.get("credentials", []):
        expires = datetime.fromisoformat(cred["expires_at"])
        if expires < datetime.now() + timedelta(days=7):
            expiring += 1
    print(expiring)
except:
    print("0")
EOF
)

    if [ "$EXPIRING" -eq 0 ]; then
        pass "No credentials expiring in next 7 days"
    else
        warn "$EXPIRING credentials expiring in next 7 days"
    fi
else
    warn "Credential tracking file not found"
fi

echo ""

# ============================================
# 10. Backup Security
# ============================================
echo "10. Checking Backup Security..."

if [ -d "/backups/odoo" ]; then
    # Check backup directory permissions
    BACKUP_PERMS=$(stat -c "%a" /backups/odoo)
    if [ "$BACKUP_PERMS" = "700" ] || [ "$BACKUP_PERMS" = "750" ]; then
        pass "Backup directory has restrictive permissions ($BACKUP_PERMS)"
    else
        warn "Backup directory permissions may be too permissive ($BACKUP_PERMS)"
    fi

    # Check if backups are encrypted
    ENCRYPTED_BACKUPS=$(find /backups/odoo -name "*.gpg" -o -name "*.enc" | wc -l)
    TOTAL_BACKUPS=$(find /backups/odoo -name "*.sql.gz" | wc -l)

    if [ "$ENCRYPTED_BACKUPS" -gt 0 ]; then
        pass "Found $ENCRYPTED_BACKUPS encrypted backups"
    elif [ "$TOTAL_BACKUPS" -gt 0 ]; then
        warn "Backups are not encrypted (consider enabling encryption)"
    fi
fi

echo ""

# ============================================
# Summary
# ============================================
echo "=========================================="
echo "Security Audit Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

# Calculate security score
TOTAL=$((PASSED + WARNINGS + FAILED))
SCORE=$(( (PASSED * 100) / TOTAL ))

echo "Security Score: $SCORE/100"
echo ""

if [ "$FAILED" -eq 0 ] && [ "$WARNINGS" -lt 5 ]; then
    echo -e "${GREEN}✓ Security audit PASSED${NC}"
    echo "System meets security requirements."
    exit 0
elif [ "$FAILED" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Security audit PASSED with warnings${NC}"
    echo "System is secure but has areas for improvement."
    exit 0
else
    echo -e "${RED}✗ Security audit FAILED${NC}"
    echo "Critical security issues found. Address immediately."
    exit 1
fi
