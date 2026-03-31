# MCP Invoke Agent Skill

**Purpose**: Invoke Digital FTE MCP server tools from Claude Code

**Version**: 1.0.0

**Category**: External Actions

---

## Description

This skill enables Claude to invoke MCP server tools for external actions like sending emails, posting to LinkedIn, and sending WhatsApp messages. All actions go through the approval workflow based on safety level classification.

---

## Available Tools

### send-email

Send an email via Gmail API.

**Usage:**
```
claude-code "Send email to [recipient] with subject [subject]"
```

**Parameters:**
- `recipient`: Email address (validated format)
- `subject`: Email subject (max 200 chars)
- `body`: Email body (max 10,000 chars)

**Safety Level:** 2 (Requires approval)

**Example:**
```
claude-code "Send email to john@example.com with subject 'Project Update' and body 'The project is on track...'"

# Action queued for approval
# Action ID: action-20260331120000
# Safety Level: 2 (Notify - requires approval)
# Approval note created: obsidian-vault/Approvals/action-20260331120000.md

# User approves via CLI:
# python -m mcp_servers.digital_fte_server.approval.cli approve action-20260331120000

# Email sent successfully
```

---

### linkedin-post

Post an update to LinkedIn.

**Usage:**
```
claude-code "Post to LinkedIn: [content]"
```

**Parameters:**
- `content`: Post content (max 3000 chars)

**Safety Level:** 2 (Requires approval)

**Character Limit:** 3000 characters (automatically truncated if exceeded)

**Example:**
```
claude-code "Post to LinkedIn: Excited to announce our new product launch! 🚀"

# Action queued for approval
# Action ID: action-20260331120100
# Safety Level: 2 (Notify - requires approval)
# Content preview: "Excited to announce our new product launch! 🚀"

# User approves and post is published
```

---

### whatsapp-send

Send a WhatsApp message.

**Usage:**
```
claude-code "Send WhatsApp to [recipient]: [message]"
```

**Parameters:**
- `recipient`: Phone number in E.164 format (e.g., +1234567890)
- `message`: Message text (max 5000 chars)

**Safety Level:** 2 (Requires approval)

**Example:**
```
claude-code "Send WhatsApp to +1234567890: Meeting confirmed for tomorrow at 2pm"

# Action queued for approval
# Action ID: action-20260331120200
# Safety Level: 2 (Notify - requires approval)
# Recipient: +1234567890

# User approves and message is sent
```

---

## Safety Levels

All MCP tool invocations are classified by safety level:

### Level 0: Auto-Execute (Read-only)
- No approval required
- Executes immediately
- Examples: Read data, query status

### Level 1: Auto-Execute (Low-risk writes)
- No approval required
- Executes immediately
- Examples: Create draft, save to vault

### Level 2: Notify (Requires approval)
- **Approval required before execution**
- User notified via approval note
- Examples: Send email, post to social media, send message

### Level 3: Explicit Approval (High-risk)
- **Explicit approval required**
- User must confirm with reason
- Examples: Financial transactions, delete operations, bulk actions

**Current Implementation:**
- All three tools (send-email, linkedin-post, whatsapp-send) are **Level 2**
- Require approval before execution
- Safety level can be adjusted based on parameters (e.g., sensitive keywords escalate to Level 3)

---

## Approval Workflow

### Step 1: Tool Invocation
```
claude-code "Send email to john@example.com..."
```

### Step 2: Action Classified
```
Classifying action: send-email
Parameters: {recipient: "john@example.com", subject: "...", body: "..."}
Safety Level: 2 (Notify)
```

### Step 3: Queued for Approval
```
Action queued for approval
Action ID: action-20260331120000
Approval note: obsidian-vault/Approvals/action-20260331120000.md
```

### Step 4: User Reviews
```
# User opens approval note in Obsidian
# Reviews action details, parameters, safety level
# Decides to approve or reject
```

### Step 5: User Approves
```bash
# Via CLI
python -m mcp_servers.digital_fte_server.approval.cli approve action-20260331120000

# Or via agent skill
claude-code "Approve action action-20260331120000"
```

### Step 6: Action Executed
```
Executing approved action...
[PASS] Email sent successfully
Action moved to: obsidian-vault/Done/action-20260331120000.md
```

---

## Rate Limits

Each tool has daily rate limits:

| Tool | Daily Limit | Current Usage | Reset Time |
|------|-------------|---------------|------------|
| send-email | 100 | 15 | Midnight UTC |
| linkedin-post | 100 | 3 | Midnight UTC |
| whatsapp-send | 1000 | 45 | Midnight UTC |

**Rate Limit Exceeded:**
```
Error: Rate limit exceeded for send-email
Daily limit: 100
Current usage: 100
Retry after: 2026-04-01T00:00:00Z (8 hours)
```

---

## Input Validation

All parameters are validated before queuing:

### Email Validation
- **Format:** RFC 5322 compliant
- **Example:** `user@example.com`
- **Invalid:** `user@`, `@example.com`, `user`

### Phone Number Validation
- **Format:** E.164 (international format)
- **Example:** `+1234567890`
- **Invalid:** `1234567890`, `+1-234-567-8900`, `(123) 456-7890`

