# Data Model: Platinum Tier - Always-On Cloud + Local Executive

**Date**: 2026-04-03  
**Feature**: Platinum Tier  
**Purpose**: Define data structures for dual-agent coordination

## Overview

This data model defines the entities used for coordinating two autonomous agents (cloud and local) through a synchronized Obsidian vault. The model supports claim-by-move semantics, logical timestamps for ordering, and work-zone specialization.

---

## 1. Agent Configuration

**Purpose**: Defines agent identity, capabilities, and operational parameters.

**Attributes**:
- `agent_id`: string - Unique identifier ("cloud" | "local")
- `agent_type`: enum - Agent deployment type ("cloud" | "local")
- `llm_provider`: enum - LLM choice ("claude" | "gemini")
- `credential_scope`: enum - API access level ("read_only" | "full")
- `vault_path`: string - Absolute path to Obsidian vault
- `sync_enabled`: boolean - Whether vault sync is active
- `sync_method`: enum - Synchronization technology ("git" | "syncthing")
- `sync_interval_seconds`: integer - How often to sync (default: 30)
- `health_check_interval_seconds`: integer - Health check frequency (default: 300)

**Relationships**:
- One agent configuration per agent instance
- Referenced by Work Queue Items (claimed_by)
- Referenced by Draft Approvals (created_by)

**Storage**: JSON file at `{vault_path}/config/agent-config.json`

**Example**:
```json
{
  "agent_id": "cloud",
  "agent_type": "cloud",
  "llm_provider": "claude",
  "credential_scope": "read_only",
  "vault_path": "/opt/obsidian-vault",
  "sync_enabled": true,
  "sync_method": "git",
  "sync_interval_seconds": 30,
  "health_check_interval_seconds": 300
}
```

**Validation Rules**:
- `agent_id` must be unique across all agents
- Cloud agent MUST have `credential_scope: "read_only"`
- Local agent MUST have `credential_scope: "full"`
- `sync_interval_seconds` must be between 10 and 300

---

## 2. Work Queue Item

**Purpose**: Represents a task or action that needs to be processed by an agent.

**Attributes**:
- `item_id`: string (UUID) - Unique identifier
- `domain`: enum - Work domain ("email" | "social" | "accounting" | "banking")
- `item_type`: enum - Type of work ("draft" | "action_plan" | "approval_request")
- `status`: enum - Current state ("pending" | "claimed" | "in_progress" | "completed" | "failed")
- `created_at`: LamportTimestamp - When item was created
- `created_by`: string (agent_id) - Which agent created it
- `claimed_by`: string (agent_id) | null - Which agent claimed it
- `claimed_at`: LamportTimestamp | null - When it was claimed
- `completed_at`: LamportTimestamp | null - When it was completed
- `content_path`: string - Relative path to content file (Markdown)
- `metadata`: object - Domain-specific metadata

**Relationships**:
- Created by Agent (created_by → Agent.agent_id)
- Claimed by Agent (claimed_by → Agent.agent_id)
- May reference Draft Approval (for approval_request items)

**Storage**: 
- Pending: `{vault_path}/Needs_Action/{domain}/{item_id}.json`
- Claimed: `{vault_path}/In_Progress/{agent_id}/{item_id}.json`
- Completed: `{vault_path}/Done/{item_id}.json`

**Example**:
```json
{
  "item_id": "550e8400-e29b-41d4-a716-446655440000",
  "domain": "email",
  "item_type": "draft",
  "status": "claimed",
  "created_at": {"agent_id": "cloud", "counter": 42},
  "created_by": "cloud",
  "claimed_by": "local",
  "claimed_at": {"agent_id": "local", "counter": 17},
  "completed_at": null,
  "content_path": "Pending_Approval/email/reply-to-john-doe.md",
  "metadata": {
    "email_id": "msg_abc123",
    "subject": "Re: Project Update",
    "priority": "normal"
  }
}
```

**State Transitions**:
```
pending → claimed → in_progress → completed
                                 → failed
```

**Validation Rules**:
- `item_id` must be unique
- `claimed_by` must be null when status is "pending"
- `claimed_at` must be set when status is "claimed" or later
- Cloud agent can only create items with `item_type: "draft"` or `item_type: "action_plan"`
- Local agent can create any item_type

