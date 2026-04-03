# Data Model: Gold Tier - Autonomous Employee

**Feature**: 001-gold-tier-autonomous  
**Date**: 2026-03-31  
**Status**: Complete

## Overview

This document defines the data entities, relationships, and validation rules for Gold Tier implementation. All entities are stored locally per the constitution's local-first principle.

---

## Entity Definitions

### 1. Business Transaction

**Purpose**: Represents a financial event tracked in the accounting system

**Storage**: 
- Primary: Obsidian vault (`Accounting/transactions.db` - SQLite)
- Backup: Markdown files in `Accounting/YYYY-MM/` for human readability

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | UUID | Yes | Unique transaction identifier | UUID v4 format |
| `external_id` | String | Yes | Odoo transaction ID | Non-empty string |
| `amount` | Decimal | Yes | Transaction amount | > 0, max 2 decimal places |
| `currency` | String | Yes | Currency code | ISO 4217 (default: USD) |
| `date` | DateTime | Yes | Transaction date | Valid datetime, not future |
| `category` | Enum | Yes | Accounting category | One of: Revenue, COGS, Operating Expenses, Assets, Liabilities, Equity |
| `subcategory` | String | No | User-defined subcategory | Max 100 chars |
| `description` | String | Yes | Transaction description | Max 500 chars |
| `partner_name` | String | No | Counterparty name | Max 200 chars |
| `partner_id` | String | No | Odoo partner ID | Non-empty string |
| `account_code` | String | Yes | Odoo account code | 3-digit code |
| `move_type` | Enum | Yes | Transaction type | One of: invoice, payment, expense, refund |
| `state` | Enum | Yes | Transaction state | One of: draft, posted, cancelled |
| `created_at` | DateTime | Yes | Record creation timestamp | Auto-generated |
| `updated_at` | DateTime | Yes | Last update timestamp | Auto-updated |
| `duplicate_check_hash` | String | Yes | Hash for duplicate detection | SHA-256 of amount+date+description |

**Relationships**:
- One transaction may appear in multiple CEO Briefings (many-to-many via time period)
- One transaction generates one Audit Log Entry on creation

**State Transitions**:
```
draft → posted → [final state]
draft → cancelled → [final state]
posted → cancelled → [final state]
```

**Validation Rules**:
1. Amount must be positive
2. Date cannot be in the future
3. Category must match account_code mapping (see research.md)
4. Duplicate check: No existing transaction with same amount, date (±24h), and description similarity >80%

**Indexes** (SQLite):
- Primary key: `id`
- Unique: `external_id`
- Index: `date`, `category`, `duplicate_check_hash`

---

### 2. Social Media Post

**Purpose**: Represents content published to social media platforms

**Storage**:
- Primary: Obsidian vault (`Content_Queue/` for scheduled, `Done/` for published)
- Metadata: SQLite for engagement tracking

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | UUID | Yes | Unique post identifier | UUID v4 format |
| `content` | String | Yes | Post text content | Max 280 chars (Twitter limit) |
| `media_urls` | Array[String] | No | Attached media URLs | Valid URLs, max 4 items |
| `platforms` | Array[Enum] | Yes | Target platforms | One or more of: facebook, instagram, twitter |
| `scheduled_time` | DateTime | Yes | Scheduled publication time | Valid datetime |
| `published_time` | DateTime | No | Actual publication time | Set on publish |
| `status` | Enum | Yes | Post status | One of: draft, scheduled, published, failed |
| `platform_ids` | Object | No | Platform-specific post IDs | `{facebook: "123", instagram: "456", twitter: "789"}` |
| `engagement_metrics` | Object | No | Engagement data | See Engagement Metrics structure below |
| `approval_status` | Enum | Yes | User approval state | One of: pending, approved, rejected |
| `approval_timestamp` | DateTime | No | When user approved | Required if approved |
| `created_at` | DateTime | Yes | Record creation timestamp | Auto-generated |
| `updated_at` | DateTime | Yes | Last update timestamp | Auto-updated |

**Engagement Metrics Structure**:
```json
{
  "facebook": {
    "likes": 0,
    "comments": 0,
    "shares": 0,
    "reach": 0,
    "last_updated": "2026-03-31T10:00:00Z"
  },
  "instagram": {
    "likes": 0,
    "comments": 0,
    "engagement_rate": 0.0,
    "last_updated": "2026-03-31T10:00:00Z"
  },
  "twitter": {
    "likes": 0,
    "retweets": 0,
    "replies": 0,
    "impressions": 0,
    "last_updated": "2026-03-31T10:00:00Z"
  }
}
```

**Relationships**:
- One post appears in one CEO Briefing (many-to-one via week)
- One post generates multiple Audit Log Entries (draft, approval, publish, engagement checks)

