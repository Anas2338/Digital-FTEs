# Platinum Tier Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Platinum Tier Digital FTE system with cloud-hosted agent, local agent, and Obsidian vault synchronization.

**Architecture**: Dual-agent system with cloud agent (24/7 monitoring) + local agent (approvals/execution) coordinated via Git-synchronized Obsidian vault.

**Prerequisites**:
- Cloud VM (Ubuntu 22.04 LTS recommended, 2GB RAM minimum)
- Local machine (Windows/macOS/Linux)
- Git repository for vault synchronization
- Domain name with DNS access (for Odoo HTTPS)
- Python 3.11+ with uv package manager

---

## Phase 1: Cloud VM Setup

### 1.1 Provision Cloud VM

Recommended specs:
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 2GB minimum (4GB recommended)
- **CPU**: 2 cores minimum
- **Disk**: 20GB minimum (50GB recommended for backups)
- **Network**: Public IP with ports 80, 443 open

Providers: DigitalOcean, Linode, AWS EC2, Google Cloud, Azure

### 1.2 Initial VM Configuration

```bash
# SSH into VM
ssh root@your-vm-ip

# Run cloud VM setup script
cd /opt
git clone https://github.com/your-org/digital-fte.git
cd digital-fte
bash cloud/deployment/setup_cloud_vm.sh
```

This script:
- Updates system packages
- Installs Python 3.11+, uv, git, nginx, postgresql
- Creates digital-fte user
- Sets up directory structure in /opt/digital-fte

### 1.3 Install Dependencies

```bash
# Install Python dependencies
cd /opt/digital-fte
bash cloud/deployment/install_dependencies.sh
```

This installs all required Python packages using uv.

---

## Phase 2: Odoo Installation

### 2.1 Install Odoo 17.0

```bash
# Run Odoo setup script
sudo bash cloud/deployment/setup_odoo.sh
```

This script:
- Installs PostgreSQL and creates odoo database user
- Installs Odoo Community Edition 17.0
- Configures Odoo with 2 workers and resource limits
- Creates /etc/odoo/odoo.conf configuration

### 2.2 Configure SSL for Odoo

```bash
# Configure nginx reverse proxy with Let's Encrypt SSL
sudo bash cloud/deployment/configure_ssl.sh your-domain.com admin@your-domain.com
```

Replace `your-domain.com` with your actual domain.

This script:
- Installs certbot for Let's Encrypt
- Configures nginx reverse proxy
- Obtains SSL certificate
- Sets up automatic certificate renewal

### 2.3 Configure Odoo Systemd Service

```bash
# Copy systemd service file
sudo cp cloud/deployment/odoo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable odoo.service
sudo systemctl start odoo.service

# Verify Odoo is running
sudo systemctl status odoo.service
curl https://your-domain.com/web/health
```

### 2.4 Set Up Odoo Backups

```bash
# Install backup cron job
sudo bash cloud/deployment/install-odoo-backup-cron.sh
```

This configures daily backups at ~6:25 AM with 30-day retention.

---

## Phase 3: Vault Synchronization Setup

### 3.1 Create Git Repository for Vault

```bash
# On your local machine, create vault repository
cd /path/to/obsidian-vault
git init
git add .
git commit -m "Initial vault commit"
git remote add origin https://github.com/your-org/digital-fte-vault.git
git push -u origin master
```

**Security Note**: Use a private repository. Add `.gitignore` to exclude:
- `.obsidian/workspace*` (local UI state)
- `WhatsApp_Sessions/` (local-only credentials)
- `.env*` (secrets)

### 3.2 Clone Vault on Cloud VM

```bash
# On cloud VM
cd /opt/digital-fte
git clone https://github.com/your-org/digital-fte-vault.git obsidian-vault
cd obsidian-vault

# Create coordination directories
mkdir -p In_Progress/{cloud,local}
mkdir -p Pending_Approval/{email,social,accounting}
mkdir -p Updates
mkdir -p Manual_Interventions
```

### 3.3 Configure Vault Sync