### Content Validation
- **Email subject:** 1-200 characters
- **Email body:** 1-10,000 characters
- **LinkedIn post:** 1-3,000 characters
- **WhatsApp message:** 1-5,000 characters

**Validation Error:**
```
Error: Invalid email address format
Provided: user@
Expected: user@example.com
```

---

## Error Handling

### Authentication Errors
```
Error: Gmail API authentication failed
Reason: OAuth token expired
Action: Re-authenticate with: python watchers/gmail_watcher/auth.py
```

### Network Errors
```
Error: Network timeout
Reason: Could not reach Gmail API
Action: Check internet connection and retry
```

### API Errors
```
Error: LinkedIn API error 403
Reason: Insufficient permissions
Action: Re-authenticate and grant required permissions
```

### Validation Errors
```
Error: Invalid parameters
Field: recipient
Reason: Email address format invalid
Provided: user@
Expected: user@example.com
```

---

## MCP Server Configuration

The MCP server must be running for tools to work:

**Start Server:**
```bash
cd mcp-servers/digital-fte-server
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Check Server Health:**
```bash
curl http://localhost:8000/health

# Response:
# {
#   "status": "healthy",
#   "timestamp": "2026-03-31T12:00:00Z",
#   "version": "0.1.0"
# }
```

**List Available Tools:**
```bash
curl http://localhost:8000/tools/list

# Response:
# [
#   {
#     "name": "send-email",
#     "description": "Send an email via Gmail API",
#     "parameters": {...}
#   },
#   ...
# ]
```

---

## Integration with Claude Code

### Register MCP Server

Add to `.claude/config.json`:

```json
{
  "mcpServers": {
    "digital-fte": {
      "url": "http://localhost:8000",
      "tools": ["send-email", "linkedin-post", "whatsapp-send"]
    }
  }
}
```

### Invoke from Claude Code

```
claude-code "Send email to john@example.com with subject 'Test'"
```

Claude will:
1. Detect MCP tool invocation
2. Call MCP server `/tools/invoke` endpoint
3. Receive action ID and approval status
4. Create approval note if Level 2+
5. Wait for user approval
6. Execute action after approval

---

## Examples

### Example 1: Send Email with Approval

```bash
# User request
claude-code "Send email to john@example.com with subject 'Project Update' and body 'The project is on track for Q2 launch.'"

# Claude invokes MCP tool
# Action queued for approval (Level 2)
# Approval note created

# User reviews and approves
python -m mcp_servers.digital_fte_server.approval.cli approve action-20260331120000

# Email sent
# [PASS] Email sent successfully to john@example.com
```

### Example 2: LinkedIn Post with Template

```bash
# User request
claude-code "Post to LinkedIn using milestone template: We hit 10,000 users!"

# Claude generates post using template engine
# Content: "🎉 We hit 10,000 users! This milestone represents..."

# Action queued for approval (Level 2)
# User reviews content in approval note

# User approves
claude-code "Approve action action-20260331120100"

# Post published
# [PASS] LinkedIn post published
# Post URL: https://linkedin.com/posts/...
```

### Example 3: WhatsApp Message with Retry

```bash
# User request
claude-code "Send WhatsApp to +1234567890: Meeting confirmed for tomorrow at 2pm"

# Action queued for approval
# User approves

# First attempt fails (network error)
# Retry 1 after 1s: Failed
# Retry 2 after 2s: Failed
# Retry 3 after 4s: Success

# [PASS] WhatsApp message sent (3 attempts, 7.5s)
```

---

## Audit Trail

All MCP tool invocations are logged to SQLite database:

**Database:** `watchers/shared/digital_fte.db`

**Table:** `actions`

**Fields:**
- `action_id`: Unique identifier
- `action_type`: Tool name (send-email, linkedin-post, whatsapp-send)
- `parameters`: JSON parameters
- `safety_level`: 0-3
- `status`: pending, approved, rejected, executed, failed
- `created_timestamp`: When action was created
- `approved_timestamp`: When action was approved
- `executed_timestamp`: When action was executed
- `audit_trail`: JSON array of state transitions

**Query Audit Trail:**
```bash
sqlite3 watchers/shared/digital_fte.db "SELECT * FROM actions WHERE action_type='send-email' ORDER BY created_timestamp DESC LIMIT 10;"
```

---

## Best Practices

1. **Review before approving**: Always check approval notes before approving actions
2. **Use descriptive subjects**: Clear email subjects help with approval review
3. **Test with drafts first**: Create drafts before sending to verify content
4. **Monitor rate limits**: Check daily usage to avoid hitting limits
5. **Keep credentials fresh**: Re-authenticate before tokens expire
6. **Review audit trail**: Periodically check action history for anomalies
7. **Use templates**: Leverage template engine for consistent messaging

---

## Security Considerations

- **No auto-execution**: Level 2+ actions always require approval
- **Parameter validation**: All inputs validated before queuing
- **Rate limiting**: Prevents abuse and API quota exhaustion
- **Audit logging**: Complete trail of all actions
- **Credential isolation**: API credentials stored in OS keychain
- **Approval expiration**: Pending approvals expire after 24 hours

---

## Notes

- MCP server must be running for tools to work
- All actions logged to database for audit trail
- Approval notes created in Obsidian vault
- Rate limits reset at midnight UTC
- Failed actions can be retried (3 attempts with exponential backoff)
- Approved actions execute immediately
