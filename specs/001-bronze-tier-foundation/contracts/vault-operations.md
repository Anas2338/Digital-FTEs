# Vault Operations Contracts

**Feature**: 001-bronze-tier-foundation
**Date**: 2026-03-29
**Type**: Agent Skill API Contracts

## Overview

This document defines the contracts for the `vault-operations` agent skill, which provides Claude Code with capabilities to manage the Obsidian vault.

## Skill Metadata

**Name**: `vault-operations`

**Description**: Manage Obsidian vault operations including creating notes, reading notes, moving notes, updating dashboard, and searching vault content. Use when users need to create new notes with proper frontmatter, read existing notes, reorganize vault structure, update dashboard summaries, or search for specific content across the vault.

**Triggers**:
- User mentions creating notes, adding items to vault
- User asks to read vault content, view notes
- User requests moving files, reorganizing vault
- User wants to update dashboard, refresh summary
- User needs to search vault, find specific content

---

## Operation 1: Create Note

### Purpose
Create a new markdown note in the Obsidian vault with proper YAML frontmatter.

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| folder | string | Yes | Target folder (Inbox, Needs_Action, Done) | "Inbox" |
| title | string | Yes | Note title (will be sanitized for filename) | "Q1 Budget Review" |
| content | string | Yes | Note body content (markdown) | "Meeting notes..." |
| sender | string | No | Email sender (for email-sourced notes) | "john@example.com" |
| email_date | string | No | Original email date (ISO 8601) | "2026-03-29T09:15:00" |
| tags | array | No | List of tags | ["email", "urgent"] |

### Behavior

1. Sanitize title for filename (remove unsafe characters, max 50 chars)
2. Generate timestamp-based filename: `YYYYMMDD-HHMMSS-sanitized-title.md`
3. Create YAML frontmatter with required fields
4. Format note body with metadata header
5. Write file to `obsidian-vault/{folder}/{filename}.md`
6. Update dashboard to reflect new note

### Returns

```json
{
  "success": true,
  "file_path": "obsidian-vault/Inbox/20260329-143000-q1-budget-review.md",
  "filename": "20260329-143000-q1-budget-review.md"
}
```

### Error Cases

| Error | Condition | Response |
|-------|-----------|----------|
| InvalidFolder | Folder not in [Inbox, Needs_Action, Done] | "Invalid folder: {folder}" |
| EmptyTitle | Title is empty or whitespace only | "Title cannot be empty" |
| WriteError | File system write fails | "Failed to create note: {error}" |

### Example Usage

```markdown
Create a note in Inbox folder:
- Title: "Q1 Budget Review"
- Content: "Discussed budget allocations for Q1..."
- Sender: "cfo@company.com"
- Tags: ["email", "finance"]
```

---

## Operation 2: Read Note

### Purpose
Read an existing note from the vault, including frontmatter and body content.

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| path | string | Yes | Relative path from vault root or filename | "Inbox/20260329-143000-q1-budget-review.md" |

### Behavior

1. Resolve path to absolute: `obsidian-vault/{path}`
2. Read file content using Read tool
3. Parse YAML frontmatter (between `---` markers)
4. Extract body content (after frontmatter)
5. Return structured data

### Returns

```json
{
  "success": true,
  "frontmatter": {
    "title": "Q1 Budget Review",
    "created": "2026-03-29T14:30:00",
    "source": "gmail",
    "sender": "cfo@company.com",
    "email_date": "2026-03-29T09:15:00",
    "status": "inbox",
    "tags": ["email", "finance"]
  },
  "body": "# Q1 Budget Review\n\n**From**: cfo@company.com...",
  "file_path": "obsidian-vault/Inbox/20260329-143000-q1-budget-review.md"
}
```

### Error Cases

| Error | Condition | Response |
|-------|-----------|----------|
| FileNotFound | File does not exist | "Note not found: {path}" |
| ParseError | Invalid YAML frontmatter | "Failed to parse frontmatter: {error}" |
| ReadError | File system read fails | "Failed to read note: {error}" |

### Example Usage

```markdown
Read a note from Inbox:
- Path: "Inbox/20260329-143000-q1-budget-review.md"
```

---

## Operation 3: Move Note

### Purpose
Move a note from one folder to another, updating its status field.

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| source_path | string | Yes | Current note path (relative to vault) | "Inbox/20260329-143000-note.md" |
| target_folder | string | Yes | Destination folder | "Needs_Action" |

### Behavior

1. Verify source file exists
2. Verify target folder exists
3. Extract filename from source path
4. Move file: `mv source_path target_folder/filename`
5. Read note frontmatter
6. Update status field to match target folder
7. Write updated frontmatter
8. Update dashboard to reflect move

### Returns

```json
{
  "success": true,
  "old_path": "obsidian-vault/Inbox/20260329-143000-note.md",
  "new_path": "obsidian-vault/Needs_Action/20260329-143000-note.md",
  "status_updated": "needs-action"
}
```

### Error Cases

| Error | Condition | Response |
|-------|-----------|----------|
| SourceNotFound | Source file doesn't exist | "Source note not found: {source_path}" |
| InvalidTargetFolder | Target folder invalid | "Invalid target folder: {target_folder}" |
| MoveError | File system move fails | "Failed to move note: {error}" |

### Status Mapping

| Target Folder | Status Value |
|---------------|--------------|
| Inbox | "inbox" |
| Needs_Action | "needs-action" |
| Done | "done" |

