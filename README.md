# Digital FTE - Bronze Tier Foundation

Local-first knowledge management system that captures Gmail emails into an Obsidian vault with automated dashboard updates and Claude Code integration.

## Features

### Bronze Tier (MVP)
- ✅ **Obsidian Vault Integration**: Structured vault with Inbox, Needs_Action, and Done folders
- ✅ **Gmail Watcher**: Monitors labeled emails and creates notes automatically (3-minute polling)
- ✅ **Dynamic Dashboard**: Auto-updated with folder counts and recent activity
- ✅ **Claude Code Skills**: Agent skills for vault operations (create, read, move, search, update)
- ✅ **Local-First Architecture**: All data stored locally, no cloud dependencies
- ✅ **Privacy-First**: OAuth2 authentication, no password storage, gitignored credentials

## Quick Start

See [specs/001-bronze-tier-foundation/quickstart.md](specs/001-bronze-tier-foundation/quickstart.md) for detailed setup instructions.

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Obsidian](https://obsidian.md/) (optional, for viewing vault)
- Gmail account with API access enabled

### Installation

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd Digital-FTEs
   ```

2. **Install dependencies**
   ```bash
   cd watchers
   uv sync
   ```

3. **Configure environment**
   ```bash
   cp watchers/.env.example watchers/.env
   # Edit .env with your settings
   ```

4. **Set up Gmail API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download and save as `credentials.json` in project root

5. **Initialize vault**
   ```bash
   python scripts/setup_vault.py
   ```

6. **Start Gmail watcher**
   ```bash
   python watchers/gmail_watcher.py
   ```

## Project Structure

```
Digital-FTEs/
├── watchers/                    # Gmail watcher and utilities
│   ├── pyproject.toml          # uv project configuration
│   ├── gmail_watcher.py        # Main watcher script
│   ├── gmail_auth.py           # OAuth2 authentication
│   ├── gmail_operations.py     # Gmail API operations
│   ├── error_handler.py        # Retry logic with exponential backoff
│   ├── utils.py                # Filename sanitization, timestamps
│   └── vault_utils.py          # YAML frontmatter helpers
├── scripts/                     # Vault management scripts
│   ├── setup_vault.py          # Initialize vault structure
│   ├── create_note.py          # Create notes programmatically
│   └── update_dashboard.py     # Regenerate dashboard
├── .claude/skills/              # Claude Code agent skills
│   └── vault-operations/       # Vault operations skill
│       ├── SKILL.md            # Skill definition
│       └── references/         # Supporting documentation
├── obsidian-vault/             # Obsidian vault (created by setup)
│   ├── Inbox/                  # New items
│   ├── Needs_Action/           # Items requiring attention
│   ├── Done/                   # Completed items
│   ├── Dashboard.md            # Dynamic summary
│   └── Company_Handbook.md     # Business information
├── specs/                       # Feature specifications
│   └── 001-bronze-tier-foundation/
│       ├── spec.md             # Feature specification
│       ├── plan.md             # Implementation plan
│       ├── tasks.md            # Task breakdown
│       ├── research.md         # Research findings
│       ├── data-model.md       # Data model
│       └── contracts/          # API contracts
└── credentials.json            # Gmail API credentials (gitignored)
```

## Usage

### Gmail Watcher

Monitor Gmail for labeled emails and create vault notes automatically:

```bash
# Start watcher (runs continuously)
python watchers/gmail_watcher.py

# Stop with Ctrl+C
```

**How it works:**
1. Label emails in Gmail with "ToVault" (or your configured label)
2. Watcher polls every 3 minutes
3. New emails are converted to markdown notes in `obsidian-vault/Inbox/`
4. Dashboard updates automatically with new counts

### Manual Note Creation

Create notes programmatically using the script:

```bash
python scripts/create_note.py \
  --folder Inbox \
  --title "Meeting Notes" \
  --content "Discussion points..." \
  --tags "meeting,important"
```

### Dashboard Updates

Manually refresh the dashboard:

```bash
python scripts/update_dashboard.py
```

### Claude Code Integration

Use the `vault-operations` skill in Claude Code:

```
# Create a note
Create a new note in Inbox with title "Task" and content "Details"

# Search vault
Search the vault for "budget"

# Move note
Move note from Inbox to Needs_Action

# Update dashboard
Update the dashboard with current statistics
```

## Configuration

Edit `watchers/.env` to customize:

```bash
GMAIL_LABEL=ToVault          # Gmail label to monitor
POLL_INTERVAL=180            # Polling interval in seconds (3 minutes)
CREDENTIALS_PATH=credentials.json
TOKEN_PATH=watchers/.auth/token.json
VAULT_PATH=obsidian-vault
```

## Architecture

### Data Flow

```
Gmail → Watcher → Vault Note → Dashboard Update
         ↓
    Error Handler (Retry with exponential backoff)
```

### Note Structure

```markdown
---
title: Email Subject
created: 2026-03-29T14:30:00Z
source: gmail
sender: sender@example.com
email_date: 2026-03-29T10:00:00Z
status: inbox
tags:
  - email
---

**From:** sender@example.com
**Date:** Thu, 29 Mar 2026 10:00:00 +0000
**Message ID:** <message-id>

---

Email body content here...
```

## Development

### Running Tests

```bash
# Unit tests (when implemented)
pytest tests/unit/

# Integration tests (when implemented)
pytest tests/integration/
```

### Adding New Features

1. Create feature spec in `specs/<feature-name>/spec.md`
2. Run `/sp.plan` to generate implementation plan
3. Run `/sp.tasks` to generate task breakdown
4. Implement tasks in order
5. Update documentation

## Troubleshooting

### Gmail Authentication Issues

**Problem:** "Credentials file not found"
- **Solution:** Download `credentials.json` from Google Cloud Console and place in project root

**Problem:** "Token expired"
- **Solution:** Delete `watchers/.auth/token.json` and re-authenticate

### Watcher Not Creating Notes

**Problem:** No notes appearing in vault
- **Solution:** Check that emails have the correct label ("ToVault")
- **Solution:** Verify watcher is running (`python watchers/gmail_watcher.py`)
- **Solution:** Check logs at `watchers/logs/gmail-watcher.log`

### Dashboard Not Updating

**Problem:** Dashboard shows old counts
- **Solution:** Run `python scripts/update_dashboard.py` manually
- **Solution:** Check that notes have valid frontmatter with `created` field

## Roadmap

### Silver Tier (Planned)
- Gemini AI integration for email summarization
- File system watcher for document monitoring
- Advanced search and filtering
- Custom templates for different note types

### Gold Tier (Planned)
- Multi-source aggregation (Slack, Teams, etc.)
- Automated task extraction and scheduling
- Integration with external tools (Jira, Notion, etc.)
- Advanced analytics and insights

## Contributing

This project follows Spec-Driven Development (SDD):
1. All features start with a specification
2. Implementation follows the plan
3. Tasks are tracked and validated
4. Documentation is maintained alongside code

See `.specify/memory/constitution.md` for project principles.

## License

[Your License Here]

## Support

- **Documentation**: See `specs/` directory for detailed specifications
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Questions**: Check `specs/001-bronze-tier-foundation/quickstart.md` for setup help

---

**Status**: Bronze Tier MVP Complete ✅
**Last Updated**: 2026-03-29
