# Watcher Status Agent Skill

**Purpose**: Monitor health and status of all Digital FTE watchers

**Version**: 1.0.0

**Category**: System Monitoring

---

## Description

This skill enables users to check the health status of all watchers (Gmail, WhatsApp, LinkedIn) and diagnose issues. It provides real-time status information, last check timestamps, and actionable troubleshooting steps.

---

## Commands

### check-status

Check health status of all watchers.

**Usage:**
```
claude-code "Check watcher status"
```

**Output:**
```
Watcher Health Status:

[PASS] gmail_watcher
  Last check: 2026-03-31 10:30:00 UTC (2 minutes ago)
  Status: healthy
  Events processed: 145

[FAIL] whatsapp_watcher
  Last check: 2026-03-31 09:15:00 UTC (1 hour ago)
  Status: unhealthy
  Error: Connection timeout
  Action: Restart watcher with: python watchers/whatsapp_watcher/watcher.py

[PASS] linkedin_watcher
  Last check: 2026-03-31 10:28:00 UTC (4 minutes ago)
  Status: healthy
  Events processed: 23

Overall Status: DEGRADED (1/3 watchers unhealthy)
```

---

### check-watcher

Check status of a specific watcher.

**Usage:**
```
claude-code "Check status of [watcher-name]"
```

**Parameters:**
- `watcher_name`: gmail_watcher, whatsapp_watcher, or linkedin_watcher

**Example:**
```
claude-code "Check status of gmail_watcher"

# Output:
# [PASS] gmail_watcher
# Last check: 2026-03-31 10:30:00 UTC
# Status: healthy
# Uptime: 99.8%
# Events today: 45
# Last event: 2026-03-31 10:25:00 UTC
```

---

### restart-watcher

Restart a specific watcher.

**Usage:**
```
claude-code "Restart [watcher-name]"
```

**Example:**
```
claude-code "Restart whatsapp_watcher"

# Stopping whatsapp_watcher...
# Starting whatsapp_watcher...
# [PASS] Watcher restarted successfully
```

---

### restart-all

Restart all watchers.

**Usage:**
```
claude-code "Restart all watchers"
```

**Example:**
```
claude-code "Restart all watchers"

# Restarting all watchers...
# [PASS] gmail_watcher restarted
# [PASS] whatsapp_watcher restarted
# [PASS] linkedin_watcher restarted
# All watchers running
```

---

### view-logs

View recent logs for a watcher.

**Usage:**
```
claude-code "Show logs for [watcher-name]"
```

**Example:**
```
claude-code "Show logs for gmail_watcher"

# Recent logs (last 20 lines):
# 2026-03-31 10:30:15 [INFO] Polling Gmail API...
# 2026-03-31 10:30:16 [INFO] Found 3 new messages
# 2026-03-31 10:30:17 [INFO] Processing message: "Project update"
# 2026-03-31 10:30:18 [INFO] Created vault note: inbox/project-update.md
```

---

## Health Status Levels

### Healthy
- Last check within 5 minutes
- No errors reported
- Watcher process running
- API connections working

### Degraded
- Last check within 15 minutes
- Minor errors (rate limiting, temporary network issues)
- Watcher process running but struggling
- Some API calls failing

### Unhealthy
- Last check more than 15 minutes ago
- Critical errors (authentication failure, crash)
- Watcher process not running
- API connections down

---

## Watcher Details

### Gmail Watcher
- **Purpose**: Monitor Gmail inbox for new messages
- **Polling interval**: 60 seconds
- **Health check**: Every 5 minutes
- **Common issues**:
  - OAuth token expired → Re-authenticate with `python watchers/gmail_watcher/auth.py`
  - Rate limit exceeded → Increase polling interval
  - Network timeout → Check internet connection

### WhatsApp Watcher
- **Purpose**: Monitor WhatsApp messages via bridge
- **Polling interval**: 30 seconds
- **Health check**: Every 5 minutes
- **Common issues**:
  - QR code expired → Restart bridge and scan QR code
  - Bridge not running → Start with `node watchers/whatsapp_watcher/bridge.js`
  - Session disconnected → Delete session and re-authenticate

### LinkedIn Watcher
- **Purpose**: Monitor LinkedIn notifications and messages
- **Polling interval**: 120 seconds
- **Health check**: Every 5 minutes
- **Common issues**:
  - Session cookies expired → Re-authenticate
  - Rate limit exceeded → Increase polling interval
  - Account locked → Check LinkedIn account status

---

## Troubleshooting

### Watcher Not Running

**Symptoms:**
- Status shows "unhealthy"
- Last check more than 15 minutes ago
- No recent events

