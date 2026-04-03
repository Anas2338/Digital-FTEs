# Platinum Tier Deployment Checklist

**Feature**: 001-platinum-tier  
**Status**: Ready for Deployment  
**Date**: 2026-04-03

---

## Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] **Cloud VM Provisioned**
  - Provider: _________________ (DigitalOcean, AWS, GCP, Azure, Linode)
  - OS: Ubuntu 22.04 LTS
  - RAM: 2GB minimum (4GB recommended)
  - CPU: 2 cores minimum
  - Disk: 20GB minimum (50GB recommended)
  - Public IP: _________________
  - SSH access configured

- [ ] **Domain Name**
  - Domain: _________________ (for Odoo HTTPS)
  - DNS A record pointing to VM IP
  - DNS propagated (check: `nslookup your-domain.com`)

- [ ] **Git Repository**
  - Private repository created for vault
  - SSH keys or personal access token ready
  - Repository URL: _________________

- [ ] **Credentials Prepared**
  - Gmail OAuth credentials (read-only for cloud)
  - Gmail OAuth credentials (full access for local)
  - Social media API tokens (read-only for cloud)
  - Social media API tokens (full access for local)
  - Odoo admin password
  - Twilio credentials (for SMS alerts)
  - Pushover/ntfy.sh credentials (for push alerts)

- [ ] **Local Machine Ready**
  - Python 3.11+ installed
  - uv package manager installed
  - Git installed and configured
  - Obsidian installed (optional, for vault viewing)

---

## Phase 1: Cloud VM Setup (30 minutes)

- [ ] SSH into cloud VM: `ssh root@your-vm-ip`
- [ ] Clone repository: `git clone https://github.com/your-org/digital-fte.git /opt/digital-fte`
- [ ] Run setup script: `bash /opt/digital-fte/cloud/deployment/setup_cloud_vm.sh`
- [ ] Verify Python: `python3 --version` (should be 3.11+)
- [ ] Verify uv: `uv --version`
- [ ] Install dependencies: `bash /opt/digital-fte/cloud/deployment/install_dependencies.sh`

**Validation**: `ls -la /opt/digital-fte` should show all directories

---

## Phase 2: Odoo Installation (45 minutes)

- [ ] Run Odoo setup: `sudo bash /opt/digital-fte/cloud/deployment/setup_odoo.sh`
- [ ] Configure SSL: `sudo bash /opt/digital-fte/cloud/deployment/configure_ssl.sh your-domain.com admin@your-domain.com`
- [ ] Copy systemd service: `sudo cp /opt/digital-fte/cloud/deployment/odoo.service /etc/systemd/system/`
- [ ] Enable Odoo: `sudo systemctl enable odoo.service`
- [ ] Start Odoo: `sudo systemctl start odoo.service`
- [ ] Check status: `sudo systemctl status odoo.service`
- [ ] Test health endpoint: `curl https://your-domain.com/web/health`

**Validation**: Should return `{"status": "pass"}`

---

## Phase 3: Vault Synchronization (20 minutes)

- [ ] Create vault repository (on GitHub/GitLab)
- [ ] Initialize vault locally: `cd /path/to/obsidian-vault && git init`
- [ ] Add remote: `git remote add origin https://github.com/your-org/vault.git`
- [ ] Create coordination directories:
  ```bash
  mkdir -p In_Progress/{cloud,local}
  mkdir -p Pending_Approval/{email,social,accounting}
  mkdir -p Updates Manual_Interventions Credential_Rotations
  ```
- [ ] Copy .gitignore: `cp /opt/digital-fte/sync/.gitignore.vault .gitignore`
- [ ] Initial commit: `git add . && git commit -m "Initial vault" && git push -u origin master`
- [ ] Clone to cloud VM: `git clone https://github.com/your-org/vault.git /opt/digital-fte/obsidian-vault`
- [ ] Copy sync script: `sudo cp /opt/digital-fte/cloud/deployment/sync-vault.sh /opt/digital-fte/`
- [ ] Make executable: `sudo chmod +x /opt/digital-fte/sync-vault.sh`
- [ ] Install systemd timer:
  ```bash
  sudo cp /opt/digital-fte/cloud/deployment/vault-sync.service /etc/systemd/system/
  sudo cp /opt/digital-fte/cloud/deployment/vault-sync.timer /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable vault-sync.timer
  sudo systemctl start vault-sync.timer
  ```
- [ ] Verify sync: `sudo systemctl status vault-sync.timer`

**Validation**: `cd /opt/digital-fte/obsidian-vault && git log` should show commits

---

## Phase 4: Cloud Agent Configuration (30 minutes)

- [ ] Create `.env.cloud` file:
  ```bash
  sudo nano /opt/digital-fte/.env.cloud
  # Add read-only credentials (see template)
  ```
- [ ] Create agent config:
  ```bash
  sudo nano /opt/digital-fte/obsidian-vault/config/agent-config.json
  # Set agent_id: "cloud", credential_scope: "read_only"
  ```
- [ ] Copy systemd service:
  ```bash
  sudo cp /opt/digital-fte/cloud/deployment/cloud-agent.service /etc/systemd/system/
  sudo systemctl daemon-reload
  ```
- [ ] Enable cloud agent: `sudo systemctl enable cloud-agent.service`
- [ ] Start cloud agent: `sudo systemctl start cloud-agent.service`
- [ ] Check logs: `sudo journalctl -u cloud-agent.service -f`

