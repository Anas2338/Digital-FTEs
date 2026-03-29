# Data Model: Bronze Tier Foundation

**Feature**: 001-bronze-tier-foundation
**Date**: 2026-03-29
**Phase**: Phase 1 - Design

## Overview

This document defines the data structures and entities for the Bronze Tier Foundation feature. All data is stored as markdown files with YAML frontmatter in the Obsidian vault.

## Core Entities

### 1. Note

**Description**: Individual markdown file representing a captured email or manually created item.

**Storage**: `obsidian-vault/{folder}/{filename}.md`

**Filename Format**: `YYYYMMDD-HHMMSS-sanitized-subject.md`
- Example: `20260329-143000-re-q1-budget-review.md`

**Frontmatter Schema**:
```yaml
---
title: string                    # Email subject or note title
created: datetime                # ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
source: string                   # "gmail" for Bronze Tier
sender: string                   # Email address of sender
email_date: datetime             # Original email timestamp (ISO 8601)
status: enum                     # "inbox" | "needs-action" | "done"
tags: array<string>              # List of tags (e.g., ["email", "urgent"])
---
```

**Body Structure**:
```markdown
# {title}

**From**: {sender}
**Date**: {email_date}
**Source**: {source}

---

{email_body_content}
```

**Field Specifications**:

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| title | string | Yes | 1-200 chars | "Q1 Budget Review" |
| created | datetime | Yes | ISO 8601 | "2026-03-29T14:30:00" |
| source | string | Yes | Must be "gmail" | "gmail" |
| sender | string | Yes | Valid email format | "john@example.com" |
| email_date | datetime | Yes | ISO 8601 | "2026-03-29T09:15:00" |
| status | enum | Yes | inbox/needs-action/done | "inbox" |
| tags | array | No | Array of strings | ["email", "urgent"] |

**State Transitions**:
```
inbox → needs-action → done
  ↓           ↓
 done       inbox
```

**Validation Rules**:
- Filename must match pattern: `\d{8}-\d{6}-.+\.md`
- Frontmatter must be valid YAML
- Status must be one of three allowed values
- Created timestamp must not be in future
- Email_date should be before or equal to created

---

### 2. Dashboard

**Description**: Special note that aggregates vault statistics and recent activity.

**Storage**: `obsidian-vault/Dashboard.md`

**Structure**:
```markdown
# Dashboard

Last Updated: {timestamp}

## Folder Status

- **[Inbox](Inbox/)**: {count} items
- **[Needs Action](Needs_Action/)**: {count} items
- **[Done](Done/)**: {count} items

## Recent Activity

- [[{filename}]] - {created_timestamp}
- [[{filename}]] - {created_timestamp}
... (last 10 notes)

## Quick Links

- [Company Handbook](Company_Handbook.md)
- [All Inbox Items](Inbox/)
- [Action Items](Needs_Action/)
```

**Dynamic Fields**:

| Field | Type | Source | Update Trigger |
|-------|------|--------|----------------|
| Last Updated | datetime | System clock | Every dashboard update |
| Inbox count | integer | File count in Inbox/ | Note created/moved/deleted |
| Needs Action count | integer | File count in Needs_Action/ | Note moved |
| Done count | integer | File count in Done/ | Note moved |
| Recent Activity | array | Last 10 notes by created | Note created |

**Update Mechanism**:
1. Scan folders for `.md` files
2. Count files per folder
3. Read frontmatter from all notes
4. Sort by `created` timestamp (descending)
5. Take first 10 for recent activity
6. Generate markdown from template
7. Atomic write to Dashboard.md

**Concurrency Handling**:
- Single writer (dashboard update script)
- Read-modify-write with file locking (if available)
- Fallback: Overwrite entire file (acceptable for Bronze Tier)

---

### 3. Company Handbook

**Description**: Static template for documenting business processes and information.

**Storage**: `obsidian-vault/Company_Handbook.md`

**Structure**:
```markdown
# Company Handbook

Last Updated: {manual_timestamp}

## Business Information

- **Company Name**: [Your Company]
- **Industry**: [Your Industry]
- **Founded**: [Date]

## Key Contacts

| Name | Role | Email | Phone |
|------|------|-------|-------|
| [Name] | [Role] | [Email] | [Phone] |

## Business Processes

### Process 1: [Name]

**Description**: [What this process does]

**Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Responsible**: [Person/Role]
**Frequency**: [How often]

## Guidelines

### Communication Guidelines

[Guidelines for internal/external communication]

### Decision-Making

[How decisions are made]

## Resources

- [Link to resource 1]
- [Link to resource 2]
```

**Update Pattern**: Manual updates by user (not automated)

---

### 4. Email Event

**Description**: Transient data structure representing a Gmail message to be processed.

**Storage**: In-memory only (not persisted)

**Structure**:
```python
{
    'id': str,              # Gmail message ID
    'subject': str,         # Email subject line
    'sender': str,          # Sender email address
    'date': str,            # Email date header
    'body': str,            # Plain text body content
    'timestamp': str        # Gmail internal timestamp (milliseconds)
}
```

