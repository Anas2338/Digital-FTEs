# Quickstart: Silver Tier Functional Assistant

**Feature**: 001-silver-tier-functional
**Date**: 2026-03-30
**Purpose**: Setup instructions for developers implementing Silver Tier

## Prerequisites

- ✅ Bronze Tier completed (Obsidian vault, Gmail watcher, agent skills)
- Python 3.11+ installed
- Node.js 18+ installed (for whatsapp-web.js)
- uv package manager installed (`pip install uv`)
- Git repository initialized
- OS keychain access (Windows Credential Manager, macOS Keychain, Linux Secret Service)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Brain (Claude Code)                       │
│  Agent Skills: watcher-status, mcp-invoke, approval-review, │
│                linkedin-draft, reasoning-plan, schedule-task │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Memory (Obsidian Vault)                     │
│  /Inbox, /Needs_Action, /Done, /Approvals, /Content_Queue,  │
│  /Schedules, /Reports                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│  Senses (Watchers)        │   │  Hands (MCP Server)       │
│  - Gmail Watcher          │   │  - send-email             │
│  - WhatsApp Watcher       │   │  - linkedin-post          │
│  - LinkedIn Watcher       │   │  - whatsapp-send          │
└───────────────────────────┘   └───────────────────────────┘
```

## Setup Steps

### 1. Install Dependencies

```bash
# Navigate to project root
cd /path/to/Digital-FTEs

# Install Python dependencies for watchers
cd watchers
uv pip install -e .

# Install Python dependencies for MCP server
cd ../mcp-servers/digital-fte-server
uv pip install -e .

# Install Node.js dependencies for WhatsApp bridge
cd ../../watchers/whatsapp_watcher
npm install whatsapp-web.js puppeteer
```

### 2. Configure API Credentials

#### Gmail (OAuth2)
```bash
# Run Gmail OAuth2 setup
python scripts/setup/configure_apis.py --service gmail

# Follow browser prompts to authorize
# Credentials stored in OS keychain: key="digital-fte-gmail-token"
```

#### WhatsApp (Session-based)
```bash
# Run WhatsApp setup (generates QR code)
python scripts/setup/configure_apis.py --service whatsapp

# Scan QR code with WhatsApp mobile app
# Session data stored in: watchers/whatsapp_watcher/.wwebjs_auth/
```

#### LinkedIn (Session-based)
```bash
# Run LinkedIn setup (interactive login)
python scripts/setup/configure_apis.py --service linkedin

# Enter LinkedIn credentials when prompted
# Session cookies stored in OS keychain: key="digital-fte-linkedin-session"
```

### 3. Initialize Vault Folders

```bash
# Create new Silver Tier folders
mkdir -p obsidian-vault/Approvals
mkdir -p obsidian-vault/Rejected
mkdir -p obsidian-vault/Expired
mkdir -p obsidian-vault/Content_Queue
mkdir -p obsidian-vault/Schedules
mkdir -p obsidian-vault/Reports

# Verify structure
ls -la obsidian-vault/
```

### 4. Start Watchers

```bash
# Start all watchers in background
python watchers/gmail_watcher/watcher.py --daemon &
python watchers/whatsapp_watcher/watcher.py --daemon &
python watchers/linkedin_watcher/watcher.py --daemon &

# Check watcher status
python -c "from watchers.shared.health_check import check_all; check_all()"
```

### 5. Start MCP Server

```bash
# Start MCP server
cd mcp-servers/digital-fte-server
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Verify server is running
curl http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "..."}
```

### 6. Install Agent Skills

```bash
# Agent skills are already in .claude/skills/
# Verify they're recognized by Claude Code
ls -la .claude/skills/

# Expected output:
# watcher-status/
# mcp-invoke/
# approval-review/
# linkedin-draft/
# reasoning-plan/
# schedule-task/
```

### 7. Configure Scheduler

#### Unix/Linux (cron)
```bash
# Add scheduler to crontab (runs every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /path/to/Digital-FTEs && python scripts/scheduler/task_executor.py") | crontab -