---

## 3. Draft Approval

**Purpose**: Represents a draft created by cloud agent awaiting local agent approval.

**Attributes**:
- `approval_id`: string (UUID) - Unique identifier
- `draft_type`: enum - Type of draft ("email_reply" | "social_post" | "accounting_entry")
- `draft_content_path`: string - Relative path to draft Markdown file
- `created_by`: string (agent_id) - Always "cloud"
- `created_at`: LamportTimestamp - When draft was created
- `approval_status`: enum - Current state ("pending" | "approved" | "rejected" | "expired")
- `approved_by`: string (user_id) | null - User who approved/rejected
- `approved_at`: LamportTimestamp | null - When decision was made
- `executed_at`: LamportTimestamp | null - When action was executed (after approval)
- `execution_result`: object | null - Result of execution (success/failure details)

**Relationships**:
- Created by Cloud Agent (created_by → Agent.agent_id)
- May reference Work Queue Item (if created from action plan)

**Storage**: `{vault_path}/Pending_Approval/{draft_type}/{approval_id}.json`

**Example**:
```json
{
  "approval_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "draft_type": "email_reply",
  "draft_content_path": "Pending_Approval/email/reply-to-john-doe.md",
  "created_by": "cloud",
  "created_at": {"agent_id": "cloud", "counter": 42},
  "approval_status": "approved",
  "approved_by": "user",
  "approved_at": {"agent_id": "local", "counter": 18},
  "executed_at": {"agent_id": "local", "counter": 19},
  "execution_result": {
    "success": true,
    "message_id": "msg_xyz789",
    "sent_at": "2026-04-03T14:30:00Z"
  }
}
```

**State Transitions**:
```
pending → approved → executed
        → rejected
        → expired (after 24 hours)
```

**Validation Rules**:
- `created_by` must always be "cloud"
- `approved_by` must be set when status is "approved" or "rejected"
- `executed_at` must be set when status is "executed"
- Drafts expire after 24 hours if not approved

---

## 4. Sync Status

**Purpose**: Tracks vault synchronization health between cloud and local agents.

**Attributes**:
- `agent_id`: string - Which agent's perspective ("cloud" | "local")
- `last_sync_at`: timestamp (ISO 8601) - Last successful sync
- `last_sync_commit`: string - Git commit hash or Syncthing version
- `sync_lag_seconds`: integer - Time since last sync
- `sync_method`: enum - Technology used ("git" | "syncthing")
- `conflict_count`: integer - Number of unresolved conflicts
- `last_conflict_at`: timestamp | null - When last conflict occurred
- `sync_health`: enum - Overall health ("healthy" | "degraded" | "failed")
- `consecutive_failures`: integer - Failed sync attempts in a row
- `queued_operations`: integer - Operations queued during sync failure

**Relationships**:
- One sync status per agent
- Referenced by Health Check Results

**Storage**: `{vault_path}/.sync-status/{agent_id}.json`

**Example**:
```json
{
  "agent_id": "cloud",
  "last_sync_at": "2026-04-03T14:25:30Z",
  "last_sync_commit": "a3f2b1c",
  "sync_lag_seconds": 15,
  "sync_method": "git",
  "conflict_count": 0,
  "last_conflict_at": null,
  "sync_health": "healthy",
  "consecutive_failures": 0,
  "queued_operations": 0
}
```

**Health Thresholds**:
- `healthy`: sync_lag < 60s, consecutive_failures = 0
- `degraded`: sync_lag 60-300s OR consecutive_failures 1-2
- `failed`: sync_lag > 300s OR consecutive_failures >= 3

**Validation Rules**:
- `sync_lag_seconds` calculated as `now - last_sync_at`
- `sync_health` automatically derived from thresholds
- Alert triggered when `sync_health` becomes "failed"

---

## 5. Health Check Result

**Purpose**: Records health check outcomes for monitoring and alerting.

