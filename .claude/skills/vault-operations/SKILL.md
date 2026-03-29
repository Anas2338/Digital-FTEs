---
name: vault-operations
description: Manage Obsidian vault operations including creating notes with proper frontmatter, reading and parsing existing notes, moving notes between folders, updating the dashboard with current statistics, and searching vault content. Use when users need to create new notes from emails or manual input, read existing vault notes to understand their content and metadata, reorganize notes by moving them between Inbox/Needs_Action/Done folders, refresh the dashboard to show current folder counts and recent activity, or search for specific content across all vault notes. Triggers when user mentions creating notes, reading vault content, moving files between folders, updating dashboard statistics, or searching the knowledge base.
---

# Vault Operations Skill

This skill provides comprehensive operations for managing the Digital FTE Obsidian vault.

## Operations

### 1. Create Note

Create a new note in the vault with proper YAML frontmatter and markdown structure.

**Parameters:**
- `folder` (required): Target folder - "Inbox", "Needs_Action", or "Done"
- `title` (required): Note title (will be sanitized for filename)
- `content` (required): Note body content in markdown
- `source` (optional): Source of note - "gmail", "manual", etc. (default: "manual")
- `sender` (optional): Email sender address (for email-sourced notes)
- `email_date` (optional): Original email timestamp in ISO 8601 format
- `tags` (optional): List of tags for categorization

**Behavior:**
1. Sanitize title for filename (remove unsafe characters, lowercase, max 50 chars)
2. Generate filename: `YYYYMMDD-HHMMSS-sanitized-title.md`
3. Create YAML frontmatter with all metadata fields
4. Write note to `obsidian-vault/{folder}/{filename}.md`
5. Automatically update dashboard with new counts

**Tool Usage:**
- Use `Write` tool to create the note file
- Use `Bash` tool to run `python scripts/create_note.py` with parameters

**Example Usage:**
```python
# Using the create_note.py script
python scripts/create_note.py \
  --folder Inbox \
  --title "Q1 Budget Review" \
  --content "Meeting notes from budget discussion..." \
  --source manual \
  --tags "meeting,budget,q1"
```

**Example Note Structure:**
```markdown
---
title: Q1 Budget Review
created: 2026-03-29T14:30:00Z
source: manual
status: inbox
tags:
  - meeting
  - budget
  - q1
---

Meeting notes from budget discussion...
```

---

### 2. Read Note

Read an existing note and parse its frontmatter and body content.

**Parameters:**
- `path` (required): Absolute or relative path to the note file

**Behavior:**
1. Read file content using Read tool
2. Parse YAML frontmatter (between `---` markers)
3. Extract body content (everything after frontmatter)
4. Return structured data with metadata and content

**Tool Usage:**
- Use `Read` tool with the note path
- Parse frontmatter manually or use vault_utils.py functions

**Example Usage:**
```python
# Read a note
from pathlib import Path
from watchers.vault_utils import parse_frontmatter

note_path = Path("obsidian-vault/Inbox/20260329-143000-test-note.md")
with open(note_path, 'r', encoding='utf-8') as f:
    content = f.read()

frontmatter, body = parse_frontmatter(content)
print(f"Title: {frontmatter['title']}")
print(f"Created: {frontmatter['created']}")
print(f"Body: {body}")
```

**Using Claude Code Tools:**
```
Use Read tool on: obsidian-vault/Inbox/20260329-143000-test-note.md
Parse the YAML frontmatter between --- markers
Extract the body content after the closing ---
```

---

### 3. Move Note

Move a note from one folder to another and update its status field.

**Parameters:**
- `source_path` (required): Current path to the note
- `target_folder` (required): Destination folder - "Inbox", "Needs_Action", or "Done"

**Behavior:**
1. Verify source file exists
2. Extract filename from source path
3. Construct target path: `obsidian-vault/{target_folder}/{filename}`
4. Move file using `mv` command
5. Read note, update status field in frontmatter
6. Update dashboard to reflect new counts

**Tool Usage:**
- Use `Bash` tool with `mv` command to move the file
- Use `Read` and `Write` tools to update the status field
- Use `Bash` tool to run `python scripts/update_dashboard.py`

**Example Usage:**
```bash
# Move note from Inbox to Needs_Action
mv "obsidian-vault/Inbox/20260329-143000-test-note.md" \
   "obsidian-vault/Needs_Action/20260329-143000-test-note.md"

# Update status field in frontmatter (read, modify, write)
# Then update dashboard
python scripts/update_dashboard.py
```

**Status Field Mapping:**
- Inbox → `status: inbox`
- Needs_Action → `status: needs-action`
- Done → `status: done`

---

### 4. Update Dashboard

Regenerate Dashboard.md with current vault statistics and recent activity.

**Parameters:**
None (operates on entire vault)

**Behavior:**
1. Count `.md` files in each folder (Inbox, Needs_Action, Done)
2. Read frontmatter from all notes to extract created timestamps
3. Sort notes by created timestamp (newest first)
4. Take first 10 notes for recent activity
5. Generate dashboard markdown with counts and wikilinks
6. Write to Dashboard.md atomically (temp file + rename)

**Tool Usage:**
- Use `Bash` tool to run `python scripts/update_dashboard.py`
- Or use `Glob` tool to find notes, `Read` tool to parse frontmatter, `Write` tool to update dashboard