**Validation**: Logs should show "Cloud agent starting..." and "Starting watcher cycle"

---

## Phase 5: Health Monitoring (20 minutes)

- [ ] Install Monit: `sudo apt-get install monit`
- [ ] Copy Monit config: `sudo cp /opt/digital-fte/cloud/deployment/monitrc /etc/monit/conf.d/digital-fte.conf`
- [ ] Copy alert script: `sudo cp /opt/digital-fte/cloud/deployment/alert.sh /opt/digital-fte/`
- [ ] Make executable: `sudo chmod +x /opt/digital-fte/alert.sh`
- [ ] Create alert config:
  ```bash
  sudo nano /opt/digital-fte/.alert-config
  # Add Twilio, Pushover, email credentials
  ```
- [ ] Enable Monit: `sudo systemctl enable monit`
- [ ] Start Monit: `sudo systemctl start monit`
- [ ] Reload config: `sudo monit reload`
- [ ] Check status: `sudo monit status`

**Validation**: `sudo monit status` should show all services being monitored

---

## Phase 6: Odoo Backups (10 minutes)

- [ ] Install backup cron: `sudo bash /opt/digital-fte/cloud/deployment/install-odoo-backup-cron.sh`
- [ ] Test backup manually: `sudo /etc/cron.daily/odoo-backup`
- [ ] Verify backup created: `ls -lh /backups/odoo/`

**Validation**: Backup file should exist in `/backups/odoo/`

---

## Phase 7: Local Agent Setup (30 minutes)

### On Local Machine (Windows)

- [ ] Clone repository: `git clone https://github.com/your-org/digital-fte.git C:\Users\YourUser\digital-fte`
- [ ] Install dependencies:
  ```powershell
  cd C:\Users\YourUser\digital-fte\watchers
  uv sync
  ```
- [ ] Clone vault: `git clone https://github.com/your-org/vault.git C:\Users\YourUser\digital-fte\obsidian-vault`
- [ ] Create `.env.local` with FULL credentials
- [ ] Create agent config (agent_id: "local", credential_scope: "full")
- [ ] Set up vault sync scheduled task:
  ```powershell
  schtasks /create /tn "Digital FTE Vault Sync" /tr "powershell.exe -File C:\Users\YourUser\digital-fte\local\sync-vault.ps1" /sc minute /mo 1
  ```
- [ ] Start local agent:
  ```powershell
  cd C:\Users\YourUser\digital-fte
  python local/local_agent.py obsidian-vault
  ```

**Validation**: Local agent should show "Local agent starting..." and "Starting approval processing cycle"

---

## Phase 8: Verification (30 minutes)

### Cloud Agent Verification
- [ ] Check cloud agent logs: `sudo journalctl -u cloud-agent.service -n 50`
- [ ] Verify watchers running (should see "Starting watcher cycle" every 5 minutes)
- [ ] Check vault sync: `cd /opt/digital-fte/obsidian-vault && git log -5`

### Vault Sync Verification
- [ ] On cloud VM: `cd /opt/digital-fte/obsidian-vault && git pull`
- [ ] On local machine: `cd obsidian-vault && git pull`
- [ ] Both should be in sync

### Odoo Verification
- [ ] Access Odoo: `https://your-domain.com`
- [ ] Check health: `curl https://your-domain.com/web/health`
- [ ] Check SSL: `curl -I https://your-domain.com`

### Health Monitoring Verification
- [ ] Check Monit: `sudo monit status`
- [ ] Test alert (optional): `sudo /opt/digital-fte/alert.sh test-service test "Test alert"`

---

## Phase 9: Demo Scenario Test (15 minutes)

- [ ] Send test email to monitored Gmail account
- [ ] Wait 5 minutes for cloud agent to detect
- [ ] Check vault: `Pending_Approval/email/` should have draft
- [ ] Local agent should update Dashboard.md
- [ ] Approve draft in Dashboard.md
- [ ] Local agent should execute (send email)
- [ ] Check audit trail: `cat obsidian-vault/audit_trail.jsonl`

**Validation**: Complete email flow from detection → draft → approval → send

---

## Post-Deployment Tasks

- [ ] Review monitoring dashboard: `obsidian-vault/Monitoring_Dashboard.md`
- [ ] Check health check database: `sqlite3 /opt/digital-fte/cloud/health/health_checks.db`
- [ ] Verify approval rate metric (should be tracked)
- [ ] Set up credential rotation reminders
- [ ] Schedule first security audit (1 week)
- [ ] Schedule first performance review (1 week)

---

## Troubleshooting

If any step fails, refer to:
- `specs/001-platinum-tier/TROUBLESHOOTING.md`
- Cloud agent logs: `sudo journalctl -u cloud-agent.service -n 100`
- Odoo logs: `sudo journalctl -u odoo.service -n 100`
- Vault sync logs: `sudo journalctl -u vault-sync.service -n 100`

---

## Success Criteria

✅ All services running (cloud-agent, odoo, vault-sync, monit)  
✅ Vault syncing every 30 seconds  
✅ Cloud agent detecting events every 5 minutes  
✅ Local agent processing approvals every 2 minutes  
✅ Health monitoring active with alerts configured  
✅ Odoo accessible via HTTPS  
✅ Demo scenario completes successfully  

---

## Next Steps After Deployment

1. Run validation suite (T076-T080)
2. Monitor for 24 hours
3. Review metrics and logs
4. Tune performance if needed
5. Document any issues encountered
6. Create production runbook
