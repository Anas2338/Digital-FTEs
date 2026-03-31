# Reasoning Plan Agent Skill

**Purpose**: Autonomous plan generation for complex tasks with structured execution tracking

**Version**: 1.0.0

**Category**: Autonomous Agent

---

## Description

This skill enables Claude to autonomously detect complex tasks in the `/Needs_Action` folder and generate structured Plan.md files with clear steps, success criteria, dependencies, and rollback procedures. The agent monitors task execution, validates completion, and re-evaluates plans when steps fail.

This implements the "Ralph Wiggum Stop Hook" pattern - the agent iterates until the task is complete or explicitly stopped.

---

## Automatic Triggers

The reasoning-plan skill activates automatically when:

1. **New task detected** in `obsidian-vault/Needs_Action/`
2. **Complexity score >= 25** (configurable threshold)
3. **No existing Plan.md** for the task

The agent will:
- Analyze task complexity
- Generate Plan.md if threshold exceeded
- Begin autonomous execution
- Track progress and validate completion

---

## Commands

### analyze-complexity

Analyze a task's complexity score without generating a plan.

**Usage:**
```
claude-code "Analyze complexity of task in Needs_Action/task-name.md"
```

**Output:**
- Complexity score (0-100+)
- Breakdown by factor (word count, actions, dependencies, technical terms)
- Complexity level (trivial, simple, moderate, complex, very_complex)
- Recommendation (requires planning: yes/no)

**Example:**
```
claude-code "Analyze complexity of the payment integration task"

# Output:
# Complexity Score: 47
# Level: complex
# Requires Planning: YES
# Breakdown:
#   - Action verbs: 8 (score: 16)
#   - Dependencies: 5 (score: 15)
#   - Technical terms: 6 (score: 12)
#   - Conditionals: 2 (score: 6)
```

---

### generate-plan

Manually trigger plan generation for a task.

**Usage:**
```
claude-code "Generate plan for [task description or file]"
```

**Parameters:**
- `task`: Task description or path to task file in Needs_Action

**Output:**
- Plan.md file created in same directory as task
- Plan includes: Goal, Context, Steps, Success Criteria, Risks, Rollback

**Example:**
```
claude-code "Generate plan for Needs_Action/implement-oauth.md"

# Creates: Needs_Action/implement-oauth-plan.md
```

---

### execute-plan

Execute a plan autonomously with progress tracking.

**Usage:**
```
claude-code "Execute plan for [task name]"
```

**Behavior:**
- Reads Plan.md
- Executes steps sequentially
- Updates step status (pending → in-progress → completed)
- Validates success criteria after each step
- Re-evaluates plan if step fails
- Moves task to /Done when all criteria met

**Example:**
```
claude-code "Execute plan for implement-oauth"

# Agent begins autonomous execution:
# [STEP 1/5] Setting up OAuth provider configuration...
# [PASS] Step 1 completed
# [STEP 2/5] Implementing authorization endpoint...
# [IN PROGRESS] Writing endpoint handler...
```

---

### validate-completion

Check if a task's success criteria are met.

**Usage:**
```
claude-code "Validate completion of [task name]"
```

**Checks:**
- All plan steps marked completed
- All success criteria validated
- No blocking errors or failures
- Rollback procedure not triggered

**Output:**
- Completion status (complete/incomplete)
- Remaining criteria
- Blocking issues (if any)

---

### re-evaluate-plan

Re-evaluate a plan when a step fails or requirements change.

**Usage:**
```
claude-code "Re-evaluate plan for [task name] due to [reason]"
```

**Behavior:**
- Analyzes failure reason
- Generates alternative approaches
- Updates Plan.md with new steps
- Preserves completed steps
- Adds lessons learned section

**Example:**
```
claude-code "Re-evaluate plan for payment-integration due to Stripe API deprecation"

# Plan updated with alternative approach using Stripe v2 API
# Previous steps preserved, new steps added
```

---

## Plan.md Structure

Generated plans follow this structure:

```markdown
---
task_id: task-20260330-001
status: in_progress
created: 2026-03-30T10:00:00Z
updated: 2026-03-30T10:30:00Z
complexity_score: 47
---

# Plan: [Task Name]

## Goal

[Clear, measurable objective]

## Context

[Background information, constraints, requirements]

## Steps

### Step 1: [Step Name]
**Status**: completed
**Estimated Time**: 30 minutes
**Dependencies**: None

[Detailed description of what to do]

**Success Criteria:**
- [ ] Criterion 1
- [X] Criterion 2

**Validation:**
- Test command: `npm test auth`
- Expected result: All tests pass

---

### Step 2: [Step Name]
**Status**: in_progress
**Estimated Time**: 1 hour
**Dependencies**: Step 1

[Description]

---

## Success Criteria

Overall task completion requires:

- [X] All steps completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code reviewed

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API rate limit | Medium | High | Implement exponential backoff |
| Auth token expiry | Low | Medium | Add token refresh logic |

## Rollback Procedure

If task fails or needs to be reverted:

1. Revert database migrations: `npm run migrate:rollback`
2. Remove new endpoints from routes
3. Restore previous auth configuration
4. Clear cached tokens

## Lessons Learned

[Added during execution or re-evaluation]

- Stripe v1 API deprecated, switched to v2
- Rate limiting more aggressive than documented
```

---

## Complexity Scoring