**Attributes**:
- `check_id`: string (UUID) - Unique identifier
- `agent_id`: string - Which agent performed check
- `check_type`: enum - What was checked ("agent_responsiveness" | "vault_sync" | "api_connectivity" | "odoo_health")
- `checked_at`: timestamp (ISO 8601) - When check was performed
- `status`: enum - Check outcome ("pass" | "fail")
- `latency_ms`: integer | null - Response time (if applicable)
- `error_message`: string | null - Error details (if failed)
- `recovery_attempted`: boolean - Whether auto-recovery was tried
- `recovery_successful`: boolean | null - Whether recovery worked
- `alert_sent`: boolean - Whether alert was triggered

**Relationships**:
- Performed by Agent (agent_id → Agent.agent_id)
- May reference Sync Status (for vault_sync checks)

**Storage**: SQLite database at `{vault_path}/.health-checks.db`

**Example**:
```json
{
  "check_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "agent_id": "cloud",
  "check_type": "odoo_health",
  "checked_at": "2026-04-03T14:30:00Z",
  "status": "fail",
  "latency_ms": null,
  "error_message": "Connection refused to 127.0.0.1:8069",
  "recovery_attempted": true,
  "recovery_successful": false,
  "alert_sent": true
}
```

**Check Types**:
- `agent_responsiveness`: HTTP ping to agent endpoint
- `vault_sync`: Check sync_lag from Sync Status
- `api_connectivity`: Test external API endpoints (Gmail, social media)
- `odoo_health`: Check Odoo `/web/health` endpoint

**Alert Rules**:
- Alert after 2 consecutive failures of same check_type
- Alert immediately for `vault_sync` failures (sync_lag > 300s)
- No alert if recovery_successful = true

---

## 6. Logical Timestamp

**Purpose**: Provides clock-skew-independent ordering for distributed operations.

**Attributes**:
- `agent_id`: string - Which agent created timestamp ("cloud" | "local")
- `counter`: integer - Monotonically increasing sequence number
- `wall_clock_time`: timestamp (ISO 8601) - Human-readable time (for reference only)

**Relationships**:
- Embedded in Work Queue Items, Draft Approvals, and other entities
- Used for ordering and conflict resolution

**Storage**: Embedded as object in parent entities

**Example**:
```json
{
  "agent_id": "cloud",
  "counter": 42,
  "wall_clock_time": "2026-04-03T14:30:00Z"
}
```

**Comparison Algorithm**:
```python
def compare(ts1: LamportTimestamp, ts2: LamportTimestamp) -> int:
    if ts1.counter != ts2.counter:
        return ts1.counter - ts2.counter
    # Tie-breaker: lexicographic agent_id
    return -1 if ts1.agent_id < ts2.agent_id else 1
```

**Update Rules**:
- Agent increments counter on every operation
- When receiving another agent's timestamp: `counter = max(local_counter, received_counter) + 1`
- `wall_clock_time` is informational only, not used for ordering

---

## Entity Relationship Diagram

```
Agent Configuration
    ↓ (creates)
Work Queue Item ←→ Draft Approval
    ↓ (claims)
Agent Configuration
    ↓ (monitors)
Sync Status ←→ Health Check Result
    ↓ (uses)
Logical Timestamp (embedded)
```

---

## File System Layout

```
obsidian-vault/
├── config/
│   ├── cloud-agent-config.json
│   └── local-agent-config.json
├── Needs_Action/
│   ├── email/
│   ├── social/
│   ├── accounting/
│   └── banking/
├── In_Progress/
│   ├── cloud/
│   └── local/
├── Pending_Approval/
│   ├── email/
│   ├── social/
│   └── accounting/
├── Done/
├── Updates/
├── .sync-status/
│   ├── cloud.json
│   └── local.json
└── .health-checks.db
```

---

## Data Integrity Rules

1. **Atomicity**: All file writes use atomic pattern (write to .tmp, then rename)
2. **Idempotency**: All operations safe to retry (check existence before create)
3. **Consistency**: Logical timestamps ensure total ordering across agents
4. **Durability**: Git commits provide audit trail and recovery mechanism
5. **Isolation**: Claim-by-move prevents concurrent modifications

---

## Migration Notes

**From Gold Tier**:
- Existing `Needs_Action/` and `Done/` directories remain unchanged
- Add new directories: `In_Progress/`, `Pending_Approval/`, `Updates/`
- Add `.sync-status/` and `.health-checks.db` for monitoring
- Existing work queue items can be migrated by adding logical timestamps