**Solution:**
```bash
# Check if process is running
ps aux | grep watcher

# Restart watcher
python watchers/[watcher-name]/watcher.py

# Or use agent skill
claude-code "Restart [watcher-name]"
```

---

### Authentication Errors

**Symptoms:**
- Error: "401 Unauthorized"
- Error: "Invalid credentials"
- Error: "Token expired"

**Solution:**
```bash
# Gmail: Re-authenticate
python watchers/gmail_watcher/auth.py

# WhatsApp: Restart bridge and scan QR
node watchers/whatsapp_watcher/bridge.js

# LinkedIn: Update session cookies
python watchers/linkedin_watcher/auth.py
```

---

### Rate Limiting

**Symptoms:**
- Error: "429 Too Many Requests"
- Error: "Rate limit exceeded"
- Degraded status

**Solution:**
```bash
# Increase polling interval in watcher config
# Gmail: 60s → 120s
# WhatsApp: 30s → 60s
# LinkedIn: 120s → 300s

# Or temporarily pause watcher
claude-code "Pause [watcher-name]"
```

---

### Network Issues

**Symptoms:**
- Error: "Connection timeout"
- Error: "Network unreachable"
- Intermittent failures

**Solution:**
```bash
# Check internet connection
ping google.com

# Check API endpoints
curl https://gmail.googleapis.com
curl https://api.linkedin.com

# Restart watcher with retry logic
claude-code "Restart [watcher-name]"
```

---

## Health Check Database

Watcher health is stored in SQLite database:

**Location:** `watchers/shared/digital_fte.db`

**Table:** `watcher_health`

**Schema:**
```sql
CREATE TABLE watcher_health (
    watcher_name TEXT PRIMARY KEY,
    status TEXT,
    last_check_timestamp TEXT,
    error_message TEXT,
    events_processed INTEGER
);
```

**Query health:**
```bash
sqlite3 watchers/shared/digital_fte.db "SELECT * FROM watcher_health;"
```

---

## Monitoring Best Practices

1. **Check status daily**: Run `claude-code "Check watcher status"` each morning
2. **Set up alerts**: Configure notifications for unhealthy watchers
3. **Monitor logs**: Review logs weekly for patterns
4. **Update credentials**: Refresh OAuth tokens before expiry
5. **Test after changes**: Verify watchers after config changes
6. **Keep dependencies updated**: Update Python packages regularly

---

## Integration with Dashboard

Watcher status is displayed on the Obsidian Dashboard:

**Location:** `obsidian-vault/Dashboard.md`

**Auto-updated:** Every 5 minutes

**Example:**
```markdown
## System Status

### Watchers
- ✓ Gmail: Healthy (last check: 2 min ago)
- ✗ WhatsApp: Unhealthy (last check: 1 hour ago)
- ✓ LinkedIn: Healthy (last check: 4 min ago)

Overall: DEGRADED
```

---

## Automated Health Checks

Health checks run automatically:

**Frequency:** Every 5 minutes

**Script:** `watchers/shared/health_check.py`

**Cron job:**
```bash
*/5 * * * * python watchers/shared/health_check.py
```

**Manual run:**
```bash
python watchers/shared/health_check.py
```

---

## Error Handling

### Graceful Degradation
- If one watcher fails, others continue running
- Events are queued and processed when watcher recovers
- No data loss during temporary outages

### Automatic Recovery
- Watchers retry failed operations with exponential backoff
- Authentication tokens auto-refresh when possible
- Network errors trigger automatic reconnection

### Alerting
- Critical errors logged to `watchers/logs/`
- Unhealthy status triggers dashboard alert
- Email notification for prolonged outages (optional)

---

## Examples

### Example 1: Morning Health Check

```bash
# Check all watchers
claude-code "Check watcher status"

# Output shows all healthy
# [PASS] All watchers healthy

# Continue with day
```

### Example 2: Troubleshoot Unhealthy Watcher

```bash
# Check status
claude-code "Check watcher status"

# Output shows WhatsApp unhealthy
# [FAIL] whatsapp_watcher - Connection timeout

# View logs
claude-code "Show logs for whatsapp_watcher"

# See error: "Bridge not running"

# Restart bridge
node watchers/whatsapp_watcher/bridge.js

# Verify fixed
claude-code "Check status of whatsapp_watcher"

# [PASS] whatsapp_watcher healthy
```

### Example 3: Restart All After System Reboot

```bash
# After system restart, watchers not running

# Check status
claude-code "Check watcher status"

# All show unhealthy

# Restart all
claude-code "Restart all watchers"

# Verify
claude-code "Check watcher status"

# All healthy
```

---

## Notes

- Health checks use UTC timestamps
- Status updates every 5 minutes
- Logs rotated daily (kept for 30 days)
- Database backed up daily
- Watcher processes run as daemons
- Restart required after config changes
