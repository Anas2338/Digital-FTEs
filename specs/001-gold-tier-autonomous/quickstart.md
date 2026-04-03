# Gold Tier Quickstart Guide

**Feature**: 001-gold-tier-autonomous  
**Date**: 2026-03-31  
**Prerequisites**: Bronze Tier and Silver Tier fully functional

## Overview

This guide walks you through setting up Gold Tier capabilities: Odoo accounting integration, social media management (Facebook, Instagram, Twitter/X), weekly CEO briefing generation, enhanced error recovery, and comprehensive audit logging.

**Estimated Setup Time**: 2-3 hours

---

## Prerequisites

### System Requirements

- ✅ Bronze Tier operational (Gmail watcher, basic agent workflow, Obsidian vault)
- ✅ Silver Tier operational (WhatsApp, banking integration, task management)
- ✅ Python 3.11+ with `uv` package manager
- ✅ Obsidian vault configured and accessible
- ✅ OS keychain access (Windows Credential Manager, macOS Keychain, or Linux Secret Service)

### External Services Required

1. **Odoo Community Edition** (self-hosted)
   - Version: 19.0 or later
   - Access: Admin credentials with API access enabled
   - Network: Accessible from your machine (localhost or network URL)

2. **Facebook Developer Account**
   - App created with required permissions
   - Access token with `pages_manage_posts` and `pages_read_engagement` permissions
   - Facebook Page ID

3. **Instagram Business Account**
   - Linked to Facebook Page
   - Converted from personal to business account
   - Access via Facebook Graph API

4. **Twitter Developer Account**
   - API v2 access with "Read and Write" permissions
   - API Key, API Secret, Access Token, Access Token Secret

---

## Installation

### Step 1: Install Dependencies

```bash
cd Digital-FTEs

# Install new Gold Tier dependencies
cd watchers
uv add odoorpc schedule facebook-sdk tweepy

cd ../mcp-servers/digital-fte-server
uv add odoorpc schedule facebook-sdk tweepy
```

### Step 2: Configure Odoo Integration

#### 2.1 Verify Odoo Installation

```bash
# Test Odoo connection
curl http://localhost:8069/web/database/selector

# Expected: Odoo login page HTML or database selector
```

#### 2.2 Store Odoo Credentials

```bash
# Run credential setup script
python watchers/setup_credentials.py

# When prompted, enter:
# - Odoo URL: http://localhost:8069
# - Database name: your_database_name
# - Username: admin
# - Password: your_odoo_password
```

**Credentials are stored securely in OS keychain** (never in code or config files).

#### 2.3 Test Odoo Connection

```bash
# Run Odoo connection test
python watchers/odoo_watcher/test_connection.py

# Expected output:
# ✅ Connected to Odoo 19.0
# ✅ Authentication successful
# ✅ Account access verified
```

### Step 3: Configure Social Media Integrations

#### 3.1 Facebook Setup

1. **Create Facebook App** (if not already created):
   - Go to https://developers.facebook.com/apps/
   - Create new app → Business type
   - Add "Facebook Login" and "Pages" products

2. **Get Access Token**:
   - Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/
   - Select your app
   - Request permissions: `pages_manage_posts`, `pages_read_engagement`, `pages_read_user_content`
   - Generate token
   - **Important**: Convert to long-lived token (60 days) or use page access token (never expires)

3. **Get Page ID**:
   - Go to your Facebook Page
   - Settings → Page Info → Page ID

4. **Store Credentials**:
   ```bash
   python watchers/setup_credentials.py --service facebook
   
   # When prompted:
   # - Facebook Access Token: [paste token]
   # - Facebook Page ID: [paste page ID]
   ```

#### 3.2 Instagram Setup

**Prerequisites**: Instagram account must be converted to Business Account and linked to Facebook Page.

1. **Convert to Business Account**:
   - Open Instagram app
   - Settings → Account → Switch to Professional Account → Business
   - Link to Facebook Page

2. **Get Instagram Account ID**:
   ```bash
   # Use Facebook Graph API Explorer
   # Query: me/accounts (returns your pages)
   # Then: {page-id}?fields=instagram_business_account
   ```

3. **Store Credentials**:
   ```bash
   python watchers/setup_credentials.py --service instagram
   
   # When prompted:
   # - Instagram Account ID: [paste account ID]
   # - Instagram Access Token: [same as Facebook token]
   ```

#### 3.3 Twitter/X Setup

1. **Create Twitter App** (if not already created):
   - Go to https://developer.twitter.com/en/portal/dashboard
   - Create project and app
   - Enable OAuth 2.0 with "Read and Write" permissions

2. **Get API Credentials**:
   - Go to your app settings
   - Keys and Tokens tab
   - Generate API Key, API Secret, Access Token, Access Token Secret

