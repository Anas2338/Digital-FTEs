# Gold Tier Digital FTE - Quickstart Guide

Complete setup and validation guide for Gold Tier autonomous AI agent.

## Prerequisites

- Python 3.11+
- uv package manager
- Obsidian (for vault visualization)
- Git

## 1. Initial Setup

### Install Dependencies

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync watchers dependencies
cd watchers
uv sync

# Sync MCP server dependencies
cd ../mcp-servers/digital-fte-server
uv sync

# Return to project root
cd ../..
```

### Setup Vault Structure

```bash
uv run python scripts/setup_gold_tier_vault.py
```

This creates the complete Obsidian vault structure with all required directories.

## 2. Configure Integrations

### Create .env File

```bash
# Copy the example
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

### Fill in Credentials

Edit `.env` with your actual credentials:

```env
# Odoo Community Edition 19+
ODOO_URL=https://your-odoo-instance.com
ODOO_DATABASE=your_database_name
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password

# Facebook
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# Twitter/X
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Instagram
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
```

### Verify Configuration

```bash
uv run python scripts/verify_env.py
```

Expected output: `✓ SUCCESS: All credentials verified`

### Test Connections

#### Test Odoo

```bash
uv run python watchers/odoo_watcher/test_connection.py
```

Expected output: `✓ Odoo connection successful`

#### Test Social Media

```bash
uv run python watchers/social_media_watcher/test_connections.py
```

Expected output:
```
✓ facebook: Connected
✓ twitter: Connected
✓ instagram: Connected
```

## 3. Start Watchers

### Odoo Watcher (5-minute polling)

```bash
uv run python watchers/odoo_watcher/watcher.py
```

### Social Media Watcher (5-minute polling)

```bash
uv run python watchers/social_media_watcher/watcher.py
```

### CEO Briefing Watcher (Monday 8 AM)

```bash
uv run python watchers/briefing_watcher/watcher.py
```

## 4. Start MCP Server

```bash
cd mcp-servers/digital-fte-server
uv run uvicorn server:app --host 0.0.0.0 --port 8000
```

Test server health:
```bash
curl http://localhost:8000/health
```

Expected output: `{"status":"healthy",...}`

## 5. Validation Tests

### Test Odoo Integration

```bash
# Record a test transaction
curl -X POST http://localhost:8000/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "odoo-record-transaction",
    "parameters": {
      "amount": 1000.00,
      "date": "2026-04-01",
      "description": "Test transaction",
      "category": "Revenue"
    }
  }'
```

Verify in: `obsidian-vault/Accounting/transactions.db`

### Test Social Media Posting

```bash
# Create a test post
curl -X POST http://localhost:8000/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "social-post",
    "parameters": {
      "content": "Test post from Digital FTE",
      "platforms": ["twitter"]
    }
  }'
```

Verify in: Social media platform and `social_media_posts` table

### Test CEO Briefing Generation

```bash
# Manually trigger briefing generation
uv run python watchers/briefing_watcher/watcher.py --generate-now
```

Verify in: `obsidian-vault/Briefings/YYYY-WW.md`

### Test Autonomous Task Execution

```bash
uv run python scripts/demo_autonomous_task.py
```

Expected output: Task completes all steps autonomously

### Test Circuit Breaker

```bash
# Simulate failure by disconnecting Odoo
# Then check circuit breaker opens

uv run python scripts/daily_health_check.py
```

Expected output: Circuit breaker OPEN for odoo_integration

```bash
# Reset circuit breaker after fixing issue
uv run python watchers/shared/reset_circuit_breaker.py --reset odoo_integration
```

## 6. Daily Operations

### Health Check

Run daily to verify system health:

```bash
uv run python scripts/daily_health_check.py
```

### View Integration Status

```bash
uv run python watchers/shared/view_integration_status.py
```

### Check Audit Logs

```bash
# View recent audit log entries
sqlite3 obsidian-vault/Audit_Logs/audit.db "SELECT * FROM audit_log ORDER BY sequence_number DESC LIMIT 10"
```

### Verify Hash Chain Integrity

```bash
uv run python -c "from watchers.shared.audit_logger import AuditLogger; al = AuditLogger(); print('✓ Hash chain valid' if al.verify_hash_chain() else '✗ Hash chain broken')"
```

## 7. Troubleshooting

### Circuit Breaker Stuck Open

```bash
# List all circuit breakers
uv run python watchers/shared/reset_circuit_breaker.py --list

# Reset specific breaker
uv run python watchers/shared/reset_circuit_breaker.py --reset <integration_name>

# Reset all open breakers
uv run python watchers/shared/reset_circuit_breaker.py --reset-all
```

### Watcher Not Running

Check watcher health:
```bash
uv run python watchers/shared/view_integration_status.py
```

Check logs:
```bash
tail -f watchers/logs/watcher.log
```

### Database Locked

```bash
# Close all connections and restart watchers
pkill -f "uv run python watchers"
sleep 2
# Restart watchers
```

### High Error Rate

```bash
# Check recent errors
uv run python scripts/daily_health_check.py

# Review audit log
sqlite3 obsidian-vault/Audit_Logs/audit.db "SELECT * FROM audit_log WHERE action_type LIKE '%failed%' ORDER BY timestamp DESC LIMIT 20"
```

## 8. Security Checklist

- [ ] All credentials stored in .env file (never committed to git)
- [ ] .env file in .gitignore
- [ ] OAuth2 used for all external APIs
- [ ] PII redacted in audit logs
- [ ] Hash chain integrity verified
- [ ] Action safety levels enforced (0-3)
- [ ] Rate limits configured (10 posts/day, 100 emails/day)
- [ ] Circuit breakers protecting all integrations
- [ ] Audit logging enabled for all actions

## 9. Constitution Compliance

Verify compliance with `.specify/memory/constitution.md`:

- [ ] Local-first: All data in Obsidian vault
- [ ] Privacy-first: No cloud sync without consent
- [ ] Autonomous: Watchers run 24/7
- [ ] Separation of concerns: Brain/Memory/Senses/Hands
- [ ] Event-driven: Watchers emit events
- [ ] Action safety: 4-level approval system
- [ ] Dual-tier LLM: Claude OR Gemini

## 10. Success Criteria

Gold Tier is operational when:

- [ ] All integration connection tests pass
- [ ] Odoo watcher syncing transactions (5-min interval)
- [ ] Social media watcher monitoring engagement (5-min interval)
- [ ] CEO briefing generated Monday 8 AM
- [ ] Circuit breakers protecting all integrations
- [ ] Audit logging with hash chain integrity
- [ ] Autonomous tasks executing via Ralph Loop
- [ ] Daily health check passing
- [ ] 80%+ test coverage

## Support

- Issues: https://github.com/anthropics/claude-code/issues
- Documentation: `.specify/memory/constitution.md`
- Architecture: `specs/001-gold-tier-autonomous/plan.md`
