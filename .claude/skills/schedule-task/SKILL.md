# Schedule Task Agent Skill

**Purpose**: Create and manage scheduled tasks with cron-like scheduling

**Version**: 1.0.0

**Category**: Task Automation

---

## Description

This skill enables users to create, manage, and monitor scheduled tasks that run automatically at specified times. Tasks are stored in the Obsidian vault with full execution history and support retry logic, missed schedule handling, and conflict resolution.

---

## Commands

### create-schedule

Create a new scheduled task.

**Usage:**
```
claude-code "Schedule [task description] to run [schedule]"
```

**Parameters:**
- `task_id`: Unique identifier for the task
- `schedule`: Cron expression (e.g., "0 9 * * 1" for Monday 9am)
- `command`: Command to execute
- `description`: Optional task description
- `priority`: Optional priority (1-10, default: 5)

**Example:**
```
claude-code "Schedule weekly report to run every Monday at 9am"

# Creates schedule with:
# - task_id: weekly-report
# - schedule: 0 9 * * 1
# - command: python scripts/generate_report.py
```

**Cron Expression Format:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-6, Sunday=0)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

**Common Patterns:**
- `0 9 * * *` - Daily at 9am
- `0 9 * * 1` - Every Monday at 9am
- `0 0 1 * *` - First day of every month at midnight
- `*/15 * * * *` - Every 15 minutes
- `0 9-17 * * 1-5` - Every hour from 9am-5pm, Monday-Friday

---

### list-schedules

List all scheduled tasks.

**Usage:**
```
claude-code "List scheduled tasks"
```

**Optional Filters:**
- `status`: Filter by status (active, paused, disabled)

**Example:**
```
claude-code "List active scheduled tasks"

# Output:
# Scheduled Tasks (3 active):
#
# 1. weekly-report
#    Schedule: 0 9 * * 1 (Every Monday at 9am)
#    Last run: 2026-03-24T09:00:00Z
#    Next run: 2026-03-31T09:00:00Z
#    Success rate: 95% (19/20)
#
# 2. daily-backup
#    Schedule: 0 2 * * * (Daily at 2am)
#    Last run: 2026-03-30T02:00:00Z
#    Next run: 2026-03-31T02:00:00Z
#    Success rate: 100% (30/30)
```

---

### pause-schedule

Pause a scheduled task (stops execution without deleting).

**Usage:**
```
claude-code "Pause schedule [task-id]"
```

**Example:**
```
claude-code "Pause schedule weekly-report"

# Task paused - will not execute until resumed
```

---

### resume-schedule

Resume a paused scheduled task.

**Usage:**
```
claude-code "Resume schedule [task-id]"
```

**Example:**
```
claude-code "Resume schedule weekly-report"

# Task resumed - will execute at next scheduled time
```

---

### delete-schedule

Delete a scheduled task permanently.

**Usage:**
```
claude-code "Delete schedule [task-id]"
```

**Example:**
```
claude-code "Delete schedule weekly-report"

# Schedule deleted - execution history archived
```

---

### run-now

Execute a scheduled task immediately (outside of schedule).

**Usage:**
```
claude-code "Run schedule [task-id] now"
```

**Example:**
```
claude-code "Run schedule weekly-report now"

# Executing task immediately...
# [PASS] Task completed in 2.3s
```

---

### view-history

View execution history for a scheduled task.

**Usage:**
```
claude-code "Show execution history for [task-id]"
```

**Example:**
```
claude-code "Show execution history for weekly-report"

# Execution History (last 10):
#
# 2026-03-24 09:00:00 [PASS] 2.1s (1 attempt)
# 2026-03-17 09:00:00 [PASS] 2.3s (1 attempt)
# 2026-03-10 09:00:00 [FAIL] 5.2s (3 attempts) - API timeout
# 2026-03-03 09:00:00 [PASS] 1.9s (1 attempt)
```

---

## Retry Logic

All scheduled tasks use automatic retry with exponential backoff:

1. **First attempt**: Execute immediately
2. **Second attempt**: Wait 1 second, retry
3. **Third attempt**: Wait 2 seconds, retry
4. **Fourth attempt**: Wait 4 seconds, retry

After 3 retries (4 total attempts), task is marked as failed.

**Example:**
```
Task: daily-backup
Attempt 1: Failed (network error)
Wait 1s...
Attempt 2: Failed (network error)
Wait 2s...
Attempt 3: Success
Result: [PASS] Completed in 7.5s (3 attempts)
```

---

## Missed Schedule Handling

When the system starts up, it checks for schedules that should have run while offline:

**24-Hour Catchup Window:**
- Schedules missed within last 24 hours: **Execute immediately**
- Schedules missed more than 24 hours ago: **Skip, wait for next occurrence**