3. **Store Credentials**:
   ```bash
   python watchers/setup_credentials.py --service twitter
   
   # When prompted:
   # - Twitter API Key: [paste key]
   # - Twitter API Secret: [paste secret]
   # - Twitter Access Token: [paste token]
   # - Twitter Access Token Secret: [paste secret]
   ```

#### 3.4 Test Social Media Connections

```bash
# Test all social media connections
python watchers/social_media_watcher/test_connections.py

# Expected output:
# ✅ Facebook: Connected (Page: Your Page Name)
# ✅ Instagram: Connected (Account: @yourusername)
# ✅ Twitter: Connected (@yourusername)
```

### Step 4: Initialize Obsidian Vault Structure

```bash
# Create Gold Tier directories in Obsidian vault
python scripts/setup_gold_tier_vault.py

# Creates:
# - obsidian-vault/Briefings/
# - obsidian-vault/Accounting/
# - obsidian-vault/Audit_Logs/
```

### Step 5: Start Watchers

```bash
# Start Odoo watcher (polls every 5 minutes)
python watchers/odoo_watcher/watcher.py &

# Start social media watcher (polls every 5 minutes)
python watchers/social_media_watcher/watcher.py &

# Start briefing watcher (runs Monday 8 AM)
python watchers/briefing_watcher/watcher.py &

# Verify watchers are running
ps aux | grep watcher
```

---

## Configuration

### Transaction Categorization Rules

Edit `watchers/odoo_watcher/config.py` to customize category mappings:

```python
CATEGORY_MAPPING = {
    'Revenue': ['400', '401', '402'],  # Odoo account codes
    'COGS': ['500', '501'],
    'Operating Expenses': ['600', '601', '602', '603'],
    'Assets': ['100', '101', '102'],
    'Liabilities': ['200', '201'],
    'Equity': ['300', '301']
}
```

### Social Media Rate Limits

Edit `watchers/social_media_watcher/config.py`:

```python
RATE_LIMITS = {
    'daily_posts': 10,  # Max posts per day across all platforms
    'high_engagement_threshold': 3.0,  # Notify when engagement > 3x average
}
```

### CEO Briefing Schedule

Edit `watchers/briefing_watcher/config.py`:

```python
BRIEFING_SCHEDULE = {
    'day_of_week': 'monday',
    'time': '08:00',  # 24-hour format
    'timezone': 'local',  # Uses system timezone
}
```

### Circuit Breaker Settings

Edit `mcp-servers/digital-fte-server/circuit_breaker.py`:

```python
CIRCUIT_BREAKER_CONFIG = {
    'error_threshold': 0.20,  # Open circuit at 20% error rate
    'window_size': 10,  # Track last 10 requests
    'recovery_schedule': [300, 600, 1200, 3600],  # 5m, 10m, 20m, 1h
}
```

---

## Verification

### Test 1: Odoo Transaction Recording

```bash
# Create test transaction in Odoo
# Wait 5 minutes for watcher to detect
# Check Obsidian vault: Accounting/transactions.db

sqlite3 obsidian-vault/Accounting/transactions.db "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 1;"

# Expected: Your test transaction appears
```

### Test 2: Social Media Posting

```bash
# Create test post
python -c "
from mcp_servers.digital_fte_server.tools.social_post import social_post
result = social_post(
    content='Test post from Digital FTE',
    platforms=['facebook'],
    approval_required=False  # For testing only
)
print(result)
"

# Check Facebook page for post
```

### Test 3: CEO Briefing Generation

```bash
# Generate test briefing (don't wait for Monday)
python -c "
from mcp_servers.digital_fte_server.tools.generate_briefing import generate_briefing
result = generate_briefing(force_regenerate=True)
print(result)
"

# Check: obsidian-vault/Briefings/YYYY-WW.md
```

### Test 4: Circuit Breaker

```bash
# Simulate Odoo failure
# Stop Odoo service temporarily
sudo systemctl stop odoo  # or equivalent

# Trigger multiple requests (will fail)
for i in {1..5}; do
    python watchers/odoo_watcher/test_connection.py
done

# Check circuit breaker status
sqlite3 watchers/shared/integration_status.db "SELECT * FROM integration_status WHERE integration_name='odoo';"

# Expected: circuit_breaker_state = 'open'

# Restart Odoo
sudo systemctl start odoo

# Wait for recovery (5 minutes)
# Circuit breaker should transition to half_open, then closed
```

### Test 5: Audit Logging

```bash
# Check audit logs
cat obsidian-vault/Audit_Logs/$(date +%Y-%m-%d).md

# Expected: All actions logged with timestamps, parameters, results
```

---

## Usage

### Manual Operations

#### Record Transaction Manually

```bash
python -c "
from mcp_servers.digital_fte_server.tools.odoo_record_transaction import odoo_record_transaction
result = odoo_record_transaction(
    amount=150.00,
    date='2026-03-31T10:00:00Z',
    description='Consulting services',
    account_code='400',
    move_type='invoice'
)
print(result)
"
```