**Example Usage:**
```bash
# Simple approach - use the script
python scripts/update_dashboard.py

# Manual approach using Claude Code tools
# 1. Use Glob to find all notes: obsidian-vault/**/*.md
# 2. Use Read to parse each note's frontmatter
# 3. Count notes per folder
# 4. Sort by created timestamp
# 5. Generate markdown content
# 6. Use Write to update Dashboard.md
```

**Dashboard Structure:**
```markdown
# Dashboard

## Last Updated
2026-03-29T14:30:00Z

## Folder Status
| Folder | Count | Link |
|--------|-------|------|
| Inbox | 5 | [[Inbox/]] |
| Needs Action | 3 | [[Needs_Action/]] |
| Done | 12 | [[Done/]] |

## Recent Activity
- [[Inbox/20260329-143000-test-note|Test Note]] - 2026-03-29 14:30
- [[Inbox/20260329-120000-another-note|Another Note]] - 2026-03-29 12:00
...
```

---

### 5. Search Vault

Search for content across all vault notes using pattern matching.

**Parameters:**
- `query` (required): Search pattern (supports regex)
- `case_sensitive` (optional): Case-sensitive search (default: false)
- `max_results` (optional): Maximum number of results (default: 50)

**Behavior:**
1. Use Grep tool to search all `.md` files in vault
2. Search in both frontmatter and body content
3. Return matching files with excerpts showing context
4. Limit results to max_results

**Tool Usage:**
- Use `Grep` tool with pattern and path `obsidian-vault/**/*.md`
- Use `-i` flag for case-insensitive search
- Use `head_limit` parameter to limit results

**Example Usage:**
```
# Search for "budget" in all notes (case-insensitive)
Use Grep tool:
  pattern: "budget"
  path: "obsidian-vault"
  glob: "**/*.md"
  output_mode: "content"
  -i: true
  head_limit: 50

# Search for specific sender in frontmatter
Use Grep tool:
  pattern: "sender: john@example.com"
  path: "obsidian-vault"
  glob: "**/*.md"
  output_mode: "files_with_matches"
```

---

## Tool Usage Patterns

### Read Tool
- Read existing notes to understand structure
- Parse YAML frontmatter for metadata
- Extract body content
- Verify note exists before operations

### Write Tool
- Create new notes with frontmatter
- Update dashboard content
- Modify note metadata
- Use atomic writes (temp file + rename) for safety

### Grep Tool
- Search vault content by pattern
- Find notes by tag or metadata field
- Full-text search across all notes
- Filter by file type (*.md)

### Glob Tool
- Find notes by filename pattern
- List all notes in a directory
- Discover vault structure
- Count files in folders

### Bash Tool
- Move/rename notes (`mv` command)
- Run Python scripts (create_note.py, update_dashboard.py)
- Count files (`find | wc -l`)
- Create directories (`mkdir -p`)

---

## Workflow Examples

### Create New Note Workflow

1. **Prepare metadata**: Gather title, content, source, tags
2. **Generate filename**: Timestamp + sanitized title
3. **Create frontmatter**: YAML with all required fields
4. **Write note**: Use Write tool or create_note.py script
5. **Update dashboard**: Automatically refresh counts

```bash
# Complete workflow using script
python scripts/create_note.py \
  --folder Inbox \
  --title "Important Email" \
  --content "Email body content here..." \
  --source gmail \
  --sender "sender@example.com" \
  --email-date "2026-03-29T10:00:00Z" \
  --tags "email,important"
```

### Update Dashboard Workflow

1. **Count notes**: Scan each folder for .md files
2. **Read metadata**: Parse frontmatter from all notes
3. **Sort by timestamp**: Order by created field (newest first)
4. **Generate markdown**: Format counts and recent activity
5. **Write dashboard**: Atomic update to Dashboard.md

```bash
# Simple dashboard update
python scripts/update_dashboard.py
```

### Move Note Workflow

1. **Verify source**: Check note exists at source path
2. **Move file**: Use mv to relocate to target folder
3. **Update status**: Modify frontmatter status field
4. **Update dashboard**: Refresh counts to reflect change

```bash
# Move note and update
mv "obsidian-vault/Inbox/note.md" "obsidian-vault/Needs_Action/note.md"
# Update status field in frontmatter
python scripts/update_dashboard.py
```

### Search Vault Workflow

1. **Define query**: Pattern to search for
2. **Use Grep**: Search across all .md files
3. **Review results**: Examine matching files and excerpts
4. **Open notes**: Use Read tool to view full content

```
# Search workflow
1. Grep for pattern in obsidian-vault/**/*.md
2. Review matching files
3. Read specific notes for full context
```

---

## Notes

- All operations preserve UTF-8 encoding
- Filenames are sanitized to remove unsafe characters
- Dashboard updates are atomic (temp file + rename)
- Frontmatter must be valid YAML between --- markers
- Timestamps use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Status field must match folder: inbox, needs-action, done
- Tags are optional but recommended for organization
- Search supports regex patterns for advanced queries

---

## Related Files

- `watchers/utils.py` - Filename sanitization and timestamp formatting
- `watchers/vault_utils.py` - YAML frontmatter generation and parsing
- `scripts/create_note.py` - Note creation script
- `scripts/update_dashboard.py` - Dashboard regeneration script
- `specs/001-bronze-tier-foundation/data-model.md` - Data model specification
- `specs/001-bronze-tier-foundation/contracts/vault-operations.md` - API contracts