# Verify crontab
crontab -l
```

#### Windows (Task Scheduler)
```powershell
# Import Task Scheduler XML
schtasks /create /xml scripts/scheduler/digital-fte-scheduler.xml /tn "DigitalFTE-Scheduler"

# Verify task
schtasks /query /tn "DigitalFTE-Scheduler"
```

## Verification Tests

### Test 1: Watcher Health Check

```bash
# Run watcher status agent skill
claude-code "Check watcher status"

# Expected output:
# Gmail Watcher: healthy (last check: 2 minutes ago)
# WhatsApp Watcher: healthy (last check: 3 minutes ago)
# LinkedIn Watcher: healthy (last check: 4 minutes ago)
```

### Test 2: MCP Server Tool Invocation

```bash
# Test send-email tool (will queue for approval)
curl -X POST http://localhost:8000/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "send-email",
    "parameters": {
      "recipient": "test@example.com",
      "subject": "Test Email",
      "body": "This is a test email from Digital FTE"
    }
  }'

# Expected response:
# {
#   "success": true,
#   "action_id": "uuid-here",
#   "status": "pending_approval",
#   "message": "Action queued for approval in /Approvals"
# }
```

### Test 3: Approval Workflow

```bash
# Check pending approvals
claude-code "Review pending approvals"

# Approve the test email
claude-code "Approve action <action-id>"

# Verify email was sent
# Check obsidian-vault/Done/ for confirmation note
```

### Test 4: LinkedIn Draft Generation

```bash
# Generate LinkedIn post draft
claude-code "Draft a LinkedIn post about our Q1 revenue growth"

# Expected: Draft saved to obsidian-vault/Content_Queue/
```

### Test 5: Reasoning Loop

```bash
# Create complex task
echo "Launch new product line with marketing campaign, website redesign, and sales training" > obsidian-vault/Needs_Action/product-launch.md

# Wait 30 seconds for reasoning loop to detect
# Verify Plan.md was created
ls obsidian-vault/Needs_Action/Plan.md
```

### Test 6: Scheduled Task

```bash
# Create scheduled task
claude-code "Schedule a weekly summary report every Monday at 9am"

# Verify schedule was created
ls obsidian-vault/Schedules/
cat obsidian-vault/Schedules/weekly-summary.md
```

## Troubleshooting

### Watcher Not Starting

**Symptom**: Watcher process exits immediately

**Solutions**:
1. Check API credentials: `python scripts/setup/configure_apis.py --verify`
2. Check log file: `tail -f watchers/logs/watcher-<name>.log`
3. Verify Python dependencies: `uv pip list | grep <package>`

### WhatsApp QR Code Expired

**Symptom**: WhatsApp watcher shows "session expired" error

**Solution**:
```bash
# Re-authenticate
rm -rf watchers/whatsapp_watcher/.wwebjs_auth/
python scripts/setup/configure_apis.py --service whatsapp
# Scan new QR code
```

### LinkedIn Session Invalid

**Symptom**: LinkedIn watcher shows "authentication failed" error

**Solution**:
```bash
# Re-authenticate
python scripts/setup/configure_apis.py --service linkedin --force-reauth
# Enter credentials again
```

### MCP Server Not Responding

**Symptom**: `curl http://localhost:8000/health` times out

**Solutions**:
1. Check if server is running: `ps aux | grep uvicorn`
2. Check port availability: `lsof -i :8000` (Unix) or `netstat -ano | findstr :8000` (Windows)
3. Check server logs: `tail -f mcp-servers/digital-fte-server/logs/server.log`

### Approval Queue Not Working

**Symptom**: Actions execute without approval

**Solutions**:
1. Verify action safety level classification: Check `mcp-servers/digital-fte-server/approval/classifier.py`
2. Check approval folder exists: `ls obsidian-vault/Approvals/`
3. Verify MCP server approval middleware is enabled

### Reasoning Loop Not Triggering

**Symptom**: Complex tasks don't generate Plan.md