```bash
# Copy vault sync script
sudo cp cloud/deployment/sync-vault.sh /opt/digital-fte/
sudo chmod +x /opt/digital-fte/sync-vault.sh

# Install systemd timer for 30-second sync
sudo cp cloud/deployment/vault-sync.service /etc/systemd/system/
sudo cp cloud/deployment/vault-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vault-sync.timer
sudo systemctl start vault-sync.timer

# Verify sync is running
sudo systemctl status vault-sync.timer
```

---

## Phase 4: Cloud Agent Configuration

### 4.1 Configure Read-Only Credentials

Create `/opt/digital-fte/.env.cloud`:

```bash
# Gmail (read-only OAuth2)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token

# Social Media (read-only tokens)
FACEBOOK_ACCESS_TOKEN=your-read-only-token
INSTAGRAM_ACCESS_TOKEN=your-read-only-token
TWITTER_API_KEY=your-read-only-key

# Odoo (read-only user)
ODOO_URL=https://your-domain.com
ODOO_DB=odoo
ODOO_USERNAME=agent_readonly
ODOO_PASSWORD=secure-password

# LLM Provider (Claude or Gemini)
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-api-key
# OR
# LLM_PROVIDER=gemini
# GOOGLE_API_KEY=your-api-key
```

**Security**: Ensure read-only credentials only. Cloud agent must NOT have write access.

### 4.2 Create Agent Configuration

Create `/opt/digital-fte/obsidian-vault/config/agent-config.json`:

```json
{
  "agent_id": "cloud",
  "credential_scope": "read_only",
  "vault_path": "/opt/digital-fte/obsidian-vault",
  "llm_provider": "claude",
  "work_zones": {
    "drafts": true,
    "approvals": false,
    "execution": false
  }
}
```

### 4.3 Install Cloud Agent Service

```bash
# Copy systemd service file
sudo cp cloud/deployment/cloud-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloud-agent.service
sudo systemctl start cloud-agent.service

# Verify cloud agent is running
sudo systemctl status cloud-agent.service
sudo journalctl -u cloud-agent.service -f
```

---

## Phase 5: Health Monitoring Setup

### 5.1 Install Monit

```bash
sudo apt-get install monit
```

### 5.2 Configure Monit

```bash
# Copy Monit configuration
sudo cp cloud/deployment/monitrc /etc/monit/conf.d/digital-fte.conf

# Copy alert script
sudo cp cloud/deployment/alert.sh /opt/digital-fte/
sudo chmod +x /opt/digital-fte/alert.sh
```

### 5.3 Configure Alert Channels

Create `/opt/digital-fte/.alert-config`:

```bash
# Enable alert channels
ENABLE_SMS=true
ENABLE_PUSH=true
ENABLE_EMAIL=true

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1234567890

# Pushover (Push notifications)
PUSHOVER_APP_TOKEN=your-app-token
PUSHOVER_USER_KEY=your-user-key

# OR ntfy.sh (alternative push)
NTFY_TOPIC=digital-fte-alerts
NTFY_SERVER=https://ntfy.sh

# Email
EMAIL_TO=admin@your-domain.com
EMAIL_FROM=alerts@your-domain.com
SMTP_HOST=localhost
```

### 5.4 Start Monit

```bash
sudo systemctl enable monit
sudo systemctl start monit
sudo monit reload

# Verify monitoring
sudo monit status
```

---

## Phase 6: Local Agent Setup

### 6.1 Install Local Agent (Windows)

```powershell
# Clone repository
cd C:\Users\YourUser\
git clone https://github.com/your-org/digital-fte.git
cd digital-fte

# Install dependencies
cd watchers
uv sync

# Clone vault
cd ..
git clone https://github.com/your-org/digital-fte-vault.git obsidian-vault
```

### 6.2 Configure Local Agent

Create `obsidian-vault/config/agent-config.json`:

```json
{
  "agent_id": "local",
  "credential_scope": "full",
  "vault_path": "C:\\Users\\YourUser\\digital-fte\\obsidian-vault",
  "work_zones": {
    "drafts": false,
    "approvals": true,
    "execution": true
  }
}
```

### 6.3 Configure Full Credentials

Create `.env.local` with FULL credentials (write access):