### Example Usage

```markdown
Move a note from Inbox to Needs_Action:
- Source: "Inbox/20260329-143000-note.md"
- Target: "Needs_Action"
```

---

## Operation 4: Update Dashboard

### Purpose
Regenerate Dashboard.md with current vault statistics and recent activity.

### Parameters

None (operates on entire vault state)

### Behavior

1. Count files in each folder:
   - `find obsidian-vault/Inbox -name "*.md" | wc -l`
   - `find obsidian-vault/Needs_Action -name "*.md" | wc -l`
   - `find obsidian-vault/Done -name "*.md" | wc -l`
2. Find all notes across vault
3. Read frontmatter from each note
4. Sort by `created` timestamp (descending)
5. Take first 10 for recent activity
6. Generate dashboard markdown from template
7. Write to `obsidian-vault/Dashboard.md`

### Returns

```json
{
  "success": true,
  "counts": {
    "inbox": 5,
    "needs_action": 3,
    "done": 12
  },
  "recent_notes": 10,
  "updated_at": "2026-03-29T14:30:00"
}
```

### Error Cases

| Error | Condition | Response |
|-------|-----------|----------|
| ScanError | Failed to scan folders | "Failed to scan vault: {error}" |
| WriteError | Failed to write dashboard | "Failed to update dashboard: {error}" |

### Example Usage

```markdown
Update the dashboard with current vault state
```

---

## Operation 5: Search Vault

### Purpose
Search vault content using pattern matching, returning matching notes and excerpts.

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| query | string | Yes | Search term or regex pattern | "budget" |
| case_sensitive | boolean | No | Case-sensitive search (default: false) | false |
| max_results | integer | No | Maximum results to return (default: 20) | 20 |

### Behavior

1. Use Grep tool to search vault:
   - Pattern: `{query}`
   - Path: `obsidian-vault/`
   - Glob: `**/*.md`
   - Output mode: `content`
   - Case sensitivity: `-i` flag if case_sensitive=false
2. Parse grep output for file paths and matching lines
3. Group results by file
4. Return up to max_results files with excerpts

### Returns

```json
{
  "success": true,
  "results": [
    {
      "file_path": "obsidian-vault/Inbox/20260329-143000-q1-budget.md",
      "matches": [
        {
          "line_number": 15,
          "content": "Discussed budget allocations for Q1 2026"
        }
      ]
    }
  ],
  "total_matches": 3
}
```

### Error Cases

| Error | Condition | Response |
|-------|-----------|----------|
| EmptyQuery | Query is empty | "Search query cannot be empty" |
| SearchError | Grep fails | "Search failed: {error}" |

### Example Usage

```markdown
Search vault for "budget":
- Query: "budget"
- Case sensitive: false
- Max results: 20
```

---

## Tool Usage Patterns

### Read Tool
- Read existing notes: `Read(file_path="obsidian-vault/Inbox/note.md")`
- Read dashboard: `Read(file_path="obsidian-vault/Dashboard.md")`

### Write Tool
- Create new note: `Write(file_path="obsidian-vault/Inbox/note.md", content="...")`
- Update dashboard: `Write(file_path="obsidian-vault/Dashboard.md", content="...")`

### Grep Tool
- Search vault: `Grep(pattern="query", path="obsidian-vault", glob="**/*.md", output_mode="content")`
- Find by tag: `Grep(pattern="tags:.*urgent", path="obsidian-vault", glob="**/*.md")`

### Glob Tool
- List notes in folder: `Glob(pattern="obsidian-vault/Inbox/*.md")`
- Find all notes: `Glob(pattern="obsidian-vault/**/*.md")`

### Bash Tool
- Move note: `Bash(command='mv "source.md" "target.md"')`
- Count files: `Bash(command='find obsidian-vault/Inbox -name "*.md" | wc -l')`
- Create directory: `Bash(command='mkdir -p obsidian-vault/Inbox')`

---

## Error Handling

### General Error Response Format

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "parameter": "value that caused error"
  }
}
```

### Retry Strategy

- **Transient Errors** (file system busy, temporary lock): Retry up to 3 times with 1s, 2s, 4s delays
- **Permanent Errors** (file not found, invalid parameters): Do not retry, return error immediately
- **Partial Failures** (dashboard update fails after note creation): Log error, note still created successfully

---

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Create Note | < 2 seconds | Includes dashboard update |
| Read Note | < 1 second | Single file read |
| Move Note | < 2 seconds | Includes status update and dashboard |
| Update Dashboard | < 5 seconds | Scans entire vault |
| Search Vault | < 3 seconds | For < 1000 notes |

---

## Validation Rules

### Note Creation
- Title: 1-200 characters
- Folder: Must be Inbox, Needs_Action, or Done
- Content: No size limit (reasonable for Bronze Tier)
- Sender: Valid email format if provided
- Tags: Array of strings, each 1-50 characters

### Note Move
- Source path: Must exist
- Target folder: Must be valid folder name
- No circular moves (already in target folder)

### Search
- Query: 1-500 characters
- Max results: 1-100
- Pattern: Valid regex (if using regex mode)

---

## Concurrency Considerations

**Bronze Tier**: Single-user, single-process operation assumed

**Future Enhancements**:
- File locking for concurrent dashboard updates
- Optimistic concurrency control for note updates
- Queue-based processing for batch operations
