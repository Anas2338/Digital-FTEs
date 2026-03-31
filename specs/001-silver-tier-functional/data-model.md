# Data Model: Silver Tier Functional Assistant

**Feature**: 001-silver-tier-functional
**Date**: 2026-03-30
**Purpose**: Define entity schemas, relationships, and state transitions

## Entity Schemas

### 1. Watcher

**Description**: Background process monitoring external communication channel

**Attributes**:
- `watcher_id` (string, required): Unique identifier (e.g., "gmail-watcher", "whatsapp-watcher", "linkedin-watcher")
- `channel` (enum, required): Communication channel ("gmail" | "whatsapp" | "linkedin")
- `status` (enum, required): Current operational status ("running" | "stopped" | "error" | "reconnecting")
- `health_status` (enum, required): Health indicator ("healthy" | "degraded" | "unhealthy")
- `last_check_timestamp` (datetime, required): Last successful polling time (ISO 8601)
- `last_event_timestamp` (datetime, nullable): Last event detected time
- `error_count` (integer, required): Consecutive error count (resets on success)
- `total_events_processed` (integer, required): Lifetime event count
- `polling_interval_seconds` (integer, required): Time between checks (180 for Gmail, 300 for WhatsApp/LinkedIn)
- `config` (object, required): Watcher-specific configuration
  - Gmail: `{"label": "ToVault", "oauth_token_path": "..."}`
  - WhatsApp: `{"session_path": "...", "qr_timeout_seconds": 60}`
  - LinkedIn: `{"session_cookies_path": "...", "notification_types": ["message", "connection", "mention"]}`

**Validation Rules**:
- `error_count` must be >= 0
- `polling_interval_seconds` must be >= 60 (minimum 1 minute)
- `status` = "error" requires `error_count` > 0
- `health_status` = "unhealthy" when `error_count` >= 3

**State Transitions**:
```
stopped → running (on start command)
running → error (on polling failure)
error → reconnecting (on retry attempt)
reconnecting → running (on successful reconnection)
reconnecting → error (on retry failure)
running → stopped (on stop command)
```

**Storage**: SQLite table `watchers` + log file `watchers/logs/watcher-{watcher_id}.log`

---

### 2. Event

**Description**: Detected change from watcher representing new communication

**Attributes**:
- `event_id` (string, required): Unique identifier (UUID v4)
- `source_channel` (enum, required): Origin channel ("gmail" | "whatsapp" | "linkedin")
- `event_type` (enum, required): Type of event ("email" | "message" | "notification" | "connection_request" | "post_mention")
- `content` (object, required): Channel-specific content
  - Gmail: `{"subject": "...", "sender": "...", "body": "...", "timestamp": "..."}`
  - WhatsApp: `{"sender_name": "...", "sender_phone": "...", "message_text": "...", "timestamp": "..."}`
  - LinkedIn: `{"sender_profile_url": "...", "notification_type": "...", "content": "...", "timestamp": "..."}`
- `timestamp` (datetime, required): Event detection time (ISO 8601)
- `processing_status` (enum, required): Processing state ("pending" | "processed" | "failed")
- `vault_note_path` (string, nullable): Path to created Obsidian note (e.g., "obsidian-vault/Inbox/20260330-143022-email-subject.md")
- `error_message` (string, nullable): Error details if processing failed

**Validation Rules**:
- `content` structure must match `source_channel` schema
- `vault_note_path` must exist if `processing_status` = "processed"
- `error_message` must be present if `processing_status` = "failed"

**State Transitions**:
```
pending → processed (on successful vault note creation)
pending → failed (on vault write error)
failed → pending (on manual retry)
```

**Storage**: SQLite table `events` + Obsidian note in `/Inbox`

---

### 3. Action

**Description**: Requested operation requiring approval before execution

**Attributes**:
- `action_id` (string, required): Unique identifier (UUID v4)
- `action_type` (enum, required): Type of action ("send_email" | "linkedin_post" | "whatsapp_send")
- `parameters` (object, required): Action-specific parameters
  - send_email: `{"recipient": "...", "subject": "...", "body": "..."}`
  - linkedin_post: `{"content": "...", "visibility": "public"}`
  - whatsapp_send: `{"recipient_phone": "...", "message": "..."}`
