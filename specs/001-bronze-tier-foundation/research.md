# Research Report: Bronze Tier Foundation

**Date**: 2026-03-29
**Feature**: 001-bronze-tier-foundation
**Phase**: Phase 0 - Research & Unknowns Resolution

## Overview

This document consolidates research findings for implementing the Bronze Tier Foundation feature, covering Gmail API integration, Obsidian vault structure, and agent skills patterns.

## 1. Gmail API Integration

### Decision: Use Gmail API with OAuth2 Desktop Flow

**Rationale**:
- Gmail API provides official, stable access to email data
- OAuth2 ensures secure authentication without storing passwords
- Desktop application flow suitable for local-first architecture
- Label-based filtering provides user control over captured emails

**Alternatives Considered**:
- IMAP protocol: Rejected due to less secure authentication and deprecated by Gmail
- Webhook push notifications: Rejected as too complex for Bronze Tier, requires public endpoint
- Third-party email libraries: Rejected in favor of official Google client library

### Implementation Details

**Authentication Flow**:
1. User downloads `credentials.json` from Google Cloud Console
2. First run triggers OAuth2 consent flow in browser
3. Token stored in `watchers/.auth/token.json` (gitignored)
4. Automatic token refresh handled by library

**Required Scopes**:
```python
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
```

**Token Storage Location**: `watchers/.auth/token.json`
- Gitignored for security
- Contains access_token, refresh_token, expiry
- Auto-refreshes when expired (1-hour access token lifetime)

**Label-Based Filtering**:
```python
# Get label ID by name (create if doesn't exist)
def get_label_id(service, label_name='ToVault'):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    for label in labels:
        if label['name'] == label_name:
            return label['id']

    # Create label if not found
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    created = service.users().labels().create(
        userId='me', body=label_object).execute()
    return created['id']

# Retrieve messages with label
def get_messages_with_label(service, label_id):
    response = service.users().messages().list(
        userId='me',
        labelIds=[label_id],
        maxResults=100
    ).execute()
    return response.get('messages', [])
```

**Message Content Extraction**:
```python
def get_message_details(service, message_id):
    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'
    ).execute()

    headers = message['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

    body = extract_plain_text_body(message['payload'])

    return {
        'subject': subject,
        'sender': sender,
        'date': date,
        'body': body,
        'timestamp': message['internalDate']
    }
```

**Plain Text Body Extraction**:
- Prefer `text/plain` MIME parts
- Fallback to HTML with tag stripping if plain text unavailable
- Handle multipart messages recursively
- Base64 decode body data

**Rate Limiting**:
- Gmail API quota: 1 billion units/day
- Messages.list: 5 units, Messages.get: 5 units
- 3-minute polling: 480 polls/day × 10 units = 4,800 units/day
- **Well within limits** (< 0.001% of quota)

**Error Handling**:
- Transient errors (429, 500, 502, 503, 504): Retry with exponential backoff
- Permanent errors (401, 403, 404): Log and skip
- Network errors: Retry with backoff
- Retry pattern: 1s, 2s, 4s delays (per constitution)

**Dependencies**:
```toml
[project]
name = "digital-fte-watchers"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "google-api-python-client>=2.108.0",
    "google-auth-httplib2>=0.2.0",
    "google-auth-oauthlib>=1.2.0",
    "pyyaml>=6.0.1",
    "python-dotenv>=1.0.0",
]
```

