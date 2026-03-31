# Digital FTE - Quick Start Guide

**Status**: ✅ All code complete - Ready for testing

This guide will get you from zero to a working Digital FTE system in ~30 minutes.

---

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] uv package manager installed (`pip install uv`)
- [ ] Node.js 18+ installed (for WhatsApp)
- [ ] Obsidian installed
- [ ] Google account with Gmail access
- [ ] Claude Code CLI or desktop app

---

## Step 1: Install Dependencies (5 minutes)

```bash
# Clone and navigate to project
cd Digital-FTEs

# Install watcher dependencies
cd watchers
uv sync
cd ..

# Install MCP server dependencies
cd mcp-servers/digital-fte-server
uv sync
cd ../..

# Install WhatsApp bridge (optional)
cd watchers/whatsapp_watcher
npm install
cd ../..
```

**Checkpoint**: Run `uv --version` and verify it shows version info.

---

## Step 2: Set Up Gmail API (10-15 minutes)

**This is required for email functionality.**

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name: "Digital FTE"
4. Click "Create"

### 2.2 Enable Gmail API

1. In the search bar, type "Gmail API"
2. Click "Gmail API" → "Enable"

### 2.3 Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. User Type: **External**
3. Click "Create"
4. Fill in:
   - App name: "Digital FTE"
   - User support email: your email
   - Developer contact: your email
5. Click "Save and Continue"
6. Scopes: Click "Add or Remove Scopes"
   - Search for "gmail"
   - Select: `gmail.readonly` and `gmail.send`
   - Click "Update" → "Save and Continue"
7. Test users: Click "Add Users"
   - Add your email address
   - Click "Save and Continue"
8. Click "Back to Dashboard"

### 2.4 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **Desktop app**
4. Name: "Digital FTE Desktop"
5. Click "Create"
6. Click "Download JSON"
7. Rename downloaded file to `credentials.json`
8. Move to project root: `Digital-FTEs/credentials.json`

### 2.5 Test Authentication

```bash
# From project root
python test_gmail_auth.py
```

**Expected**:
- Browser window opens
- Sign in to Google
- Grant permissions
- See: "✓ Gmail authentication successful!"
- Token saved to `watchers/.auth/gmail_token.json`

**Checkpoint**: Verify `watchers/.auth/gmail_token.json` exists.

---

## Step 3: Initialize Database (1 minute)

```bash
python -c "from watchers.shared.database import Database; Database()"
```

**Checkpoint**: Verify `watchers/watchers.db` file exists.

---

## Step 4: Start MCP Server (2 minutes)

```bash
cd mcp-servers/digital-fte-server
uvicorn server:app --host 0.0.0.0 --port 8000 &
cd ../..
```

**Test**:
```bash
curl http://localhost:8000/health
```

**Expected**: `{"status":"healthy"}`

**Checkpoint**: MCP server responds to health check.

---

## Step 5: Validate Setup (1 minute)

```bash
python scripts/setup/validate_setup.py
```

**Expected output**:
```
✓ Database validation passed
✓ Vault structure validation passed
✓ Watcher health check passed
✓ MCP server health check passed
✓ Scheduler validation passed
✓ Agent skills validation passed

SUMMARY: 6/6 tests passed
```

**Checkpoint**: All 6 tests pass.

---

## Step 6: Test Gmail Integration (5 minutes)

### 6.1 Create Gmail Label

1. Open Gmail in browser
2. Click "Settings" (gear icon) → "See all settings"
3. Go to "Labels" tab
4. Scroll to "Labels" section
5. Click "Create new label"
6. Name: `ToVault`
7. Click "Create"

### 6.2 Start Gmail Watcher

```bash
cd watchers
python -m gmail_watcher.watcher &
cd ..
```

**Expected output**:
```
[INFO] Initializing Gmail watcher...
[INFO] Label: ToVault
[OK] Gmail API authenticated successfully
[INFO] Label ID: Label_xxx
[INFO] Starting watcher loop...
```

### 6.3 Test Email Capture

1. Send yourself a test email
2. In Gmail, apply label "ToVault" to the email
3. Wait 3 minutes (polling interval)
4. Check `obsidian-vault/Inbox/` for new note

**Expected**: Note created with email subject, sender, date, body.

**Checkpoint**: Email appears as note in Obsidian vault.

---

## Step 7: Test Send Email Tool (5 minutes)

### 7.1 Test via Python

```bash
cd mcp-servers/digital-fte-server
python -c "
from tools.send_email import SendEmailTool
tool = SendEmailTool()
result = tool.execute(
    recipient='your-email@gmail.com',
    subject='Test from Digital FTE',
    body='This is a test email from the Digital FTE system.'
)
print(result)
"
cd ../..
```

