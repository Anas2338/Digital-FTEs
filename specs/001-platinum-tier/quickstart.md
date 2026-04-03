# Quickstart Guide: Platinum Tier Deployment

**Feature**: Platinum Tier - Always-On Cloud + Local Executive  
**Date**: 2026-04-03  
**Estimated Time**: 4-6 hours for complete setup

## Overview

This guide walks you through deploying the Platinum Tier dual-agent architecture: a cloud agent running 24/7 for continuous monitoring and draft generation, and a local agent maintaining control over approvals and sensitive operations.

**Prerequisites**:
- ✅ Gold Tier fully functional (autonomous employee with Odoo, social media, CEO briefing)
- ✅ Cloud VM access (Oracle Cloud Free Tier, AWS, or equivalent) - 2 CPU, 4GB RAM minimum
- ✅ GitHub/GitLab account for vault synchronization (or self-hosted Git server)
- ✅ Basic Linux command-line skills (SSH, systemd, nginx)

---

## Phase 1: Cloud VM Setup (60 minutes)

### 1.1 Provision Cloud VM

**Oracle Cloud Free Tier** (recommended for cost):
```bash
# VM.Standard.E2.1.Micro: 1 CPU, 1GB RAM (upgrade to 2 CPU, 4GB if available)
# Ubuntu 22.04 LTS
# Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8069 (Odoo)
```

**AWS EC2 Alternative**:
```bash
# t3.medium: 2 CPU, 4GB RAM
# Ubuntu 22.04 LTS AMI
# Security group: Allow 22, 80, 443, 8069
```

### 1.2 Initial Server Configuration

SSH into your VM:
```bash
ssh ubuntu@<your-vm-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl wget build-essential python3.11 python3.11-venv \
  python3-pip nginx certbot python3-certbot-nginx postgresql postgresql-contrib \
  monit

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 1.3 Create Dedicated User

```bash
# Create cloudagent user
sudo useradd -r -m -s /bin/bash cloudagent
sudo mkdir -p /opt/cloud-agent
sudo chown -R cloudagent:cloudagent /opt/cloud-agent
```

### 1.4 Configure Firewall

```bash
# UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8069/tcp  # Odoo
sudo ufw enable
```

---

## Phase 2: Vault Synchronization Setup (45 minutes)

### 2.1 Create Git Repository

**Option A: GitHub Private Repository**
```bash
# On your local machine
cd /path/to/obsidian-vault
git init
git add .
git commit -m "Initial vault commit"

# Create private repo on GitHub, then:
git remote add origin git@github.com:yourusername/vault-private.git
git push -u origin master
```

**Option B: Self-Hosted Gitea** (if privacy-critical):
```bash
# Install Gitea on cloud VM or separate server
# Follow: https://docs.gitea.io/en-us/install-from-binary/
```

### 2.2 Configure SSH Keys

**On Cloud VM**:
```bash
sudo -u cloudagent ssh-keygen -t ed25519 -C "cloudagent@vm"
sudo cat /home/cloudagent/.ssh/id_ed25519.pub
# Add this public key to GitHub/GitLab deploy keys (read-only)
```

**On Local Machine**:
```bash
ssh-keygen -t ed25519 -C "local@machine"
cat ~/.ssh/id_ed25519.pub
# Add this public key to GitHub/GitLab deploy keys (read-write)
```

### 2.3 Clone Vault on Cloud VM

```bash
sudo -u cloudagent bash
cd /opt/cloud-agent
git clone git@github.com:yourusername/vault-private.git obsidian-vault
cd obsidian-vault

# Create coordination directories
mkdir -p In_Progress/{cloud,local} Pending_Approval/{email,social,accounting} Updates .sync-status

# Create .gitignore for secrets
cat > .gitignore << 'EOF'
.env
*.env
.env.*
*.session
credentials.json
tokens/
.obsidian/workspace*
EOF

git add .
git commit -m "Add Platinum Tier coordination directories"
git push
```

### 2.4 Setup Sync Script

```bash
# Create sync script
sudo -u cloudagent tee /opt/cloud-agent/sync-vault.sh > /dev/null << 'EOF'
#!/bin/bash
set -e
cd /opt/obsidian-vault

# Pull changes
git pull --rebase --autostash || exit 1