**State Transitions**:
```
draft → scheduled → published → [final state]
draft → scheduled → failed → scheduled (retry)
scheduled → rejected → [final state]
```

**Validation Rules**:
1. Content length ≤ 280 chars (Twitter limit, shortest platform)
2. At least one platform must be selected
3. Scheduled time must be in the future (when creating)
4. Approval required before publishing (Level 2 action safety)
5. Media URLs must be accessible

**High Engagement Detection**:
- Trigger notification when engagement > 3x user's average for that platform
- Calculate average from last 30 days of posts

---

### 3. CEO Briefing

**Purpose**: Weekly executive summary of business activities

**Storage**: Obsidian vault (`Briefings/YYYY-WW.md`)

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | UUID | Yes | Unique briefing identifier | UUID v4 format |
| `week_number` | Integer | Yes | ISO week number | 1-53 |
| `year` | Integer | Yes | Year | 4-digit year |
| `period_start` | Date | Yes | Week start date (Monday) | Valid date |
| `period_end` | Date | Yes | Week end date (Sunday) | Valid date, after start |
| `generated_at` | DateTime | Yes | Generation timestamp | Auto-generated |
| `financial_summary` | Object | Yes | Financial metrics | See Financial Summary structure |
| `social_media_summary` | Object | Yes | Social media metrics | See Social Media Summary structure |
| `tasks_completed` | Integer | Yes | Number of tasks completed | ≥ 0 |
| `tasks_pending` | Integer | Yes | Number of pending tasks | ≥ 0 |
| `critical_issues` | Array[Object] | Yes | Issues requiring attention | See Critical Issue structure |
| `status` | Enum | Yes | Briefing status | One of: generating, complete, failed |
| `markdown_path` | String | Yes | Path to Markdown file | Valid file path |

**Financial Summary Structure**:
```json
{
  "revenue": {
    "current_week": 12450.00,
    "last_week": 10200.00,
    "change_percent": 22.0,
    "trend": "up"
  },
  "expenses": {
    "current_week": 3200.00,
    "last_week": 3500.00,
    "change_percent": -9.0,
    "trend": "down"
  },
  "profit": {
    "current_week": 9250.00,
    "last_week": 6700.00,
    "change_percent": 38.0,
    "trend": "up"
  },
  "top_revenue_sources": [
    {"name": "Product Sales", "amount": 8000.00},
    {"name": "Consulting", "amount": 4450.00}
  ],
  "top_expenses": [
    {"name": "Marketing", "amount": 1500.00},
    {"name": "Software", "amount": 1200.00}
  ]
}
```

**Social Media Summary Structure**:
```json
{
  "facebook": {
    "posts_published": 3,
    "total_engagement": 245,
    "top_post": {
      "content": "Product Launch announcement...",
      "engagement": 120
    }
  },
  "instagram": {
    "posts_published": 5,
    "total_engagement": 380,
    "top_post": {
      "content": "Behind the Scenes...",
      "engagement": 95
    }
  },
  "twitter": {
    "posts_published": 7,
    "total_engagement": 156,
    "top_post": {
      "content": "Industry News...",
      "engagement": 45
    }
  }
}
```

**Critical Issue Structure**:
```json
{
  "priority": "high",
  "title": "Invoice #1234 overdue by 5 days",
  "description": "Customer ABC has not paid invoice #1234 ($5,000)",
  "action_required": "Follow up with customer",
  "created_at": "2026-03-31T08:00:00Z"
}
```

**Relationships**:
- One briefing aggregates many Business Transactions (one-to-many)
- One briefing aggregates many Social Media Posts (one-to-many)
- One briefing generates one Audit Log Entry on creation

**State Transitions**:
```
generating → complete → [final state]
generating → failed → generating (retry)
```

**Validation Rules**:
1. Week number must be valid for the year (1-53)
2. Period start must be a Monday
3. Period end must be a Sunday
4. Generated_at must be Monday 8:00 AM ±15 minutes
5. All summary objects must be present (even if empty)

**Generation Schedule**: Every Monday at 8:00 AM local time

---

### 4. Audit Log Entry

**Purpose**: Tamper-evident record of all agent actions

**Storage**: 
- Primary: SQLite (`obsidian-vault/Audit_Logs/audit.db`)
- Human-readable: Markdown (`obsidian-vault/Audit_Logs/YYYY-MM-DD.md`)

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | UUID | Yes | Unique entry identifier | UUID v4 format |
| `sequence_number` | Integer | Yes | Daily sequence number | Auto-increment per day |
| `timestamp` | DateTime | Yes | Action timestamp | Auto-generated, microsecond precision |
| `action_type` | Enum | Yes | Type of action | See Action Types below |
| `action_name` | String | Yes | Specific action name | Max 100 chars |
| `parameters` | Object | Yes | Action parameters (redacted) | JSON object |
| `result` | Enum | Yes | Action result | One of: success, failure, partial |
| `error_message` | String | No | Error details if failed | Max 1000 chars |
| `reasoning` | String | Yes | Agent's reasoning | Max 2000 chars |
| `user_approval` | Object | No | Approval details if Level 2+ | See User Approval structure |
| `safety_level` | Integer | Yes | Action safety level | 0-3 |
| `previous_entry_hash` | String | Yes | Hash of previous entry | SHA-256, empty for first entry |
| `entry_hash` | String | Yes | Hash of this entry | SHA-256 of all fields |