**Lifecycle**:
1. Retrieved from Gmail API
2. Processed into Note entity
3. Discarded after note creation

**Transformation to Note**:
```python
email_event → Note:
    filename = format_timestamp(timestamp) + "-" + sanitize(subject) + ".md"
    frontmatter.title = subject
    frontmatter.created = format_iso8601(now())
    frontmatter.source = "gmail"
    frontmatter.sender = sender
    frontmatter.email_date = parse_date(date)
    frontmatter.status = "inbox"
    frontmatter.tags = ["email"]
    body = format_email_body(subject, sender, date, body)
```

---

### 5. Watcher State

**Description**: Runtime state of the Gmail watcher process.

**Storage**: In-memory (not persisted for Bronze Tier)

**Structure**:
```python
{
    'last_message_id': str | None,     # Last processed Gmail message ID
    'label_id': str,                   # Gmail label ID for "ToVault"
    'poll_interval': int,              # Seconds between polls (180)
    'error_count': int,                # Consecutive errors (for circuit breaker)
    'last_poll_time': datetime,        # Timestamp of last successful poll
    'is_running': bool                 # Watcher running status
}
```

**State Transitions**:
```
STOPPED → INITIALIZING → RUNNING → STOPPED
              ↓              ↓
           ERROR ←──────────┘
              ↓
          STOPPED
```

**Persistence Strategy** (Bronze Tier):
- Not persisted to disk
- Lost on restart (acceptable - may reprocess recent emails)
- Future enhancement: Persist to `.watcher-state.json`

---

## Folder Structure

### Inbox

**Path**: `obsidian-vault/Inbox/`

**Purpose**: New items requiring initial review

**Contents**: Notes with `status: inbox`

**Lifecycle**: Notes created here by watcher, moved by user to Needs_Action or Done

---

### Needs_Action

**Path**: `obsidian-vault/Needs_Action/`

**Purpose**: Items requiring user action or follow-up

**Contents**: Notes with `status: needs-action`

**Lifecycle**: Notes moved here from Inbox, moved to Done when complete

---

### Done

**Path**: `obsidian-vault/Done/`

**Purpose**: Completed or archived items

**Contents**: Notes with `status: done`

**Lifecycle**: Notes moved here from Inbox or Needs_Action, permanent archive

---

## Data Relationships

```
Gmail API
    ↓
Email Event (transient)
    ↓
Note (persisted in Inbox/)
    ↓
Dashboard (aggregates Note metadata)
    ↑
Needs_Action/ ← Note (moved by user)
    ↓
Done/ ← Note (moved by user)
```

**Relationship Rules**:
- One Email Event creates one Note
- Dashboard references multiple Notes (last 10)
- Notes can move between folders (state transition)
- Folder location should match Note.status (consistency rule)

---

## Data Validation

### Note Validation

**On Creation**:
- Frontmatter must be valid YAML
- All required fields present
- Status is valid enum value
- Timestamps are valid ISO 8601
- Sender is valid email format

**On Move**:
- Target folder exists
- Status updated to match folder
- Dashboard updated after move

### Dashboard Validation

**On Update**:
- All folder counts are non-negative integers
- Recent activity list has ≤ 10 items
- All wikilinks reference existing notes
- Last Updated timestamp is current

---

## Data Migration

**Bronze Tier**: No migration needed (greenfield implementation)

**Future Considerations**:
- Schema versioning in frontmatter (`schema_version: 1`)
- Migration scripts for schema changes
- Backward compatibility for older notes

---

## Performance Considerations

### File System Operations

**Expected Scale** (Bronze Tier):
- Total notes: < 1000
- Notes per folder: < 500
- Dashboard updates: Every note creation/move

**Performance Targets**:
- Note creation: < 2 seconds
- Dashboard update: < 5 seconds
- Folder scan: < 1 second

**Optimization Strategies**:
- Cache folder counts (invalidate on change)
- Incremental dashboard updates (future enhancement)
- Batch operations where possible

---

## Data Integrity

### Consistency Rules

1. **Folder-Status Consistency**: Note location should match status field
2. **Dashboard Accuracy**: Counts should match actual file counts
3. **Timestamp Ordering**: created ≤ current time
4. **Unique Filenames**: No duplicate filenames in same folder

### Integrity Checks

**On Note Creation**:
- Verify file written successfully
- Verify frontmatter parseable
- Update dashboard atomically

**On Note Move**:
- Verify source file exists
- Verify target folder exists
- Update status field
- Update dashboard

**On Dashboard Update**:
- Verify all referenced notes exist
- Verify counts match reality
- Atomic write (temp file + rename)

---

## Summary

**Total Entities**: 5 (Note, Dashboard, Handbook, Email Event, Watcher State)

**Persisted Entities**: 3 (Note, Dashboard, Handbook)

**Transient Entities**: 2 (Email Event, Watcher State)

**Storage Format**: Markdown with YAML frontmatter

**Total Files** (initial state):
- 0 notes (grows over time)
- 1 Dashboard.md
- 1 Company_Handbook.md
- 1 .obsidian/workspace.json

**Data Flow**: Gmail API → Email Event → Note → Dashboard