The complexity scorer uses these factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Word count | 1 pt / 20 words | Longer tasks are more complex |
| Action verbs | 2 pts each | create, implement, build, etc. |
| Dependencies | 3 pts each | after, before, depends on, etc. |
| Technical terms | 2 pts each | API, database, integration, etc. |
| Conditionals | 3 pts each | if, then, when, unless, etc. |
| Sentences | 1 pt each | Beyond first sentence |
| List items | 2 pts each | Bullet points indicate steps |

**Complexity Levels:**
- 0-9: Trivial (no planning needed)
- 10-24: Simple (no planning needed)
- 25-49: Moderate (planning recommended)
- 50-74: Complex (planning required)
- 75+: Very Complex (planning required, consider breaking down)

**Default Threshold**: 25 (configurable in config.py)

---

## Status Tracking

Plan steps progress through these statuses:

1. **pending** - Not started
2. **in_progress** - Currently executing
3. **completed** - Finished successfully
4. **failed** - Execution failed
5. **skipped** - Skipped due to conditional logic
6. **validated** - Completed and success criteria verified

Overall plan statuses:

- **draft** - Plan created, not started
- **in_progress** - Executing steps
- **blocked** - Waiting on external dependency
- **completed** - All steps done, criteria met
- **failed** - Unrecoverable failure
- **abandoned** - User cancelled

---

## Success Criteria Validation

After each step, the agent validates success criteria:

**Automated Checks:**
- Run test commands
- Check file existence
- Verify API responses
- Validate database state

**Manual Checks:**
- User confirmation required
- Visual inspection needed
- External approval needed

**Validation Failure:**
- Mark step as failed
- Trigger plan re-evaluation
- Suggest alternative approaches

---

## Plan Re-evaluation

Plans are re-evaluated when:

1. **Step fails** - Alternative approach needed
2. **Requirements change** - User updates task
3. **Blocker encountered** - External dependency unavailable
4. **Time exceeded** - Step taking longer than estimated

**Re-evaluation Process:**
1. Analyze failure reason
2. Research alternative approaches
3. Update plan with new steps
4. Preserve completed work
5. Document lessons learned
6. Resume execution

---

## Task Completion Workflow

When all success criteria are met:

1. **Validate completion** - Run all validation checks
2. **Update task status** - Mark as completed in frontmatter
3. **Move to /Done** - Relocate task file from /Needs_Action to /Done
4. **Update Dashboard.md** - Add completion summary
5. **Archive Plan.md** - Move plan to /Done alongside task
6. **Log metrics** - Record completion time, steps, re-evaluations

---

## Configuration

Edit `.claude/skills/reasoning-plan/config.py` to customize:

```python
# Complexity threshold (default: 25)
COMPLEXITY_THRESHOLD = 25

# Auto-execute plans (default: False - requires user approval)
AUTO_EXECUTE = False

# Max execution time per step (minutes)
MAX_STEP_TIME = 60

# Max re-evaluation attempts
MAX_REEVALUATIONS = 3

# Validation timeout (seconds)
VALIDATION_TIMEOUT = 30
```

---

## Integration with Approval Workflow

Complex tasks may require approval for certain steps:

- **Level 0-1 steps** - Auto-execute (read-only, low-risk)
- **Level 2 steps** - Queue for approval (send emails, post to social)
- **Level 3 steps** - Explicit approval (financial, delete operations)

The agent will pause execution and wait for approval before proceeding with Level 2+ steps.

---

## Examples

### Example 1: Automatic Plan Generation

```bash
# User creates task in Needs_Action
echo "Implement OAuth2 authentication with Google and GitHub providers..." > obsidian-vault/Needs_Action/oauth-task.md

# Agent detects task (complexity score: 52)
# Automatically generates Plan.md
# Begins execution with user approval

# Agent output:
# [DETECT] New task: oauth-task.md
# [ANALYZE] Complexity score: 52 (complex)
# [GENERATE] Plan created: oauth-task-plan.md
# [READY] Plan has 7 steps, estimated 4 hours
# [PROMPT] Execute plan? (yes/no)
```

### Example 2: Plan Re-evaluation After Failure

```bash
# Step 3 fails due to API deprecation
# Agent re-evaluates plan

claude-code "Re-evaluate oauth plan due to Google OAuth API v1 deprecation"

# Agent output:
# [ANALYZE] Step 3 failed: API endpoint deprecated
# [RESEARCH] Investigating Google OAuth v2 migration
# [UPDATE] Plan updated with v2 implementation steps
# [PRESERVE] Steps 1-2 completed, preserved
# [RESUME] Continuing from Step 3 (updated)
```

### Example 3: Manual Complexity Check

```bash
# Check if task needs planning before starting

claude-code "Analyze complexity of Needs_Action/refactor-database.md"

# Output:
# Complexity Score: 68 (complex)
# Requires Planning: YES
# Breakdown:
#   - 12 action verbs (24 pts)
#   - 8 dependencies (24 pts)
#   - 7 technical terms (14 pts)
#   - 3 conditionals (9 pts)
# Recommendation: Generate plan before starting
```

---

## Error Handling

- **Plan generation fails**: Log error, notify user, save partial plan
- **Step execution fails**: Mark failed, trigger re-evaluation
- **Validation timeout**: Mark step as needs_manual_check
- **Max re-evaluations exceeded**: Mark plan as failed, notify user
- **User cancellation**: Mark plan as abandoned, preserve progress

---

## Notes

- Plans are versioned (v1, v2, etc.) when re-evaluated
- Completed plans archived to /Done for future reference
- Complexity threshold can be adjusted per project
- Agent respects approval workflow for sensitive operations
- All plan updates logged in audit trail