- `safety_level` (enum, required): Risk classification (0 | 1 | 2 | 3)
  - Level 0: Auto-execute (read-only)
  - Level 1: Notify (draft creation)
  - Level 2: Confirm (send email, post to social)
  - Level 3: Explicit approval (financial transactions)
- `status` (enum, required): Current state ("pending" | "approved" | "rejected" | "executed" | "expired" | "failed")
- `created_timestamp` (datetime, required): Action creation time (ISO 8601)
- `approved_timestamp` (datetime, nullable): Approval time
- `executed_timestamp` (datetime, nullable): Execution completion time
- `approver` (string, nullable): User who approved (default: "user")
- `rejection_reason` (string, nullable): Reason for rejection
- `execution_result` (object, nullable): Result of execution
  - `{"success": true, "message": "Email sent", "external_id": "..."}`
- `audit_trail` (array, required): History of state changes
  - `[{"timestamp": "...", "from_status": "...", "to_status": "...", "actor": "..."}]`

**Validation Rules**:
- `safety_level` >= 2 requires approval before execution
- `approved_timestamp` must be present if `status` = "approved" or "executed"
- `executed_timestamp` must be present if `status` = "executed"
- `rejection_reason` must be present if `status` = "rejected"
- Actions older than 24 hours with `status` = "pending" auto-transition to "expired"

**State Transitions**:
```
pending → approved (on user approval)
pending → rejected (on user rejection)
pending → expired (after 24 hours)
approved → executed (on successful execution)
approved → failed (on execution error)
rejected → [terminal state]
expired → [terminal state]
```

**Storage**: Obsidian notes in `/Approvals` (pending), `/Done` (executed), `/Rejected` (rejected), `/Expired` (expired) + SQLite table `actions`

---

### 4. Content Queue Item

**Description**: Scheduled LinkedIn post awaiting approval and publication

**Attributes**:
- `item_id` (string, required): Unique identifier (UUID v4)
- `schedule_datetime` (datetime, required): Scheduled publication time (ISO 8601)
- `post_content` (string, required): LinkedIn post text (max 3000 chars)
- `status` (enum, required): Current state ("draft" | "scheduled" | "pending_approval" | "approved" | "published" | "failed")
- `created_timestamp` (datetime, required): Item creation time
- `published_timestamp` (datetime, nullable): Actual publication time
- `performance_metrics` (object, nullable): Post engagement data
  - `{"views": 0, "likes": 0, "comments": 0, "shares": 0, "last_updated": "..."}`
- `action_id` (string, nullable): Associated Action ID for approval workflow
- `error_message` (string, nullable): Error details if publication failed

**Validation Rules**:
- `post_content` length <= 3000 characters (LinkedIn limit)
- `schedule_datetime` must be in the future when `status` = "draft" or "scheduled"
- `action_id` must be present if `status` = "pending_approval" or "approved"
- `published_timestamp` must be present if `status` = "published"

**State Transitions**:
```
draft → scheduled (on schedule_datetime set)
scheduled → pending_approval (when schedule_datetime reached)
pending_approval → approved (on user approval)
approved → published (on successful LinkedIn API call)
approved → failed (on LinkedIn API error)
failed → scheduled (on manual reschedule)
```

**Storage**: Obsidian notes in `/Content_Queue` with YAML frontmatter

**Frontmatter Schema**:
```yaml
---
item_id: "uuid-v4"
schedule: "2026-03-30T09:00:00Z"
status: "scheduled"
created: "2026-03-29T14:30:00Z"
performance:
  views: 0
  likes: 0
  comments: 0
  shares: 0
---
[Post content here]
```

---

### 5. Plan

**Description**: Structured execution plan for complex task

**Attributes**:
- `plan_id` (string, required): Unique identifier (UUID v4)
- `task_note_path` (string, required): Path to originating task note in `/Needs_Action`
- `goal` (string, required): High-level objective
- `context` (string, required): Background information and constraints
- `steps` (array, required): Ordered execution steps
  - `[{"step_id": "...", "description": "...", "status": "pending|in_progress|completed|validated", "dependencies": ["step_id"], "notes": "..."}]`