**Solutions**:
1. Check complexity threshold: `cat .claude/skills/reasoning-plan/SKILL.md`
2. Verify task note format (must be in /Needs_Action with proper frontmatter)
3. Check reasoning loop logs: `tail -f .claude/logs/reasoning-plan.log`

### Scheduler Not Running

**Symptom**: Scheduled tasks don't execute

**Solutions**:
1. Unix/Linux: Verify crontab entry: `crontab -l`
2. Windows: Verify Task Scheduler: `schtasks /query /tn "DigitalFTE-Scheduler"`
3. Check scheduler logs: `tail -f scripts/scheduler/logs/executor.log`

## Development Workflow

### Adding a New Watcher

1. Create watcher directory: `watchers/<channel>_watcher/`
2. Implement watcher.py following existing pattern
3. Add event schema to `contracts/watcher-events.json`
4. Add tests: `tests/watchers/test_<channel>_watcher.py`
5. Update health check: `watchers/shared/health_check.py`
6. Document in quickstart.md

### Adding a New MCP Tool

1. Create tool file: `mcp-servers/digital-fte-server/tools/<tool_name>.py`
2. Add tool schema to `contracts/mcp-server.json`
3. Register tool in `server.py`
4. Add tests: `tests/mcp_server/test_<tool_name>.py`
5. Update agent skill: `.claude/skills/mcp-invoke/SKILL.md`

### Adding a New Agent Skill

1. Create skill directory: `.claude/skills/<skill-name>/`
2. Write SKILL.md following template
3. Add tests: `tests/agent_skills/test_<skill_name>.py`
4. Document in quickstart.md
5. Update agent context: Run `update-agent-context.ps1`

## Performance Tuning

### Watcher Polling Intervals

Edit watcher config to adjust polling frequency:
```python
# watchers/<channel>_watcher/config.py
POLLING_INTERVAL_SECONDS = 300  # 5 minutes (default)
```

**Recommendations**:
- Gmail: 180s (3 min) - balance between responsiveness and API quota
- WhatsApp: 300s (5 min) - unofficial API, be conservative
- LinkedIn: 300s (5 min) - unofficial API, avoid detection

### Rate Limit Adjustments

Edit MCP server rate limiter:
```python
# mcp-servers/digital-fte-server/rate_limiter.py
RATE_LIMITS = {
    "send-email": (100, 86400),      # 100 per day
    "linkedin-post": (100, 86400),   # 100 per day
    "whatsapp-send": (1000, 86400),  # 1000 per day
}
```

### Complexity Threshold Tuning

Edit reasoning loop threshold:
```python
# .claude/skills/reasoning-plan/config.py
COMPLEXITY_THRESHOLD = 25  # Lower = more plans generated
```

## Security Checklist

- [ ] All API credentials stored in OS keychain (not in code/config)
- [ ] Sensitive data redacted in logs (check `watchers/shared/event_logger.py`)
- [ ] Rate limits enforced (check `mcp-servers/digital-fte-server/rate_limiter.py`)
- [ ] Approval workflow enabled for Level 2+ actions
- [ ] Input validation enabled (check `mcp-servers/digital-fte-server/validator.py`)
- [ ] Audit trail logging enabled (check SQLite `actions` table)
- [ ] 24-hour approval expiration configured
- [ ] Watcher health checks running
- [ ] MCP server health endpoint accessible

## Next Steps

After completing setup:

1. **Run Integration Tests**: `pytest tests/integration/ -v`
2. **Monitor for 24 Hours**: Check watcher logs, MCP server logs, approval queue
3. **Tune Thresholds**: Adjust complexity threshold, rate limits based on usage
4. **Generate Tasks**: Run `/sp.tasks` to create implementation task list
5. **Begin Implementation**: Start with P1 tasks (multi-channel watchers)

## Support

- **Documentation**: See `specs/001-silver-tier-functional/` for detailed specs
- **Issues**: Report bugs via GitHub issues
- **Constitution**: Review `.specify/memory/constitution.md` for principles
- **Agent Skills**: Check `.claude/skills/*/SKILL.md` for usage examples
