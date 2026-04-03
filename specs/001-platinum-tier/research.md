# Research Findings: Platinum Tier Technical Decisions

**Date**: 2026-04-03  
**Feature**: Platinum Tier - Always-On Cloud + Local Executive  
**Purpose**: Document technical decisions for Phase 0 research

## 1. Vault Synchronization Technology

### Decision: Git-Based Synchronization

**Rationale**:
- **Atomic operations**: Git's push/pull model provides true atomicity for claim-by-move semantics. When an agent tries to claim a task by moving a file, the push will fail if another agent already claimed it, preventing race conditions at the protocol level.
- **Explicit conflict detection**: Failed pushes are immediately detectable (exit code 1), allowing agents to retry or back off. Alternative (Syncthing) uses async model where both agents might think they succeeded.
- **Lower resource overhead**: Git uses 10-20MB RAM vs Syncthing's 50-100MB - critical for 4GB cloud VM running Odoo.
- **Audit trail**: Full commit history provides debugging visibility into agent coordination patterns.
- **Programmatic integration**: Git's CLI is easier to integrate into Python watchers than Syncthing's REST API.

**Alternatives Considered**:
- **Syncthing**: Faster sync latency (2-10s vs 5-15s) but lacks atomic operations needed for claim-by-move. Conflict detection is asynchronous with `.sync-conflict` files appearing after-the-fact. Higher memory usage (50-100MB).

**Implementation Notes**:
- Use GitHub/GitLab private repo or self-hosted Gitea
- Deploy SSH keys to both local and cloud agents
- Sync script runs every 30 seconds via systemd timer
- Claim-by-move pattern: `git add → git commit → git push` (push failure = another agent claimed it)
- Automatic retry with exponential backoff when pushes fail

**Performance Characteristics**:
- Sync latency: 5-15 seconds (meets <60s requirement)
- Memory: 10-20MB baseline, +5MB per operation
- CPU: 1-2% during sync operations
- Network: Only changed deltas transmitted (efficient)

---

## 2. Health Monitoring Infrastructure

### Decision: Monit + Pushover/ntfy.sh

**Rationale**:
- **Resource-efficient**: 20-40MB RAM fits comfortably in 4GB VM (vs Prometheus 400-600MB)
- **Built-in recovery**: Automatically restarts services before alerting (critical for autonomous operation)
- **Simple setup**: 2-3 hours vs 6-8 hours for Prometheus stack
- **Sufficient monitoring**: Process checks, file timestamps, HTTP endpoints cover all requirements
- **Alert delivery**: Email (built-in SMTP) + SMS/push via exec script to Twilio/Pushover

**Alternatives Considered**:
- **Prometheus + Grafana + Alertmanager**: Industry-standard but 400-600MB RAM overhead is too heavy for 4GB shared VM. Overkill for single-agent monitoring.
- **Uptime Kuma**: Beautiful UI, 150-250MB RAM, but no built-in recovery automation. Would need separate script for auto-recovery.
- **Custom Python**: Full control, 50-100MB RAM, but requires building everything from scratch including alert deduplication.
- **Healthchecks.io (SaaS)**: Zero local resources but requires internet connectivity (single point of failure) and privacy concerns.

**Implementation Notes**:
- Monitor: Agent process (HTTP endpoint), vault sync file timestamp, Odoo `/web/health`, API connectivity
- Recovery: Automatic service restart after 2 failed checks (10 minutes)
- Alerts: After 3 restart attempts within 5 cycles, trigger alert script
- Alert channels: Email (Monit SMTP), SMS (Twilio API ~$0.0075/SMS), Push (Pushover $5 one-time or ntfy.sh free)
- Log retention: 90 days via journald + logrotate

**Configuration Example**:
```bash
# /etc/monit/monitrc
check process agent with pidfile /var/run/agent.pid
  if failed host 127.0.0.1 port 8080 protocol http
    with timeout 10 seconds for 2 cycles
    then restart
  if 3 restarts within 5 cycles then exec "/usr/local/bin/alert.sh"

check file vault_sync with path /opt/obsidian-vault/.sync-timestamp
  if timestamp > 15 minutes then alert
```

---

## 3. Odoo Cloud Deployment

### Decision: Native Installation (PostgreSQL + Odoo)

**Rationale**:
- **Memory efficiency**: 800-1200MB total vs Docker's 1200-1500MB - saves 300-400MB critical for 4GB VM
- **Simpler stack**: Fewer moving parts for single-instance deployment (no Docker layer)
- **Better performance**: Direct file system access, no container overhead
- **Easier debugging**: Direct log access via journalctl, no container layer complexity
- **Backup simplicity**: Standard `pg_dump` + tar, no Docker volume management

**Alternatives Considered**:
- **Docker deployment**: Isolated environment, easy version upgrades, but 20-30% higher memory usage and additional complexity for single-instance deployment.

**Implementation Notes**:
- Install: PostgreSQL 15 + Odoo 17.0 from official deb package
- Systemd service: `odoo.service` with auto-restart
- PostgreSQL tuning: `shared_buffers=256MB` (conservative for 4GB VM)
- Odoo workers: 2-3 max (monitor with htop, tune if exceeds 600MB)
- SSL: nginx reverse proxy with Let's Encrypt (certbot)
- Backups: Daily cron job with `pg_dump` + filestore tar, 30-day retention
- Resource allocation: Leaves ~2.5GB free for OS, Python agent, and growth