# Commit local changes
git add -A
git commit -m "Cloud agent sync $(date +%s)" --allow-empty

# Push changes
git push || {
  # Push failed - another agent pushed first
  git reset HEAD~1
  exit 1
}
EOF

chmod +x /opt/cloud-agent/sync-vault.sh

# Create systemd timer for sync (every 30 seconds)
sudo tee /etc/systemd/system/vault-sync.timer > /dev/null << 'EOF'
[Unit]
Description=Vault Sync Timer

[Timer]
OnBootSec=30s
OnUnitActiveSec=30s

[Install]
WantedBy=timers.target
EOF

sudo tee /etc/systemd/system/vault-sync.service > /dev/null << 'EOF'
[Unit]
Description=Vault Sync Service

[Service]
Type=oneshot
User=cloudagent
ExecStart=/opt/cloud-agent/sync-vault.sh
EOF

sudo systemctl enable vault-sync.timer
sudo systemctl start vault-sync.timer
```

---

## Phase 3: Odoo Cloud Deployment (90 minutes)

### 3.1 Install PostgreSQL and Odoo

```bash
# Create Odoo database user
sudo -u postgres createuser -s odoo
sudo -u postgres psql -c "ALTER USER odoo WITH PASSWORD 'your-secure-password';"
sudo -u postgres createdb -O odoo odoo

# Install Odoo dependencies
sudo apt install -y python3-pip python3-dev libxml2-dev libxslt1-dev \
  libldap2-dev libsasl2-dev libjpeg-dev libpq-dev

# Download and install Odoo 17.0
wget https://nightly.odoo.com/17.0/nightly/deb/odoo_17.0.latest_all.deb
sudo dpkg -i odoo_17.0.latest_all.deb
sudo apt-get install -f  # Fix dependencies

# Configure Odoo
sudo tee /etc/odoo/odoo.conf > /dev/null << 'EOF'
[options]
admin_passwd = your-admin-password
db_host = localhost
db_port = 5432
db_user = odoo
db_password = your-secure-password
addons_path = /usr/lib/python3/dist-packages/odoo/addons
workers = 2
max_cron_threads = 1
EOF

