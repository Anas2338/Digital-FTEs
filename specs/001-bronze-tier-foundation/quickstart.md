# Quickstart Guide: Bronze Tier Foundation

**Feature**: 001-bronze-tier-foundation
**Date**: 2026-03-29
**Estimated Setup Time**: 30-45 minutes

## Overview

This guide walks you through setting up the Bronze Tier Foundation: an Obsidian vault with automated Gmail monitoring that captures labeled emails as markdown notes.

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed ([python.org](https://python.org))
- **uv** package manager installed ([docs.astral.sh/uv](https://docs.astral.sh/uv/))
- **Obsidian** desktop application ([obsidian.md](https://obsidian.md))
- **Gmail account** with access to Google Cloud Console
- **Git** (already configured for this project)

## Setup Steps

### Step 1: Install Python Dependencies

```bash
# Navigate to project root
cd /d/GIAIC/Agentic-AI/Digital-FTEs

# Install dependencies using uv
uv pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv pyyaml
```

**Expected Output**: Dependencies installed successfully

**Troubleshooting**:
- If `uv` not found: Install via `pip install uv` or follow [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- If Python version error: Verify Python 3.11+ with `python --version`

---

### Step 2: Configure Gmail API Credentials

#### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project: "Digital FTE Bronze Tier"
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

#### 2.2 Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure consent screen (if prompted):
   - User Type: External
   - App name: "Digital FTE"
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `gmail.readonly`
4. Application type: "Desktop app"
5. Name: "Gmail Watcher"
6. Click "Create"
7. Download credentials JSON file

#### 2.3 Save Credentials

```bash
# Copy downloaded file to project root
cp ~/Downloads/client_secret_*.json credentials.json

# Verify file exists
ls -la credentials.json
```

**Security Note**: `credentials.json` is gitignored and will not be committed.

---

### Step 3: Initialize Obsidian Vault

```bash
# Run vault initialization script
python scripts/setup_vault.py
```

**What This Does**:
- Creates `obsidian-vault/` directory
- Creates folders: `Inbox/`, `Needs_Action/`, `Done/`
- Creates `.obsidian/workspace.json` configuration
- Creates `Dashboard.md` with initial template
- Creates `Company_Handbook.md` with template

**Expected Output**:
```
✓ Created obsidian-vault directory
✓ Created Inbox folder
✓ Created Needs_Action folder
✓ Created Done folder
✓ Created .obsidian configuration
✓ Created Dashboard.md
✓ Created Company_Handbook.md
Vault initialized successfully at: obsidian-vault/
```

**Verify**:
```bash
ls -la obsidian-vault/
# Should show: .obsidian/, Inbox/, Needs_Action/, Done/, Dashboard.md, Company_Handbook.md
```

---

### Step 4: Configure Gmail Label

#### 4.1 Create Label in Gmail

1. Open [Gmail](https://mail.google.com)
2. Click "More" in left sidebar
3. Click "Create new label"
4. Name: "ToVault"
5. Click "Create"

#### 4.2 Test Label

1. Send yourself a test email
2. Apply "ToVault" label to the email
3. Verify label appears in Gmail sidebar

**Alternative Label Name**: If you prefer a different label name, update `.env` file (Step 5)

---

### Step 5: Configure Environment Variables

```bash
# Create .env file
cat > watchers/.env <<'EOF'
GMAIL_LABEL=ToVault
POLL_INTERVAL=180
CREDENTIALS_PATH=credentials.json
TOKEN_PATH=watchers/.auth/token.json
EOF

# Create auth directory
mkdir -p watchers/.auth
```

**Configuration Options**:

| Variable | Default | Description |
|----------|---------|-------------|
| GMAIL_LABEL | ToVault | Gmail label to monitor |
| POLL_INTERVAL | 180 | Seconds between checks (3 minutes) |
| CREDENTIALS_PATH | credentials.json | Path to OAuth2 credentials |
| TOKEN_PATH | watchers/.auth/token.json | Path to store access token |

---

### Step 6: First Run - Authenticate Gmail

```bash
# Start Gmail watcher
python watchers/gmail_watcher.py
```

**What Happens**:
1. Browser opens automatically
2. Google OAuth consent screen appears
3. Sign in with your Gmail account
4. Grant permissions (read-only access)
5. Browser shows "Authentication successful"
6. Watcher starts monitoring

**Expected Output**:
```
[2026-03-29 14:30:00] INFO - GmailWatcher - Initialized with label: ToVault
[2026-03-29 14:30:00] INFO - GmailWatcher - Starting watcher (polling every 180s)
[2026-03-29 14:30:00] INFO - GmailWatcher - Processed 0 new messages
```

**Troubleshooting**:
- **Browser doesn't open**: Check firewall settings, try manual URL from console
- **Permission denied**: Verify Gmail API enabled in Cloud Console
- **Invalid credentials**: Re-download credentials.json from Cloud Console

---

### Step 7: Test Email Capture

#### 7.1 Send Test Email

1. Send email to yourself with subject: "Test - Bronze Tier Setup"
2. Apply "ToVault" label to the email
3. Wait up to 3 minutes for watcher to detect

#### 7.2 Verify Note Created

```bash
# Check Inbox folder
ls -la obsidian-vault/Inbox/

# Should show new file like: 20260329-143000-test-bronze-tier-setup.md
```

#### 7.3 View Note Content

```bash
# Read the created note
cat obsidian-vault/Inbox/20260329-*.md
```

**Expected Content**:
```markdown
---
title: Test - Bronze Tier Setup
created: 2026-03-29T14:30:00
source: gmail
sender: your-email@gmail.com
email_date: 2026-03-29T14:25:00
status: inbox
tags:
  - email
---

# Test - Bronze Tier Setup

**From**: your-email@gmail.com
**Date**: 2026-03-29T14:25:00
**Source**: gmail

---

[Email body content]
```

---

### Step 8: Open Vault in Obsidian

1. Launch Obsidian application
2. Click "Open folder as vault"
3. Navigate to: `/d/GIAIC/Agentic-AI/Digital-FTEs/obsidian-vault`
4. Click "Open"

**What You'll See**:
- Left sidebar: Folders (Inbox, Needs_Action, Done)
- Main panel: Dashboard.md with folder counts and recent activity
- File explorer: All notes visible

**Verify Dashboard**:
- Inbox count should show 1 (your test email)
- Recent Activity should list the test note
- All links should be clickable

---

### Step 9: Test Claude Code Integration

#### 9.1 Verify Agent Skill

```bash
# Check vault-operations skill exists
ls -la .claude/skills/vault-operations/SKILL.md
```

#### 9.2 Test Note Creation

In Claude Code, try:
```
Create a note in Inbox with title "Manual Test Note" and content "Testing vault operations skill"
```

**Expected Behavior**:
- Claude Code uses vault-operations skill
- New note created in `obsidian-vault/Inbox/`
- Dashboard updated with new count

#### 9.3 Test Note Reading

```
Read the note titled "Manual Test Note" from Inbox
```

**Expected Behavior**:
- Claude Code displays note content including frontmatter

---

### Step 10: Verify Dashboard Updates

```bash
# Manually trigger dashboard update (if needed)
python scripts/update_dashboard.py
```

**Check Dashboard**:
1. Open `obsidian-vault/Dashboard.md` in Obsidian
2. Verify folder counts are accurate
3. Verify recent activity shows last 10 notes
4. Verify all wikilinks work

---

## Daily Usage

### Starting the Watcher

```bash
# Start in foreground (see logs in terminal)
python watchers/gmail_watcher.py

# Or start in background (Linux/Mac)
nohup python watchers/gmail_watcher.py > watchers/logs/watcher.out 2>&1 &

# Or start in background (Windows)
start /B python watchers/gmail_watcher.py
```

### Stopping the Watcher

```bash
# Foreground: Press Ctrl+C

# Background: Find and kill process
ps aux | grep gmail_watcher
kill <PID>
```

### Processing Emails

1. Apply "ToVault" label to emails in Gmail
2. Wait up to 3 minutes for watcher to detect
3. Check `obsidian-vault/Inbox/` for new notes
4. Open Obsidian to view and organize

### Organizing Notes

**In Obsidian**:
1. Open note from Inbox
2. Drag to Needs_Action or Done folder
3. Dashboard updates automatically

**Via Claude Code**:
```
Move the note "20260329-143000-test-note.md" from Inbox to Needs_Action
```

---

## Verification Checklist

After setup, verify:

- [ ] Python 3.11+ installed and accessible
- [ ] uv package manager installed
- [ ] Gmail API enabled in Google Cloud Console
- [ ] OAuth2 credentials downloaded as `credentials.json`
- [ ] Obsidian vault initialized with all folders
- [ ] Gmail label "ToVault" created
- [ ] Environment variables configured in `watchers/.env`
- [ ] Gmail watcher authenticated successfully
- [ ] Test email captured as note in Inbox
- [ ] Obsidian opens vault successfully
- [ ] Dashboard shows accurate counts
- [ ] Claude Code vault-operations skill works
- [ ] Watcher logs to `watchers/logs/gmail-watcher.log`

---

## Troubleshooting

### Watcher Not Detecting Emails

**Check**:
1. Watcher is running: `ps aux | grep gmail_watcher`
2. Label name matches `.env` configuration
3. Email has correct label applied
4. Check logs: `tail -f watchers/logs/gmail-watcher.log`

**Common Issues**:
- Label name mismatch (case-sensitive)
- Token expired (delete `watchers/.auth/token.json` and re-authenticate)
- Network connectivity issues

### Dashboard Not Updating

**Check**:
1. Dashboard.md file permissions (should be writable)
2. Notes have valid frontmatter
3. Manually run: `python scripts/update_dashboard.py`

**Fix**:
```bash
# Regenerate dashboard
python scripts/update_dashboard.py --force
```

### Obsidian Not Opening Vault

**Check**:
1. Vault path is correct
2. `.obsidian/` folder exists
3. No file permission issues

**Fix**:
```bash
# Reinitialize vault
python scripts/setup_vault.py --force
```

### Claude Code Skill Not Working

**Check**:
1. Skill file exists: `.claude/skills/vault-operations/SKILL.md`
2. Skill frontmatter is valid YAML
3. Restart Claude Code session

---

## Next Steps

After successful setup:

1. **Customize Company Handbook**: Edit `obsidian-vault/Company_Handbook.md` with your business information
2. **Configure Additional Labels**: Create more Gmail labels for categorization
3. **Explore Agent Skills**: Try different vault operations via Claude Code
4. **Monitor Logs**: Check `watchers/logs/gmail-watcher.log` for activity
5. **Plan Silver Tier**: Consider MCP server implementation for advanced features

---

## Support

**Documentation**:
- Specification: `specs/001-bronze-tier-foundation/spec.md`
- Implementation Plan: `specs/001-bronze-tier-foundation/plan.md`
- Data Model: `specs/001-bronze-tier-foundation/data-model.md`

**Logs**:
- Watcher logs: `watchers/logs/gmail-watcher.log`
- Error logs: Check console output

**Common Commands**:
```bash
# Check watcher status
ps aux | grep gmail_watcher

# View recent logs
tail -20 watchers/logs/gmail-watcher.log

# Count notes in Inbox
ls obsidian-vault/Inbox/*.md | wc -l

# Search vault
grep -r "search term" obsidian-vault/ --include="*.md"
```

---

**Setup Complete!** Your Bronze Tier Foundation is ready for automated email capture and knowledge management.