**Example:**
```
System offline: Friday 5pm - Monday 8am

Scheduled tasks:
- daily-backup (runs at 2am daily)
  - Saturday 2am: Missed (within 24h) → Execute on startup
  - Sunday 2am: Missed (within 24h) → Execute on startup
  - Monday 2am: Missed (within 24h) → Execute on startup

- weekly-report (runs Monday 9am)
  - Monday 9am: Not yet due → Execute at 9am as scheduled
```

---

## Conflict Resolution

When multiple tasks are scheduled for the same time:

**Execution Order:**
1. Sort by priority (1 = highest, 10 = lowest)
2. Within same priority, sort by task_id alphabetically
3. Execute sequentially (not in parallel)

**Example:**
```
Scheduled for Monday 9am:
- weekly-report (priority: 5)
- send-newsletter (priority: 3)
- cleanup-logs (priority: 7)

Execution order:
1. send-newsletter (priority 3)
2. weekly-report (priority 5)
3. cleanup-logs (priority 7)
```

---

## Execution History Tracking

Each schedule stores the last 100 executions with:

- **Timestamp**: When task executed
- **Status**: Success or failure
- **Duration**: Execution time in seconds
- **Attempts**: Number of retry attempts
- **Output**: Command output (truncated to 200 chars)
- **Error**: Error message if failed

**Storage Location:**
- `obsidian-vault/Schedules/[task-id].md`

**Frontmatter Metrics:**
```yaml
execution_count: 45
success_count: 43
failure_count: 2
last_run: 2026-03-30T09:00:00Z
next_run: 2026-04-06T09:00:00Z
```

---

## Platform Support

### Unix/Linux
- Uses **crontab** for scheduling
- Requires cron daemon running
- Tasks persist across reboots

### Windows
- Uses **Task Scheduler** for scheduling
- Requires Task Scheduler service running
- Tasks persist across reboots

### macOS
- Uses **crontab** (same as Linux)
- Alternative: launchd (future support)

---

## Examples

### Example 1: Daily Backup

```bash
# Create daily backup at 2am
claude-code "Schedule daily backup to run at 2am every day"

# Agent creates:
# - task_id: daily-backup
# - schedule: 0 2 * * *
# - command: python scripts/backup.py
# - priority: 3 (high priority)

# Task runs automatically every day at 2am
# Execution history tracked in obsidian-vault/Schedules/daily-backup.md
```

### Example 2: Weekly Report

```bash
# Create weekly report every Monday at 9am
claude-code "Schedule weekly report to run every Monday at 9am"

# Agent creates:
# - task_id: weekly-report
# - schedule: 0 9 * * 1
# - command: python scripts/generate_report.py
# - priority: 5 (normal priority)

# View execution history
claude-code "Show execution history for weekly-report"

# Pause during vacation
claude-code "Pause schedule weekly-report"

# Resume after vacation
claude-code "Resume schedule weekly-report"
```

### Example 3: Hourly Health Check

```bash
# Create hourly health check
claude-code "Schedule health check to run every hour"

# Agent creates:
# - task_id: health-check
# - schedule: 0 * * * *
# - command: python scripts/health_check.py
# - priority: 8 (low priority)

# Run immediately to test
claude-code "Run schedule health-check now"

# Check if it's working
claude-code "Show execution history for health-check"
```

---

## Error Handling

- **Invalid cron expression**: Returns error with format help
- **Task already exists**: Returns error, suggest using update command
- **Task not found**: Returns error with list of available tasks
- **Execution timeout**: Task killed after 1 hour, marked as failed
- **Permission denied**: Returns error, suggest running with appropriate permissions

---

## Best Practices

1. **Use descriptive task IDs**: `weekly-report` not `task1`
2. **Set appropriate priorities**: Critical tasks = 1-3, Normal = 4-6, Low = 7-10
3. **Test with run-now first**: Verify task works before scheduling
4. **Monitor execution history**: Check for failures and adjust
5. **Use catchup window wisely**: Critical tasks should run even if missed
6. **Avoid overlapping schedules**: Space out resource-intensive tasks
7. **Set realistic timeouts**: Long-running tasks may need custom timeout

---

## Integration with Approval Workflow

Scheduled tasks bypass the approval workflow since they are pre-approved by the user when created. However:

- **Task creation**: Requires user confirmation
- **Task modification**: Requires user confirmation
- **Task deletion**: Requires user confirmation
- **Manual execution**: Runs immediately without approval

---

## Monitoring and Alerts

The agent monitors scheduled tasks and alerts on:

- **Consecutive failures**: 3+ failures in a row
- **Missed schedules**: Task missed outside catchup window
- **Long execution times**: Task taking 2x longer than average
- **Low success rate**: Success rate drops below 80%

Alerts are posted to `obsidian-vault/Alerts/` for review.

---

## Notes

- All times are in UTC
- Schedules persist across system restarts
- Execution history limited to last 100 runs
- Tasks run with same permissions as the scheduler process
- Long-running tasks (>1 hour) are automatically terminated
- Concurrent execution of same task is prevented (IgnoreNew policy)