# Start Odoo
sudo systemctl enable odoo
sudo systemctl start odoo
```

### 3.2 Configure Nginx Reverse Proxy with SSL

```bash
# Create nginx config
sudo tee /etc/nginx/sites-available/odoo > /dev/null << 'EOF'
upstream odoo {
    server 127.0.0.1:8069;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://odoo;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 3.3 Setup Automated Backups

```bash
# Create backup script
sudo tee /etc/cron.daily/odoo-backup > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/odoo"
mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump odoo | gzip > $BACKUP_DIR/odoo-$(date +%Y%m%d).sql.gz

# Backup filestore
tar -czf $BACKUP_DIR/filestore-$(date +%Y%m%d).tar.gz /var/lib/odoo/filestore

# Retain 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
EOF

sudo chmod +x /etc/cron.daily/odoo-backup
```

---

## Phase 4: Cloud Agent Deployment (60 minutes)

### 4.1 Copy Agent Code to Cloud VM

**On your local machine**:
```bash
# Package cloud agent code
cd /path/to/Digital-FTEs
tar -czf cloud-agent.tar.gz cloud/ watchers/ coordination/ sync/ \
  --exclude='*.pyc' --exclude='__pycache__' --exclude='.venv'

# Copy to cloud VM
scp cloud-agent.tar.gz ubuntu@<vm-ip>:/tmp/
```

**On cloud VM**:
```bash
sudo -u cloudagent bash
cd /opt/cloud-agent
tar -xzf /tmp/cloud-agent.tar.gz

# Install dependencies with uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 4.2 Configure Cloud Agent

```bash
# Create read-only credentials file
sudo -u cloudagent tee /opt/cloud-agent/.env.cloud > /dev/null << 'EOF'
# Cloud agent - READ-ONLY credentials
AGENT_ID=cloud
AGENT_TYPE=cloud
LLM_PROVIDER=claude
CREDENTIAL_SCOPE=read_only

# Gmail (read-only)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token

# Social media (read-only monitoring)
FACEBOOK_ACCESS_TOKEN=your-read-token
INSTAGRAM_ACCESS_TOKEN=your-read-token
TWITTER_API_KEY=your-api-key

# Odoo (read-only)
ODOO_URL=https://your-domain.com
ODOO_DB=odoo
ODOO_USERNAME=readonly_user
ODOO_PASSWORD=readonly_password

# Vault sync
VAULT_PATH=/opt/cloud-agent/obsidian-vault
SYNC_METHOD=git
SYNC_INTERVAL=30
EOF

chmod 600 /opt/cloud-agent/.env.cloud
```

### 4.3 Create Systemd Service

```bash
sudo tee /etc/systemd/system/cloud-agent.service > /dev/null << 'EOF'
[Unit]
Description=Cloud Agent - Autonomous Python Service
After=network-online.target vault-sync.timer
Wants=network-online.target

[Service]
Type=simple
User=cloudagent
Group=cloudagent
WorkingDirectory=/opt/cloud-agent
ExecStart=/opt/cloud-agent/.venv/bin/python -u /opt/cloud-agent/cloud/agent/cloud_agent.py

Restart=on-failure
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=300

KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloud-agent

MemoryMax=512M
MemoryHigh=400M
CPUQuota=50%
TasksMax=100

PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/cloud-agent/data /opt/cloud-agent/obsidian-vault
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cloud-agent
sudo systemctl start cloud-agent
```

---

## Phase 5: Health Monitoring Setup (45 minutes)

### 5.1 Configure Monit

```bash
# Configure Monit
sudo tee /etc/monit/monitrc > /dev/null << 'EOF'
set daemon 300  # Check every 5 minutes
set log /var/log/monit.log

# Email alerts
set mailserver smtp.gmail.com port 587
    username "your-email@gmail.com" password "your-app-password"
    using tlsv12

set alert your-email@gmail.com

# Cloud agent monitoring
check process cloud-agent with pidfile /var/run/cloud-agent.pid
  start program = "/usr/bin/systemctl start cloud-agent"
  stop program = "/usr/bin/systemctl stop cloud-agent"
  if failed host 127.0.0.1 port 8080 protocol http
    with timeout 10 seconds for 2 cycles
    then restart
  if 3 restarts within 5 cycles then exec "/usr/local/bin/alert.sh"

# Vault sync monitoring
check file vault_sync with path /opt/cloud-agent/obsidian-vault/.git/FETCH_HEAD
  if timestamp > 15 minutes then alert

# Odoo monitoring
check host odoo with address 127.0.0.1
  if failed port 8069 protocol http
    request "/web/health"
    with timeout 10 seconds for 2 cycles
    then alert
EOF

sudo chmod 600 /etc/monit/monitrc
sudo systemctl enable monit
sudo systemctl start monit
```

### 5.2 Create Alert Script

```bash
# Create alert script for SMS/push
sudo tee /usr/local/bin/alert.sh > /dev/null << 'EOF'
#!/bin/bash
# Send SMS via Twilio
curl -X POST https://api.twilio.com/2010-04-01/Accounts/$TWILIO_SID/Messages.json \
  --data-urlencode "Body=$1" \
  --data-urlencode "From=$TWILIO_FROM" \
  --data-urlencode "To=$TWILIO_TO" \
  -u "$TWILIO_SID:$TWILIO_TOKEN"

# Send push via Pushover
curl -s -F "token=$PUSHOVER_TOKEN" \
  -F "user=$PUSHOVER_USER" \
  -F "message=$1" \
  https://api.pushover.net/1/messages.json
EOF

sudo chmod +x /usr/local/bin/alert.sh
```

---

## Phase 6: Local Agent Configuration (30 minutes)

### 6.1 Update Local Agent Config

**On your local machine**:
```bash
cd /path/to/Digital-FTEs

# Update local agent config
cat > obsidian-vault/config/local-agent-config.json << 'EOF'
{
  "agent_id": "local",
  "agent_type": "local",
  "llm_provider": "claude",
  "credential_scope": "full",
  "vault_path": "D:\\obsidian-vault",
  "sync_enabled": true,
  "sync_method": "git",
  "sync_interval_seconds": 30,
  "health_check_interval_seconds": 300
}
EOF

# Commit and push
git add .
git commit -m "Add local agent config"
git push
```

### 6.2 Enable Local Sync

```bash
# Create local sync script (Windows PowerShell)
$script = @'
cd D:\obsidian-vault
git pull --rebase --autostash
git add -A
git commit -m "Local agent sync $(Get-Date -Format 'yyyyMMddHHmmss')" --allow-empty
git push
'@

$script | Out-File -FilePath "C:\Scripts\sync-vault.ps1" -Encoding UTF8

# Create scheduled task (run every 30 seconds)
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Scripts\sync-vault.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Seconds 30)
Register-ScheduledTask -TaskName "VaultSync" -Action $action -Trigger $trigger
```

---

## Phase 7: Demo Scenario Walkthrough (15 minutes)

### 7.1 Trigger Test Email

```bash
# Send test email to your Gmail account
# Subject: "Test Platinum Tier"
# Body: "Please draft a reply confirming receipt."
```

### 7.2 Verify Cloud Agent Processing

```bash
# On cloud VM, check logs
sudo journalctl -u cloud-agent -f