- `success_criteria` (array, required): Measurable completion criteria
  - `["Criterion 1", "Criterion 2", ...]`
- `risks` (array, required): Identified risks and mitigation strategies
  - `[{"risk": "...", "mitigation": "...", "severity": "low|medium|high"}]`
- `rollback_procedure` (string, required): Steps to undo changes if plan fails
- `status` (enum, required): Overall plan state ("active" | "completed" | "failed" | "abandoned")
- `created_timestamp` (datetime, required): Plan generation time
- `completed_timestamp` (datetime, nullable): Plan completion time

**Validation Rules**:
- At least one step must exist
- Step dependencies must reference valid `step_id` values
- No circular dependencies allowed
- All steps must be "completed" before plan status = "completed"
- All success criteria must be validated before plan status = "completed"

**State Transitions**:
```
active → completed (when all steps completed and criteria validated)
active → failed (when critical step fails and no recovery possible)
active → abandoned (on user decision to stop)
```

**Storage**: Markdown file `Plan.md` in same directory as task note

**File Structure**:
```markdown
# Plan: [Goal]

**Plan ID**: uuid-v4
**Created**: 2026-03-30T14:30:00Z
**Status**: active

## Goal
[High-level objective]

## Context
[Background and constraints]

## Steps
1. [Step 1] - Status: pending
   - Dependencies: None
   - Notes: ...

2. [Step 2] - Status: pending
   - Dependencies: Step 1
   - Notes: ...

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Risks
- **Risk**: [Description] | **Severity**: high | **Mitigation**: [Strategy]

## Rollback Procedure
[Steps to undo changes]
```

---

### 6. Schedule

**Description**: Recurring task definition with execution history

**Attributes**:
- `schedule_id` (string, required): Unique identifier (UUID v4)
- `task_description` (string, required): Human-readable task description
- `cron_expression` (string, required): Cron format schedule (e.g., "0 9 * * 1" for Monday 9am)
- `platform` (enum, required): Scheduling platform ("cron" | "taskscheduler" | "in_process")
- `task_command` (string, required): Command or agent skill to execute
- `status` (enum, required): Schedule state ("active" | "paused" | "disabled")
- `last_run_timestamp` (datetime, nullable): Last execution time
- `next_run_timestamp` (datetime, required): Next scheduled execution time
- `execution_history` (array, required): Recent execution records (max 100)
  - `[{"timestamp": "...", "status": "success|failed", "duration_seconds": 0, "error_message": null}]`
- `retry_count` (integer, required): Current retry attempt (0-3)
- `created_timestamp` (datetime, required): Schedule creation time

**Validation Rules**:
- `cron_expression` must be valid cron syntax (5 fields: minute hour day month weekday)
- `next_run_timestamp` must be calculated from `cron_expression`
- `retry_count` must be 0-3 (max 3 retries per constitution)
- `execution_history` limited to last 100 executions

**State Transitions**:
```
active → paused (on user pause command)
paused → active (on user resume command)
active → disabled (on permanent removal)
```

**Storage**: Obsidian notes in `/Schedules` + platform-specific registration (crontab or Task Scheduler XML)

**Frontmatter Schema**:
```yaml
---
schedule_id: "uuid-v4"
cron: "0 9 * * 1"
platform: "cron"
status: "active"
last_run: "2026-03-25T09:00:00Z"
next_run: "2026-04-01T09:00:00Z"
retry_count: 0
---
# Task: [Description]

**Command**: `/agent-skill reasoning-plan`

## Execution History
- 2026-03-25 09:00:00 - Success (2.3s)
- 2026-03-18 09:00:00 - Success (1.8s)
```

---

## Entity Relationships

```
Watcher (1) ──creates──> (N) Event
Event (1) ──generates──> (1) Vault Note

Action (1) ──references──> (0..1) Content Queue Item
Action (N) ──stored in──> (1) Approval Queue

Plan (1) ──associated with──> (1) Task Note
Plan (1) ──contains──> (N) Steps

Schedule (1) ──executes──> (N) Execution History Records
Schedule (1) ──triggers──> (N) Actions (indirectly via agent skills)
```

## Data Flow