**Backup Script**:
```bash
#!/bin/bash
# /etc/cron.daily/odoo-backup
sudo -u postgres pg_dump odoo | gzip > /backups/odoo-$(date +%Y%m%d).sql.gz
tar -czf /backups/filestore-$(date +%Y%m%d).tar.gz /var/lib/odoo/filestore
find /backups -name "*.gz" -mtime +30 -delete
```

**Restore Procedure**:
```bash
sudo systemctl stop odoo
sudo -u postgres psql -c "DROP DATABASE odoo;"
sudo -u postgres psql -c "CREATE DATABASE odoo;"
gunzip < backup.sql.gz | sudo -u postgres psql odoo
tar -xzf filestore-backup.tar.gz -C /
sudo systemctl start odoo
```

---

## 4. Logical Timestamp Implementation

### Decision: Lamport Timestamps

**Rationale**:
- **Simplest** for 2-agent claim-by-move coordination
- **Sufficient** for total ordering (all that's needed for conflict resolution)
- **Minimal storage**: Single counter + agent_id (8-16 bytes)
- **Clock-skew independent**: No reliance on wall-clock synchronization
- Vector clocks detect causality but unnecessary for "who claimed first?" use case
- Hybrid Logical Clocks require physical clocks, defeating clock-skew-independence goal

**Alternatives Considered**:
- **Vector Clocks**: Maintains vector of all agent counters `{cloud: 5, local: 3}`. Detects causality (concurrent vs happened-before) but overkill for 2 agents with 2x storage overhead.
- **Hybrid Logical Clocks (HLC)**: Combines physical time with logical counter. Timestamps approximate wall-clock time but requires physical clock, defeating the purpose.

**Implementation**:
```python
@dataclass
class LamportTimestamp:
    agent_id: Literal["cloud", "local"]
    counter: int
    
    def __lt__(self, other: "LamportTimestamp") -> bool:
        if self.counter != other.counter:
            return self.counter < other.counter
        return self.agent_id < other.agent_id  # Tie-breaker

class LamportClock:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.counter = 0
    
    def tick(self) -> LamportTimestamp:
        self.counter += 1
        return LamportTimestamp(self.agent_id, self.counter)
    
    def update(self, received: LamportTimestamp) -> LamportTimestamp:
        self.counter = max(self.counter, received.counter) + 1
        return LamportTimestamp(self.agent_id, self.counter)
```

**File Format**:
- Compact string: `"cloud:42"` or `"local:17"`
- JSON: `{"agent_id": "cloud", "counter": 42}`
- Comparison: Lower counter wins; agent_id as tie-breaker (cloud < local)

**Usage Pattern**:
1. Agent increments counter on every operation (claim, update, complete)
2. When receiving another agent's timestamp, update local counter to `max(local, received) + 1`
3. Conflict resolution: Compare timestamps, lower counter wins

---

## 5. Systemd Service Configuration

### Decision: Production-Ready Service Unit with Security Hardening

**Rationale**:
- **Automatic restart**: `Restart=on-failure` with `RestartSec=10` ensures agent recovers from crashes
- **Restart loop prevention**: `StartLimitBurst=5` in `StartLimitIntervalSec=300` prevents infinite restart loops
- **Resource protection**: `MemoryMax=512M`, `CPUQuota=50%` prevents runaway processes
- **Security hardening**: Run as non-root user, isolated /tmp, read-only system, restricted write paths
- **Comprehensive logging**: All output to journald with `SyslogIdentifier` for easy filtering

**Service Unit** (`/etc/systemd/system/cloud-agent.service`):
```ini
[Unit]
Description=Cloud Agent - Autonomous Python Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=cloudagent
Group=cloudagent
WorkingDirectory=/opt/cloud-agent
ExecStart=/opt/cloud-agent/.venv/bin/python -u /opt/cloud-agent/main.py

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
ReadWritePaths=/opt/cloud-agent/data /opt/cloud-agent/logs
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

**Key Features**:
- Automatic restart on failure with 10-second delay
- Max 5 restarts in 5 minutes (prevents restart loops)
- Graceful shutdown with SIGTERM (30-second timeout)
- Hard memory limit: 512MB, soft warning at 400MB
- Max 50% of one CPU core
- Isolated /tmp, read-only system except specified paths
- Logs accessible via `journalctl -u cloud-agent`

**Python SIGTERM Handler**:
```python
import signal
import sys

def shutdown_handler(signum, frame):
    print("Received SIGTERM, shutting down gracefully...")
    # Cleanup: close connections, save state
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
```

**Management Commands**:
```bash
# Enable and start
sudo systemctl enable cloud-agent
sudo systemctl start cloud-agent

# Monitor logs
sudo journalctl -u cloud-agent -f

# Check status and resource usage
sudo systemctl status cloud-agent
```

---

## Summary of Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| Vault Sync | Git | Atomic operations for claim-by-move, 10-20MB RAM |
| Health Monitoring | Monit | Built-in recovery, 20-40MB RAM, simple setup |
| Odoo Deployment | Native | 300-400MB RAM savings, simpler stack |
| Logical Timestamps | Lamport | Simplest, sufficient for 2-agent ordering |
| Systemd Service | Hardened unit | Auto-restart, resource limits, security |

**Total Resource Budget** (4GB VM):
- OS + base services: ~1GB
- Odoo (native): ~1GB
- Cloud agent: ~500MB
- Monit: ~40MB
- Git sync: ~20MB
- **Free headroom**: ~1.4GB (35% buffer)

All decisions prioritize resource efficiency, operational simplicity, and alignment with constitution principles (local-first, privacy-first, autonomous operation).