**Package Manager**: uv (Astral's fast Python package manager)
- Uses `pyproject.toml` for dependency specification (PEP 621 standard)
- Commands: `uv sync` to install dependencies, `uv add <package>` to add new ones
- Creates `uv.lock` for reproducible builds (gitignored)
- 10-100x faster than pip for dependency resolution

---

## 2. Obsidian Vault Structure

### Decision: Minimal Configuration with Manual Dashboard Updates

**Rationale**:
- Obsidian auto-generates configuration on first open
- Minimal `.obsidian/` folder sufficient for Bronze Tier
- Manual dashboard updates via Python script (no plugin dependencies)
- Standard markdown and YAML frontmatter for maximum compatibility

**Alternatives Considered**:
- Dataview plugin for dynamic queries: Rejected as adds complexity and plugin dependency
- Custom Obsidian plugin: Rejected as out of scope for Bronze Tier
- JSON-based metadata: Rejected in favor of standard YAML frontmatter

### Vault Directory Structure

```
obsidian-vault/
├── .obsidian/
│   └── workspace.json          # Minimal workspace config
├── Inbox/                      # New items
├── Needs_Action/               # Items requiring attention
├── Done/                       # Completed items
├── Dashboard.md                # Dynamic summary (updated by script)
└── Company_Handbook.md         # Static template
```

### Minimal .obsidian/workspace.json

```json
{
  "main": {
    "id": "main-workspace",
    "type": "split",
    "children": [
      {
        "id": "main-leaf",
        "type": "leaf",
        "state": {
          "type": "markdown",
          "state": {
            "file": "Dashboard.md",
            "mode": "source"
          }
        }
      }
    ]
  }
}
```

**Key Points**:
- Opens Dashboard.md by default
- Obsidian will enhance this on first open
- Can start with empty `.obsidian/` folder - Obsidian creates defaults

### YAML Frontmatter Schema

**For Email-Sourced Notes**:
```yaml
---
title: Email Subject Line
created: 2026-03-29T10:15:00
source: gmail
sender: sender@example.com
email_date: 2026-03-29T09:30:00
status: inbox
tags:
  - email
---
```

**Field Specifications**:
- `title`: Email subject (string)
- `created`: Note creation timestamp (ISO 8601 datetime)
- `source`: Always "gmail" for Bronze Tier (string)
- `sender`: Email sender address (string)
- `email_date`: Original email timestamp (ISO 8601 datetime)
- `status`: Current status - "inbox", "needs-action", or "done" (string)
- `tags`: List of tags for categorization (array)

**Parsing Rules**:
- Must start and end with `---` on separate lines
- Must be at beginning of file
- Standard YAML syntax
- Obsidian preserves unrecognized fields

### Dashboard.md Template

```markdown
# Dashboard

Last Updated: {{TIMESTAMP}}

## Folder Status

- **[Inbox](Inbox/)**: {{INBOX_COUNT}} items
- **[Needs Action](Needs_Action/)**: {{NEEDS_ACTION_COUNT}} items
- **[Done](Done/)**: {{DONE_COUNT}} items

## Recent Activity

{{RECENT_NOTES_LIST}}

## Quick Links

- [Company Handbook](Company_Handbook.md)
- [All Inbox Items](Inbox/)
- [Action Items](Needs_Action/)
```

**Update Mechanism**:
1. Python script scans folders, counts `.md` files
2. Reads frontmatter from recent notes (last 10 by created timestamp)
3. Generates markdown with wikilinks to notes
4. Atomic write: write to temp file, then rename to Dashboard.md

### Filename Sanitization

**Safe Characters**: `a-z A-Z 0-9 - _ .`

**Unsafe Characters to Remove**: `< > : " / \ | ? * # [ ]`

**Sanitization Function**:
```python
import re

def sanitize_filename(subject: str, max_length: int = 50) -> str:
    # Remove unsafe characters
    unsafe_chars = r'[<>:"/\\|?*#\[\]]'
    sanitized = re.sub(unsafe_chars, '', subject)

    # Replace spaces with hyphens
    sanitized = re.sub(r'\s+', '-', sanitized)
    sanitized = re.sub(r'-+', '-', sanitized)

    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-')

    # Ensure not empty
    if not sanitized:
        sanitized = 'untitled'

    return sanitized.lower()
```

**Filename Format**: `YYYYMMDD-HHMMSS-sanitized-subject.md`

**Examples**:
- `"Re: Q1 Budget Review [URGENT]"` → `20260329-143000-re-q1-budget-review-urgent.md`
- `"Meeting Notes: 2026/03/29"` → `20260329-100000-meeting-notes-20260329.md`

### Markdown Linking

**Wikilinks** (Recommended):
```markdown
[[20260329-143000-email-subject]]           # Link to note
[[note-name|Display Text]]                  # Link with custom text
```

**Standard Markdown**:
```markdown
[Inbox](Inbox/)                             # Folder link
[Display Text](path/to/note.md)             # Note link
```

**Best Practice**: Use wikilinks for notes, standard markdown for folders

---

## 3. Agent Skills Implementation

### Decision: Single vault-operations Skill with Multiple Operations

**Rationale**:
- Consolidates related operations in one skill
- Follows existing `.claude/skills/` pattern in project
- Reduces skill discovery overhead
- Easier to maintain single SKILL.md than multiple files

**Alternatives Considered**:
- Separate skill per operation: Rejected as too granular, increases complexity
- No skills, direct tool usage: Rejected as spec requires "All AI functionality should be implemented as Agent Skills"

### Skill Directory Structure

```
.claude/skills/vault-operations/
├── SKILL.md                    # Required - main skill definition
├── references/                 # Optional - reference docs
│   ├── frontmatter-schema.md
│   └── vault-structure.md
└── scripts/                    # Optional - helper scripts
    ├── create_note.py
    └── update_dashboard.py
```

### SKILL.md Frontmatter

```yaml
---
name: vault-operations
description: Manage Obsidian vault operations including creating notes, reading notes, moving notes, updating dashboard, and searching vault content. Use when users need to create new notes with proper frontmatter, read existing notes, reorganize vault structure, update dashboard summaries, or search for specific content across the vault. Triggers when user mentions creating notes, reading vault content, moving files, updating dashboards, or searching the knowledge base.
---
```

**Critical Pattern**: Description must include:
1. What the skill does (capabilities)
2. When to use it (trigger conditions)
3. Example scenarios

### Tool Integration Patterns

**Read Tool**:
- Read existing notes to understand structure
- Read dashboard before updating
- Parse YAML frontmatter

**Write Tool**:
- Create new notes with frontmatter
- Update dashboard content
- Atomic file writes

**Grep Tool**:
- Search vault content by pattern
- Find notes by tag or metadata
- Full-text search across vault

**Glob Tool**:
- Find notes by filename pattern
- List all notes in directory
- Discover vault structure

**Bash Tool**:
- Move/rename notes (`mv` command)
- Create directories (`mkdir`)
- Count files (`find | wc -l`)

### Skill Operations

**1. vault-create-note**:
```markdown
## Create Note

1. Determine file path: `obsidian-vault/{folder}/{filename}.md`
2. Generate YAML frontmatter with required fields
3. Add markdown content
4. Write using Write tool
5. Verify creation successful
```

**2. vault-read-note**:
```markdown
## Read Note

1. Use Read tool with absolute path
2. Parse frontmatter (between `---` markers)
3. Extract body content
4. Return structured data
```

**3. vault-move-note**:
```markdown
## Move Note

1. Use Bash tool: `mv "source.md" "destination.md"`
2. Update dashboard if moving between tracked folders
3. Verify move successful
```

**4. vault-update-dashboard**:
```markdown
## Update Dashboard

1. Count files in each folder (Inbox, Needs_Action, Done)
2. Get last 10 notes by created timestamp
3. Generate dashboard markdown from template
4. Write to Dashboard.md using Write tool
```

**5. vault-search**:
```markdown
## Search Vault

1. Use Grep tool with pattern
2. Search in `obsidian-vault/**/*.md`
3. Return matching files and excerpts
```

### Skill Invocation

**How Claude Code Discovers Skills**:
1. Reads frontmatter from all SKILL.md files (metadata always in context)
2. Matches user request against descriptions
3. Loads full SKILL.md body when triggered

**Triggering Best Practices**:
- Include action verbs (create, read, move, update, search)
- Mention specific contexts (vault, notes, dashboard)
- List concrete scenarios

---

## 4. Idempotency Patterns

### Decision: Timestamp-Based Filenames + Duplicate Detection

**Rationale**:
- Timestamp in filename (YYYYMMDD-HHMMSS) prevents most collisions
- Same email processed twice creates different filenames (different timestamps)
- Dashboard updates are idempotent (regenerate from current state)
- No database needed for duplicate tracking

**Alternatives Considered**:
- Email message ID tracking: Rejected as requires persistent state storage
- Content hash comparison: Rejected as too complex for Bronze Tier
- Database for processed emails: Rejected as violates simplicity principle

### Implementation

**Note Creation Idempotency**:
- Filename includes timestamp: `20260329-143000-subject.md`
- Same email at different times creates different files (acceptable for Bronze Tier)
- User can manually delete duplicates

**Dashboard Update Idempotency**:
- Always regenerate from current vault state
- Count files in folders
- Read frontmatter for recent notes
- Safe to run multiple times - same result

**Watcher State**:
- Track `last_message_id` in memory (not persisted)
- On restart, may reprocess recent emails (acceptable for Bronze Tier)
- Timestamp-based filenames prevent overwrites

---

## 5. Python Watcher Architecture

### Decision: Simple Polling Loop with Exponential Backoff

**Rationale**:
- Polling is simplest approach for Bronze Tier
- 3-minute interval well within API quotas
- Exponential backoff handles transient errors
- No complex event-driven infrastructure needed

**Alternatives Considered**:
- Gmail push notifications: Rejected as requires webhook endpoint and complexity
- Event-driven with message queue: Rejected as over-engineered for Bronze Tier
- Systemd/Windows Service: Rejected as deployment complexity, manual start/stop sufficient

### Watcher Components

**Main Loop**:
```python
def run(self):
    self.initialize()  # Authenticate, get label ID

    while True:
        try:
            self.process_new_messages()
            time.sleep(self.poll_interval)  # 180 seconds
        except KeyboardInterrupt:
            break
        except Exception as e:
            self.logger.error(f"Error: {e}")
            time.sleep(self.poll_interval)  # Continue after error
```

**Error Handling**:
- Transient errors (429, 500, 502, 503, 504): Retry with 1s, 2s, 4s backoff
- Permanent errors (401, 403): Log and exit (requires user intervention)
- Network errors: Retry with backoff
- Per-message errors: Log and continue with next message

**Logging**:
- File: `watchers/logs/gmail-watcher.log`
- Format: `timestamp - name - level - message`
- Levels: INFO (normal operation), ERROR (failures), DEBUG (detailed)

**Process Management**:
- Start: `python watchers/gmail_watcher.py`
- Stop: Ctrl+C (graceful shutdown)
- No daemon mode for Bronze Tier (manual start/stop)

---

## Summary of Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Gmail Auth** | OAuth2 desktop flow | Secure, official, no password storage |
| **Email Filtering** | Label-based (ToVault) | User control, simple implementation |
| **Content Extraction** | Plain text only | Avoids HTML parsing complexity |
| **Vault Config** | Minimal .obsidian/ | Obsidian auto-generates rest |
| **Dashboard Updates** | Python script regeneration | No plugin dependencies |
| **Filename Format** | Timestamp + sanitized subject | Prevents collisions, human-readable |
| **Agent Skills** | Single vault-operations skill | Consolidates related operations |
| **Idempotency** | Timestamp-based filenames | Simple, no state tracking needed |
| **Watcher Architecture** | Polling with exponential backoff | Simple, reliable, within quotas |
| **Error Handling** | Retry transient, log permanent | Follows constitution requirements |

---

## Next Steps

1. ✅ Research complete - all unknowns resolved
2. ⏳ Phase 1: Generate data-model.md
3. ⏳ Phase 1: Generate contracts/vault-operations.md
4. ⏳ Phase 1: Generate quickstart.md
5. ⏳ Update agent context
6. ⏳ Re-evaluate Constitution Check

---

**Research Status**: ✅ COMPLETE
**Date Completed**: 2026-03-29
**Ready for Phase 1**: YES