#### Post to Social Media

```bash
python -c "
from mcp_servers.digital_fte_server.tools.social_post import social_post
result = social_post(
    content='Exciting announcement!',
    platforms=['facebook', 'instagram', 'twitter'],
    media_urls=['https://example.com/image.jpg']
)
print(result)
"
```

#### Generate Briefing On-Demand

```bash
python -c "
from mcp_servers.digital_fte_server.tools.generate_briefing import generate_briefing
result = generate_briefing()
print(result)
"
```

#### Check Integration Health

```bash
python watchers/shared/health_aggregator.py

# Expected output:
# Odoo: healthy (circuit breaker: closed)
# Facebook: healthy (circuit breaker: closed)
# Instagram: healthy (circuit breaker: closed)
# Twitter: healthy (circuit breaker: closed)
```

---

## Troubleshooting

### Odoo Connection Issues

**Problem**: "Connection refused" error

**Solution**:
1. Verify Odoo is running: `curl http://localhost:8069`
2. Check firewall settings
3. Verify credentials in keychain: `python watchers/shared/keychain.py --list`

**Problem**: "Authentication failed"

**Solution**:
1. Verify username/password in Odoo web interface
2. Re-run credential setup: `python watchers/setup_credentials.py --service odoo`
3. Check Odoo user has API access enabled

### Social Media API Issues

**Problem**: "Invalid access token"

**Solution**:
1. Regenerate access token in developer portal
2. For Facebook: Convert to long-lived token or use page access token
3. Update credentials: `python watchers/setup_credentials.py --service facebook`

**Problem**: "Rate limit exceeded"

**Solution**:
1. Check current rate limit status: `python watchers/social_media_watcher/check_limits.py`
2. Wait for rate limit reset (shown in error message)
3. Reduce posting frequency in config

### CEO Briefing Not Generating

**Problem**: Briefing not created on Monday morning

**Solution**:
1. Check briefing watcher is running: `ps aux | grep briefing_watcher`
2. Check logs: `cat watchers/briefing_watcher/watcher.log`
3. Verify schedule config: `cat watchers/briefing_watcher/config.py`
4. Test manual generation: `python -c "from mcp_servers.digital_fte_server.tools.generate_briefing import generate_briefing; generate_briefing()"`

### Circuit Breaker Stuck Open

**Problem**: Integration shows "offline" but service is healthy

**Solution**:
1. Check integration status: `sqlite3 watchers/shared/integration_status.db "SELECT * FROM integration_status;"`
2. Manually reset circuit breaker: `python watchers/shared/reset_circuit_breaker.py --integration odoo`
3. Verify service health: `python watchers/odoo_watcher/test_connection.py`

---

## Monitoring

### Daily Health Check

```bash
# Run daily health check script
python scripts/daily_health_check.py

# Checks:
# - All watchers running
# - All integrations healthy
# - No circuit breakers open
# - Audit logs being written
# - Disk space sufficient
```

### View Audit Logs

```bash
# Today's audit log
cat obsidian-vault/Audit_Logs/$(date +%Y-%m-%d).md

# Query audit database
sqlite3 obsidian-vault/Audit_Logs/audit.db "
SELECT timestamp, action_type, action_name, result 
FROM audit_log 
WHERE date(timestamp) = date('now') 
ORDER BY timestamp DESC 
LIMIT 20;
"
```

### View Integration Status

```bash
# Check all integration statuses
sqlite3 watchers/shared/integration_status.db "
SELECT 
    integration_name,
    status,
    circuit_breaker_state,
    error_rate,
    last_success_at,
    last_failure_at
FROM integration_status;
"
```

---

## Security Best Practices

1. **Never commit credentials**: All credentials stored in OS keychain only
2. **Rotate API tokens**: Rotate every 90 days per constitution
3. **Review audit logs**: Check weekly for suspicious activity
4. **Limit API permissions**: Use minimum required permissions for each service
5. **Monitor rate limits**: Stay well below platform limits to avoid bans
6. **Backup Obsidian vault**: Regular backups of vault (contains all data)
7. **Encrypt sensitive data**: Financial data encrypted at rest (AES-256)

---

## Next Steps

1. ✅ Gold Tier setup complete
2. ⏭️ Monitor for one week to verify all integrations working
3. ⏭️ Review first CEO briefing on Monday morning
4. ⏭️ Adjust categorization rules based on your business
5. ⏭️ Customize social media posting schedule
6. ⏭️ Train agent on your specific workflows

---

## Support

- **Documentation**: See `specs/001-gold-tier-autonomous/` for detailed specs
- **Issues**: Report at https://github.com/anthropics/claude-code/issues
- **Constitution**: `.specify/memory/constitution.md` for principles and constraints

**Gold Tier Status**: 🟢 Operational - Autonomous Employee Ready