```bash
# Gmail (full OAuth2 with send permission)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-full-access-token

# Social Media (write tokens)
FACEBOOK_ACCESS_TOKEN=your-write-token
INSTAGRAM_ACCESS_TOKEN=your-write-token

# Odoo (full access user)
ODOO_URL=https://your-domain.com
ODOO_DB=odoo
ODOO_USERNAME=agent_full
ODOO_PASSWORD=secure-password

# WhatsApp (local-only sessions)
WHATSAPP_SESSION_PATH=C:\\Users\\YourUser\\digital-fte\\WhatsApp_Sessions
```

### 6.4 Set Up Vault Sync (Windows)

```powershell
# Create scheduled task for vault sync
# Run sync-vault.ps1 every 30 seconds
schtasks /create /tn "Digital FTE Vault Sync" /tr "powershell.exe -File C:\Users\YourUser\digital-fte\local\sync-vault.ps1" /sc minute /mo 1
```

### 6.5 Start Local Agent

```powershell
# Run local agent
cd C:\Users\YourUser\digital-fte
python local/local_agent.py obsidian-vault
```

---

## Phase 7: Verification

### 7.1 Test Cloud Agent

```bash
# On cloud VM, check logs
sudo journalctl -u cloud-agent.service -f

# Verify watchers are running
# Should see "Starting watcher cycle" every 5 minutes
```

### 7.2 Test Vault Sync

```bash
# On cloud VM
cd /opt/digital-fte/obsidian-vault
git log -5

# On local machine
cd obsidian-vault
git pull
# Should see recent commits from cloud agent
```

### 7.3 Test Draft Generation

Send a test email to your monitored Gmail account. Within 5 minutes:
1. Cloud agent detects email
2. Generates draft reply
3. Writes to `Pending_Approval/email/`
4. Syncs to vault
5. Local agent detects draft
6. Updates Dashboard.md

### 7.4 Test Health Monitoring

```bash
# Simulate service failure
sudo systemctl stop cloud-agent.service

# Wait 10 minutes (2 failed checks)
# Monit should automatically restart service

# Check Monit logs
sudo journalctl -u monit -f
```

---

## Troubleshooting

### Cloud Agent Not Starting

```bash
# Check logs
sudo journalctl -u cloud-agent.service -n 100

# Common issues:
# - Missing credentials in .env.cloud
# - Vault path incorrect in agent-config.json
# - Python dependencies not installed
```

### Vault Sync Failing

```bash
# Check sync status
cat /opt/digital-fte/obsidian-vault/.sync-status/cloud.json

# Common issues:
# - Git authentication failure (use SSH keys or personal access token)
# - Merge conflicts (check git status)
# - Insufficient permissions
```

### Odoo Not Accessible

```bash
# Check Odoo service
sudo systemctl status odoo.service

# Check nginx
sudo systemctl status nginx

# Check SSL certificate
sudo certbot certificates

# Test health endpoint
curl https://your-domain.com/web/health
```

### Health Monitoring Not Alerting

```bash
# Check Monit status
sudo monit status

# Test alert script manually
sudo /opt/digital-fte/alert.sh cloud-agent test "Test alert"

# Check alert configuration
cat /opt/digital-fte/.alert-config
```

---

## Maintenance

### Daily Tasks
- Check Dashboard.md for pending approvals
- Review Manual_Interventions/ for issues requiring attention

### Weekly Tasks
- Review health check database: `sqlite3 /opt/digital-fte/cloud/health/health_checks.db`
- Check approval rate metric (should be ≥80%)
- Verify backups exist: `ls -lh /backups/odoo/`

### Monthly Tasks
- Review manual intervention count (should be <5 per month)
- Rotate credentials (90-day cycle per FR-042)
- Update system packages: `sudo apt-get update && sudo apt-get upgrade`

---

## Security Checklist

- [ ] Cloud agent has read-only credentials only
- [ ] Local agent credentials stored in OS keychain
- [ ] WhatsApp sessions NOT synced to vault
- [ ] Vault repository is private
- [ ] SSL certificates configured and auto-renewing
- [ ] Firewall configured (only ports 80, 443, 22 open)
- [ ] Monit alerts configured and tested
- [ ] Backup encryption enabled
- [ ] Credential rotation scheduled

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs: `sudo journalctl -u cloud-agent.service -n 100`
3. Check health status: `sudo monit status`
4. Review specs/001-platinum-tier/TROUBLESHOOTING.md