# Expected: Cloud agent detects email, generates draft reply
# Check vault for draft
ls /opt/cloud-agent/obsidian-vault/Pending_Approval/email/
```

### 7.3 Approve and Send (Local Agent)

```bash
# On local machine, check Dashboard.md
# Expected: Pending approval section with draft reply

# Approve the draft (mark as approved in Dashboard.md)
# Local agent will execute send via MCP

# Verify sent email in Gmail
```

### 7.4 Verify Completion

```bash
# Check Done directory
ls obsidian-vault/Done/

# Check audit logs
cat obsidian-vault/Audit_Logs/$(date +%Y-%m-%d).md
```

---

## Troubleshooting

### Cloud Agent Won't Start

```bash
# Check logs
sudo journalctl -u cloud-agent -n 100

# Common issues:
# - Missing dependencies: uv pip install -r requirements.txt
# - Permission errors: sudo chown -R cloudagent:cloudagent /opt/cloud-agent
# - Port conflicts: sudo lsof -i :8080
```

### Vault Sync Failing

```bash
# Check sync logs
sudo journalctl -u vault-sync -n 50

# Test manual sync
sudo -u cloudagent /opt/cloud-agent/sync-vault.sh

# Common issues:
# - SSH key not added to GitHub: cat /home/cloudagent/.ssh/id_ed25519.pub
# - Merge conflicts: cd /opt/cloud-agent/obsidian-vault && git status
# - Network issues: ping github.com
```

### Odoo Not Accessible

```bash
# Check Odoo status
sudo systemctl status odoo

# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check SSL certificate
sudo certbot certificates

# Test Odoo directly
curl http://127.0.0.1:8069/web/health
```

### Health Monitoring Not Alerting

```bash
# Check Monit status
sudo monit status

# Test alert script
sudo /usr/local/bin/alert.sh "Test alert"

# Check Monit logs
sudo tail -f /var/log/monit.log
```

---

## Success Criteria Checklist

- [ ] Cloud VM provisioned and accessible via SSH
- [ ] Vault synchronization working (30-second sync cycle)
- [ ] Odoo accessible via HTTPS with valid SSL certificate
- [ ] Cloud agent running as systemd service
- [ ] Health monitoring active (Monit checks every 5 minutes)
- [ ] Local agent configured and syncing
- [ ] Demo scenario completed successfully (email → draft → approve → send)
- [ ] Audit logs showing both agent activities
- [ ] No credential leaks (cloud agent has read-only access only)

---

## Next Steps

1. **Monitor for 24 hours**: Verify cloud agent stability and sync reliability
2. **Tune resource limits**: Adjust MemoryMax/CPUQuota if needed
3. **Configure additional domains**: Enable social media, accounting drafts
4. **Set up backup verification**: Test Odoo restore procedure
5. **Document custom workflows**: Add domain-specific approval rules

---

## Support Resources

- **Logs**: `sudo journalctl -u cloud-agent -f`
- **Health Status**: `sudo monit status`
- **Vault Sync**: Check `.sync-status/cloud.json` and `.sync-status/local.json`
- **Odoo Admin**: `https://your-domain.com` (admin/your-admin-password)

**Estimated Total Time**: 4-6 hours for complete setup
