# Frontmatter Schema Reference

This document defines the YAML frontmatter schema for notes in the Digital FTE Obsidian vault.

## Standard Fields

All notes should include these frontmatter fields:

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Note title (human-readable) | `"Q1 Budget Review"` |
| `created` | datetime | Note creation timestamp (ISO 8601) | `"2026-03-29T14:30:00Z"` |
| `source` | string | Source of the note | `"gmail"`, `"manual"` |
| `status` | string | Current workflow status | `"inbox"`, `"needs-action"`, `"done"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `sender` | string | Email sender address (for email-sourced notes) | `"john@example.com"` |
| `email_date` | datetime | Original email timestamp (ISO 8601) | `"2026-03-29T10:00:00Z"` |
| `tags` | array | List of tags for categorization | `["email", "urgent", "budget"]` |

## Field Specifications

### title
- **Type**: String
- **Required**: Yes
- **Description**: Human-readable title for the note
- **Constraints**:
  - Should be descriptive and concise
  - Used in dashboard recent activity list
  - Displayed in Obsidian note list
- **Example**: `"Meeting Notes: Q1 Planning"`

### created
- **Type**: Datetime (ISO 8601 format)
- **Required**: Yes
- **Description**: Timestamp when the note was created in the vault
- **Format**: `YYYY-MM-DDTHH:MM:SSZ`
- **Constraints**:
  - Must be valid ISO 8601 datetime
  - Timezone should be UTC (Z suffix)
  - Used for sorting in dashboard recent activity
- **Example**: `"2026-03-29T14:30:22Z"`

### source
- **Type**: String
- **Required**: Yes
- **Description**: Identifies where the note originated
- **Valid Values**:
  - `"gmail"` - Created from Gmail watcher
  - `"manual"` - Created manually by user or Claude Code
  - Future: `"file-watcher"`, `"api"`, etc.
- **Example**: `"gmail"`

### status
- **Type**: String
- **Required**: Yes
- **Description**: Current workflow status of the note
- **Valid Values**:
  - `"inbox"` - New item requiring initial review
  - `"needs-action"` - Task requiring attention or follow-up
  - `"done"` - Completed item for reference
- **Constraints**:
  - Must match the folder location:
    - Inbox folder → `"inbox"`
    - Needs_Action folder → `"needs-action"`
    - Done folder → `"done"`
  - Should be updated when note is moved between folders
- **Example**: `"inbox"`

### sender
- **Type**: String
- **Required**: No (only for email-sourced notes)
- **Description**: Email address of the sender
- **Constraints**:
  - Only applicable when `source: gmail`
  - Should be valid email format
  - Used for filtering and searching
- **Example**: `"john.doe@example.com"`

### email_date
- **Type**: Datetime (ISO 8601 format)
- **Required**: No (only for email-sourced notes)
- **Description**: Original timestamp when the email was sent
- **Format**: `YYYY-MM-DDTHH:MM:SSZ`
- **Constraints**:
  - Only applicable when `source: gmail`
  - May differ from `created` field (email sent vs note created)
  - Useful for tracking when communication occurred
- **Example**: `"2026-03-29T10:15:00Z"`

### tags
- **Type**: Array of strings
- **Required**: No
- **Description**: List of tags for categorization and filtering
- **Constraints**:
  - Each tag should be lowercase
  - Use hyphens for multi-word tags (e.g., `"action-item"`)
  - Avoid special characters
  - Keep tags concise (1-2 words)
- **Example**: `["email", "urgent", "budget", "q1"]`

## Complete Example

```yaml
---
title: Q1 Budget Review Meeting
created: 2026-03-29T14:30:22Z
source: gmail
sender: finance@example.com
email_date: 2026-03-29T10:15:00Z
status: inbox
tags:
  - email
  - meeting
  - budget
  - q1
---
```

## Validation Rules

1. **Frontmatter Delimiters**: Must start and end with `---` on separate lines
2. **Position**: Frontmatter must be at the beginning of the file
3. **YAML Syntax**: Must be valid YAML (proper indentation, no syntax errors)
4. **Required Fields**: All required fields must be present
5. **Field Types**: Values must match specified types (string, datetime, array)
6. **Status-Folder Consistency**: Status field must match folder location
7. **Email Fields**: `sender` and `email_date` should only be present when `source: gmail`

## Parsing Notes

- Use `watchers/vault_utils.py` functions for parsing and generation
- `parse_frontmatter(content)` returns `(frontmatter_dict, body_content)`
- `generate_frontmatter(...)` creates properly formatted YAML
- Obsidian preserves unrecognized fields (safe to add custom fields)
- Empty frontmatter (`---\n---`) is valid but not recommended

## Extension Guidelines

When adding new fields in future tiers:

1. **Document the field** in this schema reference
2. **Update vault_utils.py** if generation logic needed
3. **Maintain backward compatibility** - existing notes should remain valid
4. **Use optional fields** for new features to avoid breaking existing notes
5. **Follow naming conventions** - lowercase with underscores (snake_case)

## Related Files

- `watchers/vault_utils.py` - Frontmatter generation and parsing functions
- `specs/001-bronze-tier-foundation/data-model.md` - Complete data model
- `.claude/skills/vault-operations/SKILL.md` - Vault operations skill documentation