**Action Types**:
- `read`: Read-only operations (Level 0)
- `write`: Low-risk writes (Level 1)
- `external_communication`: Medium-risk (Level 2)
- `financial`: High-risk financial operations (Level 3)
- `system`: System operations (config changes, etc.)

**User Approval Structure**:
```json
{
  "required": true,
  "approved": true,
  "timestamp": "2026-03-31T08:00:00Z",
  "method": "cli_prompt"
}
```

**Relationships**:
- Each entry links to previous entry via hash chain
- Entries reference related entities (transaction_id, post_id, briefing_id)

**Validation Rules**:
1. Sequence number must be unique per day
2. Timestamp must be monotonically increasing within a day
3. Previous entry hash must match actual previous entry
4. Entry hash must be valid SHA-256 of entry content
5. User approval required for safety_level ≥ 2

**PII Redaction Rules**:
- Transaction descriptions: First 20 chars only
- Email addresses: Mask domain (user@****)
- Phone numbers: Mask middle digits (555-***-1234)
- API keys: Never log (show "***" only)
- Social media content: First 50 chars only

**Hash Chain Integrity**:
```python
entry_hash = sha256(
    f"{timestamp}|{action_type}|{action_name}|{parameters}|{result}|{previous_entry_hash}"
)
```

---

### 5. Multi-Step Task

**Purpose**: Workflow definition for autonomous task completion

**Storage**: Obsidian vault (`Needs_Action/tasks.db` - SQLite)

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | UUID | Yes | Unique task identifier | UUID v4 format |
| `title` | String | Yes | Task title | Max 200 chars |
| `description` | String | Yes | Task description | Max 2000 chars |
| `steps` | Array[Object] | Yes | Ordered task steps | See Step structure |
| `current_step_index` | Integer | Yes | Current step being executed | 0 to len(steps)-1 |
| `status` | Enum | Yes | Task status | One of: pending, in_progress, completed, failed, blocked |
| `completion_criteria` | String | Yes | How to validate completion | Max 500 chars |
| `created_at` | DateTime | Yes | Task creation timestamp | Auto-generated |
| `started_at` | DateTime | No | When execution started | Set on first step |
| `completed_at` | DateTime | No | When task completed | Set on completion |
| `retry_count` | Integer | Yes | Number of retry attempts | Default: 0, max: 3 |
| `requires_user_input` | Boolean | Yes | Waiting for user clarification | Default: false |

**Step Structure**:
```json
{
  "step_number": 1,
  "action": "odoo_query_financials",
  "parameters": {"period": "last_month"},
  "status": "completed",
  "result": {"revenue": 50000, "expenses": 20000},
  "completed_at": "2026-03-31T08:15:00Z",
  "dependencies": [],
  "validation": "revenue > 0 and expenses > 0"
}
```

**Relationships**:
- One task generates multiple Audit Log Entries (one per step)
- One task may appear in CEO Briefing if completed during the week

**State Transitions**:
```
pending → in_progress → completed → [final state]
pending → in_progress → failed → pending (retry if retry_count < 3)
pending → in_progress → blocked → in_progress (when unblocked)
```

**Validation Rules**:
1. Steps must be ordered (step_number sequential)
2. Current step must exist in steps array
3. Cannot mark task complete unless all steps completed
4. Retry count cannot exceed 3
5. Each step must have validation criteria

**Ralph Wiggum Loop Pattern**:
- Agent iterates through steps until completion_criteria met
- Self-validates each step before proceeding
- Escalates to user only when autonomous resolution impossible

---

### 6. Integration Status

**Purpose**: Health status of external service integrations

**Storage**: SQLite (`watchers/shared/integration_status.db`)

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `integration_name` | Enum | Yes | Integration identifier | One of: odoo, facebook, instagram, twitter, gmail, whatsapp |
| `status` | Enum | Yes | Current status | One of: healthy, degraded, offline |
| `circuit_breaker_state` | Enum | Yes | Circuit breaker state | One of: closed, open, half_open |
| `error_count` | Integer | Yes | Errors in current window | ≥ 0 |
| `success_count` | Integer | Yes | Successes in current window | ≥ 0 |
| `error_rate` | Float | Yes | Current error rate | 0.0 to 1.0 |
| `last_success_at` | DateTime | No | Last successful call | Valid datetime |
| `last_failure_at` | DateTime | No | Last failed call | Valid datetime |
| `last_failure_reason` | String | No | Error message | Max 500 chars |
| `recovery_attempt` | Integer | Yes | Current recovery attempt | ≥ 0 |
| `next_recovery_at` | DateTime | No | Next recovery attempt time | Valid datetime, future |
| `updated_at` | DateTime | Yes | Last status update | Auto-updated |

