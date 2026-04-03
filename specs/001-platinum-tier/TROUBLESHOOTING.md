# Platinum Tier Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues with the Platinum Tier Digital FTE system.

**Quick Links**:
- [Cloud Agent Issues](#cloud-agent-issues)
- [Local Agent Issues](#local-agent-issues)
- [Vault Sync Issues](#vault-sync-issues)
- [Odoo Issues](#odoo-issues)
- [Health Monitoring Issues](#health-monitoring-issues)
- [Performance Issues](#performance-issues)

---

## Cloud Agent Issues

### Cloud Agent Won't Start

**Symptoms**: `systemctl status cloud-agent.service` shows failed or inactive

**Diagnosis**:
```bash
# Check service logs
sudo journalctl -u cloud-agent.service -n 100 --no-pager

# Check for Python errors
sudo journalctl -u cloud-agent.service | grep -i error

# Verify configuration
cat /opt/digital-fte/obsidian-vault/config/agent-config.json
```

**Common Causes**:

1. **Missing credentials**
   - Check `.env.cloud` exists and has all required variables
   - Verify credentials are read-only (not full access)
   - Test credentials manually: `python -c "import os; print(os.getenv('GMAIL_CLIENT_ID'))"`

2. **Invalid vault path**
   - Verify path in agent-config.json: `/opt/digital-fte/obsidian-vault`
   - Check directory exists: `ls -la /opt/digital-fte/obsidian-vault`
   - Verify permissions: `ls -ld /opt/digital-fte/obsidian-vault`

3. **Python dependencies missing**
   - Reinstall: `cd /opt/digital-fte && bash cloud/deployment/install_dependencies.sh`
   - Check uv: `uv --version`

4. **Port conflict**
   - Check if port 8080 is in use: `sudo netstat -tulpn | grep 8080`
   - Kill conflicting process or change port in config

**Resolution**:
```bash
# Fix permissions
sudo chown -R digital-fte:digital-fte /opt/digital-fte

# Restart service
sudo systemctl restart cloud-agent.service

# Monitor startup
sudo journalctl -u cloud-agent.service -f
```

### Cloud Agent Crashes Repeatedly

**Symptoms**: Service starts but crashes within minutes, Monit keeps restarting it

**Diagnosis**:
```bash
# Check crash logs
sudo journalctl -u cloud-agent.service | grep -A 10 "Traceback"

# Check memory usage
free -h
ps aux | grep cloud_agent

# Check disk space
df -h
```

**Common Causes**:

1. **Memory exhaustion**
   - Cloud agent using >2GB RAM
   - Check systemd limits: `systemctl show cloud-agent.service | grep Memory`
   - Increase VM RAM or reduce worker count

2. **API rate limiting**
   - Gmail API: 250 quota units/user/second
   - Social media APIs: varies by platform
   - Check API error messages in logs

3. **Vault sync conflicts**
   - Git merge conflicts causing crashes
   - Check: `cd /opt/digital-fte/obsidian-vault && git status`

**Resolution**:
```bash
# Increase memory limit (if VM has capacity)
sudo systemctl edit cloud-agent.service
# Add: [Service]
#      MemoryLimit=4G

# Reduce watcher frequency (if rate limited)
# Edit cloud/agent/cloud_agent.py, change sleep(300) to sleep(600)

# Resolve git conflicts
cd /opt/digital-fte/obsidian-vault
git status
# Manually resolve conflicts, then:
git add .
git commit -m "Resolve conflicts"
```

### Watchers Not Detecting Events

**Symptoms**: No drafts being generated despite new emails/posts

**Diagnosis**:
```bash
# Check watcher logs
sudo journalctl -u cloud-agent.service | grep -i watcher

# Verify credentials work
# Test Gmail API manually
python3 << EOF
from cloud.watchers.gmail_watcher_cloud import GmailWatcherCloud
# ... test code
EOF
```

**Common Causes**:

1. **Expired OAuth tokens**
   - Gmail/social media tokens expire
   - Refresh tokens in `.env.cloud`

2. **API permissions insufficient**
   - Gmail: needs `gmail.readonly` scope
   - Social: needs read permissions

3. **Watcher cycle too slow**
   - 5-minute cycle may miss time-sensitive events
   - Consider reducing to 2-3 minutes

**Resolution**:
```bash
# Refresh OAuth tokens
# Use OAuth playground or provider's token refresh endpoint

# Test watcher manually
cd /opt/digital-fte
python3 -c "
from cloud.watchers.gmail_watcher_cloud import GmailWatcherCloud
from cloud.agent.credential_manager import CredentialManager
# ... test watcher
"
```

---

## Local Agent Issues

### Local Agent Not Processing Approvals

**Symptoms**: Drafts appear in vault but Dashboard.md not updated

**Diagnosis**:
```powershell
# Check local agent logs (Windows)
# If running in terminal, check output

# Verify vault sync
cd obsidian-vault
git status
git log -5

# Check Dashboard.md
cat Dashboard.md
```

**Common Causes**:

1. **Vault not syncing**
   - Local git pull failing
   - Check: `git pull` manually

2. **Dashboard merge conflicts**
   - Cloud and local both writing to Dashboard.md
   - Check: `git status` for conflicts

3. **Approval processor error**
   - Python exception in approval scanning
   - Check local agent output for errors

**Resolution**:
```powershell
# Force vault sync
cd obsidian-vault
git fetch origin
git reset --hard origin/master

# Restart local agent
# Ctrl+C to stop, then restart
python local/local_agent.py obsidian-vault
```

### Approved Actions Not Executing

**Symptoms**: Approvals marked in Dashboard.md but emails not sent

**Diagnosis**:
```powershell
# Check local agent logs for MCP errors
# Look for "Executing approved actions" messages

# Verify full credentials exist
cat .env.local

# Test MCP server manually
# (if MCP servers implemented)
```

**Common Causes**:

1. **Missing full credentials**
   - Local agent needs write access
   - Verify `.env.local` has full OAuth tokens

2. **MCP server not running**
   - Check if MCP servers are started
   - Verify MCP server ports

3. **Rate limiting**
   - Gmail: 100 emails/day for free accounts
   - Social: varies by platform

**Resolution**:
```powershell
# Update credentials
# Edit .env.local with full access tokens

# Test email sending manually
python -c "
# Test Gmail send API
"

# Check rate limits
# Review API quotas in provider dashboards
```

---

## Vault Sync Issues

### Sync Lag Exceeds 5 Minutes

**Symptoms**: Monit alerts "vault-sync-status lag >5 minutes"

**Diagnosis**:
```bash
# Check sync status
cat /opt/digital-fte/obsidian-vault/.sync-status/cloud.json

# Check git sync logs
sudo journalctl -u vault-sync.service -n 50

# Check network connectivity
ping github.com
```

**Common Causes**:

1. **Git authentication failure**
   - SSH key expired or revoked
   - Personal access token expired
   - Check: `git pull` manually

2. **Large file blocking sync**
   - Binary files or large attachments
   - Check: `git status` for large files

3. **Network issues**
   - Slow connection to git remote
   - Firewall blocking git port (22 or 443)

**Resolution**:
```bash
# Regenerate SSH key
ssh-keygen -t ed25519 -C "cloud-agent@digital-fte"
# Add to GitHub/GitLab

# Or use personal access token
git remote set-url origin https://TOKEN@github.com/your-org/vault.git

# Remove large files
cd /opt/digital-fte/obsidian-vault
git rm --cached large-file.bin
echo "large-file.bin" >> .gitignore
git commit -m "Remove large file"
```

### Merge Conflicts Every Sync

**Symptoms**: Git status shows conflicts, sync fails repeatedly

**Diagnosis**:
```bash
cd /opt/digital-fte/obsidian-vault
git status
git log --oneline --graph -10
```

**Common Causes**:

1. **Both agents writing to same file**
   - Violates single-writer rule (FR-013)
   - Dashboard.md should only be written by local agent
   - Check: which agent is writing to conflicting file

2. **Clock skew between agents**
   - Lamport timestamps should handle this
   - Check: system time on both machines

3. **Sync frequency too high**
   - 30-second sync may cause race conditions
   - Consider increasing to 60 seconds

**Resolution**:
```bash
# Resolve conflicts manually
cd /opt/digital-fte/obsidian-vault
git status
# Edit conflicting files
git add .
git commit -m "Resolve conflicts"

# Verify single-writer rule
# Ensure cloud agent only writes to:
# - In_Progress/cloud/
# - Pending_Approval/
# - Updates/

# Ensure local agent only writes to:
# - Dashboard.md
# - In_Progress/local/
```

---

## Odoo Issues

### Odoo Not Accessible via HTTPS

**Symptoms**: `curl https://your-domain.com/web/health` fails

**Diagnosis**:
```bash
# Check Odoo service
sudo systemctl status odoo.service

# Check nginx
sudo systemctl status nginx
sudo nginx -t

# Check SSL certificate
sudo certbot certificates

# Check DNS
nslookup your-domain.com
```

**Common Causes**:

1. **SSL certificate not issued**
   - Let's Encrypt validation failed
   - Check: `sudo certbot certificates`

2. **Nginx misconfigured**
   - Proxy pass incorrect
   - Check: `sudo nginx -t`

3. **Firewall blocking ports**
   - Ports 80, 443 not open
   - Check: `sudo ufw status`

**Resolution**:
```bash
# Reissue SSL certificate
sudo certbot --nginx -d your-domain.com

# Fix nginx config
sudo nano /etc/nginx/sites-available/odoo
# Verify proxy_pass http://localhost:8069

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# Open firewall ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Odoo Performance Degraded

**Symptoms**: Slow response times, health checks timing out

**Diagnosis**:
```bash
# Check Odoo resource usage
ps aux | grep odoo
top -p $(pgrep -f odoo)

# Check PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check disk I/O
iostat -x 1 5
```

**Common Causes**:

1. **Insufficient workers**
   - Default 2 workers may be too few
   - Check: `/etc/odoo/odoo.conf` workers setting

2. **Database not optimized**
   - Missing indexes
   - Needs VACUUM
   - Check: PostgreSQL slow query log

3. **Memory exhaustion**
   - Odoo using >2GB RAM
   - Check: `free -h`

**Resolution**:
```bash
# Increase workers (if RAM available)
sudo nano /etc/odoo/odoo.conf
# Set: workers = 4

# Optimize PostgreSQL
sudo -u postgres psql odoo -c "VACUUM ANALYZE;"

# Restart Odoo
sudo systemctl restart odoo.service
```

---

## Health Monitoring Issues

### Monit Not Sending Alerts

**Symptoms**: Services failing but no SMS/email/push alerts received

**Diagnosis**:
```bash
# Check Monit status
sudo monit status

# Test alert script manually
sudo /opt/digital-fte/alert.sh cloud-agent test "Test alert"

# Check alert config
cat /opt/digital-fte/.alert-config

# Check Monit logs
sudo journalctl -u monit -n 50
```

**Common Causes**:

1. **Alert channels disabled**
   - Check: `ENABLE_SMS=false` in config
   - Enable desired channels

2. **Invalid credentials**
   - Twilio: wrong account SID or auth token
   - Pushover: wrong app token or user key
   - Test credentials manually

3. **Alert throttling**
   - 5-minute minimum between alerts
   - Check: last alert time in logs

**Resolution**:
```bash
# Enable alert channels
sudo nano /opt/digital-fte/.alert-config
# Set: ENABLE_SMS=true, ENABLE_PUSH=true

# Test Twilio manually
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=$TWILIO_FROM_NUMBER" \
  --data-urlencode "To=$TWILIO_TO_NUMBER" \
  --data-urlencode "Body=Test" \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN"

# Reload Monit
sudo monit reload
```

### False Positive Health Checks

**Symptoms**: Monit constantly restarting healthy services

**Diagnosis**:
```bash
# Check health check results
sudo monit status

# Check service logs for actual errors
sudo journalctl -u cloud-agent.service -n 100

# Check health endpoint manually
curl http://localhost:8080/health
```

**Common Causes**:

1. **Health check timeout too short**
   - 10-second timeout may be insufficient
   - Increase in monitrc

2. **Service slow to start**
   - Health endpoint not ready immediately
   - Add startup delay

3. **Transient network issues**
   - Temporary connectivity problems
   - Increase failure threshold

**Resolution**:
```bash
# Adjust Monit thresholds
sudo nano /etc/monit/conf.d/digital-fte.conf
# Change: for 2 cycles -> for 3 cycles
# Change: timeout 10 seconds -> timeout 20 seconds

# Reload Monit
sudo monit reload
```

---

## Performance Issues

### High CPU Usage

**Symptoms**: CPU constantly >80%, system sluggish

**Diagnosis**:
```bash
# Identify CPU hog
top
htop

# Check specific processes
ps aux | grep -E "cloud_agent|odoo|python"
```

**Common Causes**:

1. **Watcher cycle too frequent**
   - 5-minute cycle may be too aggressive
   - Increase to 10 minutes

2. **Odoo workers too many**
   - Each worker uses CPU
   - Reduce worker count

3. **Git sync too frequent**
   - 30-second sync may be excessive
   - Increase to 60 seconds

**Resolution**:
```bash
# Reduce watcher frequency
# Edit cloud/agent/cloud_agent.py
# Change: await asyncio.sleep(300) -> await asyncio.sleep(600)

# Reduce Odoo workers
sudo nano /etc/odoo/odoo.conf
# Set: workers = 2

# Reduce sync frequency
sudo nano /etc/systemd/system/vault-sync.timer
# Change: OnUnitActiveSec=30s -> OnUnitActiveSec=60s

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart cloud-agent.service odoo.service vault-sync.timer
```

### High Memory Usage

**Symptoms**: Memory >90%, OOM killer activating

**Diagnosis**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check OOM killer logs
dmesg | grep -i "out of memory"
```

**Common Causes**:

1. **Memory leak in agent**
   - Python objects not garbage collected
   - Restart agent periodically

2. **Too many concurrent operations**
   - Reduce parallelism

3. **Large vault files**
   - Binary files in vault
   - Check: `du -sh /opt/digital-fte/obsidian-vault/*`

**Resolution**:
```bash
# Add periodic restart to cloud agent
sudo systemctl edit cloud-agent.service
# Add: [Service]
#      RuntimeMaxSec=86400  # Restart daily

# Reduce memory limits
sudo systemctl edit odoo.service
# Add: [Service]
#      MemoryLimit=1G

# Clean up large files
cd /opt/digital-fte/obsidian-vault
find . -type f -size +10M
# Remove or move large files
```

---

## Emergency Procedures

### Complete System Failure

If all services are down:

1. **Stop all services**
   ```bash
   sudo systemctl stop cloud-agent.service odoo.service vault-sync.timer monit
   ```

2. **Check system resources**
   ```bash
   df -h  # Disk space
   free -h  # Memory
   top  # CPU
   ```

3. **Review logs**
   ```bash
   sudo journalctl -xe | tail -100
   ```

4. **Restart services one by one**
   ```bash
   sudo systemctl start vault-sync.timer
   # Wait 2 minutes, verify sync working
   
   sudo systemctl start cloud-agent.service
   # Wait 5 minutes, verify agent running
   
   sudo systemctl start odoo.service
   # Wait 2 minutes, verify Odoo accessible
   
   sudo systemctl start monit
   ```

### Data Recovery

If vault data is corrupted:

1. **Stop all agents**
2. **Restore from git history**
   ```bash
   cd /opt/digital-fte/obsidian-vault
   git reflog
   git reset --hard HEAD@{5}  # Go back 5 commits
   ```

3. **Or restore from backup**
   ```bash
   # If using vault backups
   cp -r /backups/vault/2026-04-03/ /opt/digital-fte/obsidian-vault/
   ```

---

## Getting Help

If issues persist:

1. **Collect diagnostic information**
   ```bash
   # Run diagnostic script
   bash cloud/deployment/diagnose.sh > diagnostic-report.txt
   ```

2. **Check documentation**
   - DEPLOYMENT.md for setup issues
   - spec.md for feature requirements
   - constitution.md for design principles

3. **Review logs systematically**
   - Cloud agent: `sudo journalctl -u cloud-agent.service -n 500`
   - Vault sync: `sudo journalctl -u vault-sync.service -n 500`
   - Odoo: `sudo journalctl -u odoo.service -n 500`
   - Monit: `sudo journalctl -u monit -n 500`

4. **Create GitHub issue** with:
   - Symptom description
   - Diagnostic report
   - Relevant log excerpts
   - Steps to reproduce
