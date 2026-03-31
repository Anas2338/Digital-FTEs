# Approval Review Agent Skill

**Purpose**: Review and manage pending action approvals

**Version**: 1.0.0

**Category**: Workflow Management

---

## Description

This skill provides CLI commands to review, approve, and reject pending actions that require human approval (Safety Level 2+). All Level 2+ actions (sending emails, posting to LinkedIn, sending WhatsApp messages) are queued for approval before execution.

---

## Commands

### list-pending

List all pending approval requests.

**Usage:**
```
claude-code "List pending approvals"
```

**Output:**
- Action ID
- Action type
- Safety level
- Created timestamp
- Parameters (sanitized)

---

### approve

Approve a pending action for execution.

**Usage:**
```
claude-code "Approve action <action-id>"
```

**Parameters:**
- `action-id`: The unique identifier of the action to approve

**Example:**
```
claude-code "Approve action action-20260330120000"
```

**Result:**
- Action status updated to "approved"
- Action will be executed immediately
- Approval note moved from /Approvals to /Done

---

### reject

Reject a pending action with a reason.

**Usage:**
```
claude-code "Reject action <action-id> with reason: <reason>"
```

**Parameters:**
- `action-id`: The unique identifier of the action to reject
- `reason`: Explanation for rejection

**Example:**
```
claude-code "Reject action action-20260330120000 with reason: Incorrect recipient email"
```

**Result:**
- Action status updated to "rejected"
- Approval note moved from /Approvals to /Rejected
- Rejection reason appended to note

---

### approve-all

Approve all pending actions (use with caution).

**Usage:**
```
claude-code "Approve all pending actions"
```

**Warning:** This approves ALL pending actions without individual review. Use only when you trust all queued actions.

---

## Implementation

The approval workflow is implemented in:
- `mcp-servers/digital-fte-server/approval/queue.py` - Queue management
- `mcp-servers/digital-fte-server/approval/executor.py` - Action execution
- `mcp-servers/digital-fte-server/approval/classifier.py` - Safety classification

---

## Safety Levels

- **Level 0 (Auto-Execute)**: Read-only operations - no approval needed
- **Level 1 (Notify)**: Low-risk writes (drafts) - no approval needed
- **Level 2 (Confirm)**: Medium-risk (send emails, post to social media) - **requires approval**
- **Level 3 (Explicit Approval)**: High-risk (financial, delete) - **requires approval**

---

## Approval Expiration

Pending approvals automatically expire after **24 hours** and are moved to `/Expired` folder. Expired actions cannot be executed and must be re-queued if still needed.

---

## Examples

### Example 1: Review and Approve Email

```bash
# List pending approvals
claude-code "List pending approvals"

# Output shows:
# Action ID: action-20260330120000
# Type: send-email
# To: client@example.com
# Subject: Project Update
# Safety Level: 2 (Confirm)

# Approve the email
claude-code "Approve action action-20260330120000"

# Email is sent immediately
```

### Example 2: Reject LinkedIn Post

```bash
# List pending approvals
claude-code "List pending approvals"

# Output shows:
# Action ID: action-20260330120100
# Type: linkedin-post
# Content: "Announcing our new product..."
# Safety Level: 2 (Confirm)

# Reject with reason
claude-code "Reject action action-20260330120100 with reason: Content needs legal review"

# Post is not published, moved to /Rejected
```

---

## Error Handling

- **Action not found**: Returns error if action ID doesn't exist
- **Already processed**: Returns error if action already approved/rejected/expired
- **Invalid action ID**: Returns error if action ID format is invalid

---

## Notes

- All approval actions are logged in the SQLite database with full audit trail
- Approval notes in Obsidian vault contain complete action details
- Users can manually review notes in `/Approvals` folder before approving
- Rejected actions can be re-queued by creating a new action request