**Relationships**:
- Integration status affects Action Queue (queued actions for offline integrations)
- Status changes generate Audit Log Entries

**State Transitions**:
```
healthy → degraded (error_rate > 0.10)
degraded → offline (error_rate > 0.20, circuit breaker opens)
offline → degraded (circuit breaker half-open, testing recovery)
degraded → healthy (error_rate < 0.05)
```

**Validation Rules**:
1. Error rate = error_count / (error_count + success_count)
2. Circuit breaker opens when error_rate > 0.20
3. Recovery schedule: 5min, 10min, 20min, then hourly
4. Next recovery time calculated based on recovery_attempt

**Circuit Breaker Logic**:
- CLOSED: Normal operation, all calls allowed
- OPEN: Integration disabled, calls rejected immediately
- HALF_OPEN: Testing recovery, single call allowed

---

### 7. Action Queue

**Purpose**: Pending operations awaiting execution when services become available

**Storage**: SQLite (`watchers/shared/action_queue.db`)

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | UUID | Yes | Unique queue entry identifier | UUID v4 format |
| `action_type` | String | Yes | MCP tool name | Max 100 chars |
| `parameters` | Object | Yes | Action parameters | JSON object |
| `integration_name` | Enum | Yes | Target integration | One of: odoo, facebook, instagram, twitter, gmail, whatsapp |
| `priority` | Integer | Yes | Execution priority | 0 (low) to 3 (high) |
| `created_at` | DateTime | Yes | When queued | Auto-generated |
| `scheduled_for` | DateTime | Yes | Earliest execution time | Valid datetime |
| `attempts` | Integer | Yes | Execution attempts | Default: 0, max: 3 |
| `last_attempt_at` | DateTime | No | Last execution attempt | Valid datetime |
| `last_error` | String | No | Last error message | Max 500 chars |
| `status` | Enum | Yes | Queue entry status | One of: pending, executing, completed, failed |

**Relationships**:
- Queue entries depend on Integration Status (only execute when healthy)
- Completed queue entries generate Audit Log Entries

**State Transitions**:
```
pending → executing → completed → [final state]
pending → executing → failed → pending (retry if attempts < 3)
pending → executing → failed → failed (if attempts >= 3)
```

**Validation Rules**:
1. Priority must be 0-3
2. Scheduled_for cannot be in the past (when creating)
3. Attempts cannot exceed 3
4. Cannot execute if integration status is offline

**Execution Logic**:
- Process queue every 5 minutes
- Execute in priority order (3 → 0)
- Skip entries if integration offline
- Retry failed entries with exponential backoff

---

## Entity Relationships Diagram

```
Business Transaction ──┐
                       ├──> CEO Briefing
Social Media Post ─────┤
Multi-Step Task ───────┘

All Entities ──> Audit Log Entry (one-to-many)

Integration Status ──> Action Queue (one-to-many)
```

---

## Storage Summary

| Entity | Primary Storage | Secondary Storage | Indexed Fields |
|--------|----------------|-------------------|----------------|
| Business Transaction | SQLite | Markdown | date, category, duplicate_check_hash |
| Social Media Post | Obsidian Markdown | SQLite (metrics) | scheduled_time, status, platforms |
| CEO Briefing | Obsidian Markdown | SQLite (metadata) | week_number, year |
| Audit Log Entry | SQLite | Markdown (daily) | timestamp, action_type, sequence_number |
| Multi-Step Task | SQLite | Obsidian Markdown | status, created_at |
| Integration Status | SQLite | None | integration_name, status |
| Action Queue | SQLite | None | integration_name, priority, scheduled_for |

---

## Data Retention Policy

Per constitution compliance requirements:

- **Business Transactions**: 7 years (standard accounting practice)
- **Social Media Posts**: 2 years (engagement data becomes stale)
- **CEO Briefings**: Indefinite (executive records)
- **Audit Logs**: 7 years (compliance requirement)
- **Multi-Step Tasks**: 90 days after completion
- **Integration Status**: Current state only (no history)
- **Action Queue**: 30 days after completion/failure

---

## Next Steps

1. ✅ Data model complete
2. ⏭️ Generate API contracts (contracts/*.yaml)
3. ⏭️ Generate quickstart.md
4. ⏭️ Update agent context