**Expected**:
```json
{
  "success": true,
  "message_id": "...",
  "recipient": "your-email@gmail.com",
  "subject": "Test from Digital FTE"
}
```

### 7.2 Test via MCP Server

```bash
curl -X POST http://localhost:8000/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "send-email",
    "parameters": {
      "recipient": "your-email@gmail.com",
      "subject": "Test via MCP",
      "body": "This email was sent via the MCP server."
    }
  }'
```

**Expected**: Email sent, check your inbox.

**Checkpoint**: Receive test email in Gmail.

---

## Step 8: Test Approval Workflow (5 minutes)

### 8.1 Queue an Action

```bash
curl -X POST http://localhost:8000/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "send-email",
    "parameters": {
      "recipient": "someone@example.com",
      "subject": "Important Business Email",
      "body": "This requires approval."
    }
  }'
```

**Expected**:
```json
{
  "status": "pending_approval",
  "action_id": "action-20260331...",
  "message": "Action queued for approval"
}
```

### 8.2 Check Approval Queue

```bash
cd mcp-servers/digital-fte-server
python -m approval.cli list
cd ../..
```

**Expected**: Shows pending action with details.

### 8.3 Approve Action

```bash
cd mcp-servers/digital-fte-server
python -m approval.cli approve action-20260331...
cd ../..
```

**Expected**: Action approved and executed, email sent.

**Checkpoint**: Approval workflow works end-to-end.

---

## Step 9: Open Obsidian Vault (2 minutes)

1. Open Obsidian
2. Click "Open folder as vault"
3. Navigate to `Digital-FTEs/obsidian-vault`
4. Click "Open"

**Explore**:
- `Inbox/` - Captured emails
- `Approvals/` - Pending approvals
- `Content_Queue/` - Scheduled LinkedIn posts
- `Schedules/` - Scheduled tasks

**Checkpoint**: Obsidian vault opens and shows folder structure.

---

## Step 10: Test with Claude Code (Optional)

If you have Claude Code installed:

```bash
claude-code "Check watcher status"
```

**Expected**: Claude uses watcher-status skill to report health.

```bash
claude-code "Send a test email to myself"
```

**Expected**: Claude queues email for approval.

---

## What's Next?

### Immediate Testing
- [ ] Send more test emails with ToVault label
- [ ] Test approval workflow with different action types
- [ ] Create a scheduled LinkedIn post in Content_Queue/
- [ ] Create a complex task in Needs_Action/ to trigger reasoning loop

### Optional Setup
- [ ] Set up WhatsApp watcher (requires phone authentication)
- [ ] Set up LinkedIn watcher (requires session cookies)
- [ ] Configure scheduled tasks (daily reports, weekly summaries)
- [ ] Customize approval rules in `mcp-servers/digital-fte-server/approval/classifier.py`

### Production Readiness
- [ ] Set up systemd services (Linux) or Task Scheduler (Windows) for watchers
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Create backup strategy for database and vault
- [ ] Review security settings and rate limits

---

## Troubleshooting

### "credentials.json not found"
- Ensure file is in project root: `Digital-FTEs/credentials.json`
- Check file name is exactly `credentials.json` (case-sensitive)

### "Token has been expired or revoked"
```bash
rm watchers/.auth/gmail_token.json
python test_gmail_auth.py
```

### "MCP server not responding"
```bash
# Check if running
curl http://localhost:8000/health

# Restart
cd mcp-servers/digital-fte-server
pkill -f uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 &
```

### "Watcher not capturing emails"
- Verify label "ToVault" exists in Gmail
- Check watcher logs: `watchers/logs/gmail_watcher.log`
- Verify polling interval (default: 180 seconds = 3 minutes)

### "Validation tests failing"
```bash
# Re-initialize database
python -c "from watchers.shared.database import Database; Database()"

# Re-run validation
python scripts/setup/validate_setup.py
```

---

## Documentation

- **Gmail Setup**: [docs/gmail-setup-guide.md](docs/gmail-setup-guide.md)
- **Implementation Status**: [docs/implementation-status.md](docs/implementation-status.md)
- **API Migration**: [docs/migration-to-official-apis.md](docs/migration-to-official-apis.md)
- **Full README**: [README.md](README.md)

---

## Support

- Check logs: `watchers/logs/`
- Review database: `sqlite3 watchers/watchers.db`
- Inspect vault: `obsidian-vault/`
- Run validation: `python scripts/setup/validate_setup.py`

---

**Estimated Total Time**: 30-40 minutes
**Status**: ✅ Ready to test
**Last Updated**: 2026-03-31