1. **Watcher → Event → Vault Note**:
   - Watcher polls external API
   - Detects new communication
   - Creates Event record
   - Generates Obsidian note in /Inbox
   - Updates Event.vault_note_path

2. **Agent Skill → Action → Approval → Execution**:
   - Agent skill invokes MCP tool
   - MCP server creates Action record
   - Action queued in /Approvals (if Level 2+)
   - User approves via CLI
   - Action executed
   - Result stored in /Done

3. **Content Queue → Schedule → Action → Publication**:
   - User creates note in /Content_Queue with schedule
   - Scheduler detects scheduled time
   - Creates Action for approval
   - User approves
   - LinkedIn post published
   - Performance metrics tracked

4. **Task Note → Reasoning Loop → Plan**:
   - User creates task in /Needs_Action
   - Reasoning loop detects complexity
   - Generates Plan.md with steps
   - Agent executes steps
   - Plan status updated
   - Task moved to /Done on completion

## Validation & Constraints

### Cross-Entity Constraints

1. **Action Safety Levels**:
   - Level 0 actions: No approval required, execute immediately
   - Level 1 actions: Notify user, execute immediately
   - Level 2+ actions: Must create approval note in /Approvals

2. **Rate Limiting**:
   - Gmail: Max 100 send_email actions per 24-hour window
   - LinkedIn: Max 100 linkedin_post actions per 24-hour window
   - WhatsApp: Max 1000 whatsapp_send actions per 24-hour window

3. **Approval Expiration**:
   - Actions with status="pending" for >24 hours auto-expire
   - Expired actions moved to /Expired folder

4. **Schedule Missed Execution**:
   - If system offline during scheduled time
   - Execute on next startup if within 24-hour window
   - Otherwise, skip and wait for next scheduled time

## Storage Strategy

### SQLite Schema

```sql
CREATE TABLE watchers (
    watcher_id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    health_status TEXT NOT NULL,
    last_check_timestamp TEXT NOT NULL,
    last_event_timestamp TEXT,
    error_count INTEGER NOT NULL DEFAULT 0,
    total_events_processed INTEGER NOT NULL DEFAULT 0,
    polling_interval_seconds INTEGER NOT NULL,
    config TEXT NOT NULL  -- JSON
);

CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    source_channel TEXT NOT NULL,
    event_type TEXT NOT NULL,
    content TEXT NOT NULL,  -- JSON
    timestamp TEXT NOT NULL,
    processing_status TEXT NOT NULL,
    vault_note_path TEXT,
    error_message TEXT
);

CREATE TABLE actions (
    action_id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL,
    parameters TEXT NOT NULL,  -- JSON
    safety_level INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_timestamp TEXT NOT NULL,
    approved_timestamp TEXT,
    executed_timestamp TEXT,
    approver TEXT,
    rejection_reason TEXT,
    execution_result TEXT,  -- JSON
    audit_trail TEXT NOT NULL  -- JSON array
);

CREATE INDEX idx_actions_status ON actions(status);
CREATE INDEX idx_actions_created ON actions(created_timestamp);
CREATE INDEX idx_events_status ON events(processing_status);
CREATE INDEX idx_events_timestamp ON events(timestamp);
```

### Obsidian Vault Structure

```
obsidian-vault/
├── Inbox/                    # Event-generated notes
├── Needs_Action/             # User tasks (with Plan.md if complex)
├── Done/                     # Completed tasks and executed actions
├── Approvals/                # Pending Level 2+ actions
├── Rejected/                 # Rejected actions
├── Expired/                  # Auto-expired actions
├── Content_Queue/            # Scheduled LinkedIn posts
├── Schedules/                # Recurring task definitions
└── Reports/                  # Generated reports
```

## Migration Considerations

### From Bronze Tier

- Existing vault structure preserved (/Inbox, /Needs_Action, /Done)
- New folders added (/Approvals, /Rejected, /Expired, /Content_Queue, /Schedules, /Reports)
- Gmail watcher schema extended with new fields (health_status, error_count)
- No breaking changes to existing notes

### Future Gold Tier

- Add financial transaction entities (Transaction, Account, Budget)
- Extend Action safety levels to include Level 4 (financial)
- Add multi-user support (User entity, permissions)
- Add analytics entities (Metric, Dashboard, Report)
