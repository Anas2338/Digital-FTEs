# Feature Specification: Silver Tier Functional Assistant

**Feature Branch**: `001-silver-tier-functional`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Silver Tier: Functional Assistant - All Bronze requirements plus: Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn), Automatically Post on LinkedIn about business to generate sales, Claude reasoning loop that creates Plan.md files, One working MCP server for external action (e.g., sending emails), Human-in-the-loop approval workflow for sensitive actions, Basic scheduling via cron or Task Scheduler, All AI functionality should be implemented as Agent Skills"

## Clarifications

### Session 2026-03-30

- Q: Which WhatsApp API should be used for the Silver Tier watcher (official WhatsApp Business API vs unofficial API)? → A: Unofficial WhatsApp API (e.g., whatsapp-web.js) for faster MVP development, with documented migration path to official API for production
- Q: Which LinkedIn API should be used for posting (official LinkedIn API vs unofficial API)? → A: Unofficial LinkedIn API (e.g., linkedin-api library) for faster MVP development, with documented migration path to official API for production
- Q: How should the reasoning loop be triggered (automatic vs manual vs hybrid)? → A: Automatic trigger - reasoning loop automatically analyzes every note created in /Needs_Action and generates Plan.md if task complexity exceeds threshold
- Q: Should AI automatically generate LinkedIn post content from detected milestones, or only draft when explicitly asked? → A: AI drafts only from explicit triggers - user can request AI to draft a post about specific topic, but no automatic milestone detection
- Q: How should users be notified when actions are queued for approval? → A: File watcher + CLI polling - user runs CLI command to check pending approvals, or optionally sets up file watcher to monitor /Approvals folder

## Reference Architecture Analysis

### Industry Standards for Multi-Channel Monitoring Systems

**Multi-Watcher Architectures**:
- Event bus pattern for coordinating multiple watchers
- Shared event queue with priority levels (critical, high, normal, low)
- Centralized logging and monitoring dashboard
- Independent watcher processes with health checks
- Graceful degradation when individual watchers fail

**Social Media Automation Patterns**:
- Content calendar and scheduling systems
- Rate limiting and API quota management (LinkedIn: 100 posts/day, Twitter: 300 posts/day)
- A/B testing for post performance
- Engagement tracking and analytics
- Content approval workflows before publishing

**MCP (Model Context Protocol) Server Patterns**:
- RESTful API design with versioning
- Tool registration and discovery
- Request/response schemas with validation
- Error handling with retry logic
- Authentication and authorization layers

**Human-in-the-Loop (HITL) Workflows**:
- Action classification by risk level (read, draft, send, financial)
- Approval queue with timeout policies
- Notification systems (email, SMS, desktop)
- Audit trail for all approvals/rejections
- Batch approval for similar actions

**Task Scheduling Patterns**:
- Cron expressions for recurring tasks (Unix/Linux)
- Task Scheduler XML definitions (Windows)
- Job queues with priority and retry logic
- Distributed scheduling for high availability
- Time zone handling for global operations

### AI Agent Reasoning Loop Patterns

**Planning and Execution Frameworks**:
- ReAct (Reasoning + Acting) pattern for iterative problem-solving
- Chain-of-Thought prompting for complex decisions
- Self-reflection and validation before action execution
- Plan generation with success criteria and rollback procedures
- Memory systems for context persistence across sessions

## Current Architecture Analysis

### Existing Components (from Bronze Tier)

**Implemented**:
- `obsidian-vault/` with /Inbox, /Needs_Action, /Done folders
- Dashboard.md with dynamic folder counts and recent activity
- Company_Handbook.md for business documentation
- Gmail watcher monitoring labeled emails
- Claude Code vault integration (read/write operations)
- Agent skills: vault-create-note, vault-read-note, vault-move-note, vault-update-dashboard
- YAML frontmatter for note metadata
- Watcher logging and error handling

**Architecture Strengths**:
- Local-first storage with Obsidian vault
- Modular agent skills following .claude/skills/ pattern
- Event-driven watcher architecture
- Markdown-based knowledge management

**Architecture Gaps for Silver Tier**:
- No multi-watcher coordination or event bus
- No MCP server implementation
- No approval workflow system
- No scheduling infrastructure
- No LinkedIn or WhatsApp watchers
- No outbound action capabilities (sending emails, posting to social media)
- No reasoning loop for plan generation

### Integration Points

**Watcher Layer**:
- Existing: Gmail watcher (Python, OAuth2, label-based filtering)
- New: WhatsApp watcher, LinkedIn watcher
- Coordination: Shared event queue or independent processes with centralized logging

**Action Layer**:
- Existing: Claude Code file operations (Read, Write, Edit)
- New: MCP server for external actions (email send, LinkedIn post)
- Approval: HITL workflow intercepting Level 2+ actions

**Intelligence Layer**:
- Existing: Claude Code agent with skills
- New: Reasoning loop for Plan.md generation
- Enhancement: Agent skills for all new capabilities

## User Scenarios & Testing

### User Story 1 - Multi-Channel Watcher System (Priority: P1)

As a business owner, I need watchers monitoring Gmail, WhatsApp, and LinkedIn simultaneously, so all important communications are captured in my vault regardless of channel.

**Why this priority**: Multi-channel monitoring is the foundation for a comprehensive assistant. Without this, the system only sees email (Bronze Tier limitation). This delivers immediate value by providing complete visibility across communication channels.

**Independent Test**: Can be fully tested by sending a test email, WhatsApp message, and LinkedIn notification, then verifying three separate notes appear in obsidian-vault/Inbox/ within the polling interval, each with channel-specific metadata.

**Acceptance Scenarios**:

1. **Given** all three watchers are running, **When** a new Gmail email with "ToVault" label arrives, **Then** a note is created in /Inbox with source: "gmail", sender, subject, and body
2. **Given** all three watchers are running, **When** a new WhatsApp message arrives in the monitored account, **Then** a note is created in /Inbox with source: "whatsapp", sender phone/name, and message text
3. **Given** all three watchers are running, **When** a LinkedIn notification arrives (message, connection request, or post mention), **Then** a note is created in /Inbox with source: "linkedin", sender profile, and notification content
4. **Given** one watcher fails (e.g., LinkedIn API error), **When** the other watchers continue running, **Then** Gmail and WhatsApp notes are still created and the failure is logged without crashing the system

---

### User Story 2 - MCP Server for External Actions (Priority: P2)

As a business owner, I need an MCP server that can send emails and post to LinkedIn, so the AI assistant can take actions on my behalf instead of just monitoring.

**Why this priority**: This transforms the system from passive monitoring to active assistance. The MCP server enables outbound actions while maintaining the constitution's action safety levels. This is P2 because watchers (P1) must capture context before the agent can respond.

**Independent Test**: Can be fully tested by invoking the MCP server's send-email tool with test parameters and verifying the email is sent, then invoking the linkedin-post tool and verifying the post appears on LinkedIn.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** Claude Code invokes the send-email tool with recipient, subject, and body, **Then** an email is sent via Gmail API and a confirmation note is created in /Done
2. **Given** the MCP server is running, **When** Claude Code invokes the linkedin-post tool with post content, **Then** the content is posted to LinkedIn and a confirmation note is created in /Done
3. **Given** the MCP server is running, **When** an action fails (e.g., LinkedIn API rate limit), **Then** an error is returned to Claude Code with retry-after information and the failure is logged
4. **Given** the MCP server is running, **When** Claude Code invokes a tool with invalid parameters, **Then** a validation error is returned before any external API call is made

---

### User Story 3 - Human-in-the-Loop Approval Workflow (Priority: P3)

As a business owner, I need to approve sensitive actions before they execute, so the AI assistant never sends emails or posts to social media without my explicit consent.

**Why this priority**: This implements the constitution's action safety levels (Level 2: Confirm, Level 3: Explicit Approval). This is P3 because the MCP server (P2) must exist before we can intercept its actions for approval.

**Independent Test**: Can be fully tested by having Claude Code attempt to send an email, verifying the action is queued for approval, approving it via CLI command, and confirming the email is then sent.

**Acceptance Scenarios**:

1. **Given** Claude Code wants to send an email (Level 2 action), **When** the MCP server receives the request, **Then** the action is queued in obsidian-vault/Approvals/ as a note
2. **Given** an action is pending approval, **When** the user runs the approval-review CLI command, **Then** all pending actions are listed with risk level, action type, and parameters for review
3. **Given** an action is pending approval, **When** the user runs the approve CLI command with action ID, **Then** the action executes and moves from /Approvals to /Done
4. **Given** an action is pending approval, **When** the user runs the reject CLI command with action ID and reason, **Then** the action is cancelled and moved to /Rejected with rejection reason

---

### User Story 4 - LinkedIn Auto-Posting for Business Development (Priority: P4)

As a business owner, I need the AI assistant to automatically post business updates to LinkedIn, so I maintain consistent social media presence without manual effort.

**Why this priority**: This delivers business value through automated marketing. This is P4 because it requires watchers (P1), MCP server (P2), and approval workflow (P3) to function safely.

**Independent Test**: Can be fully tested by creating a business update note in obsidian-vault/Content_Queue/, waiting for the scheduled posting time, approving the post, and verifying it appears on LinkedIn.

**Acceptance Scenarios**:

1. **Given** a note exists in /Content_Queue with frontmatter schedule: "2026-03-30 09:00", **When** the scheduler runs at 09:00, **Then** the post is queued for approval with content from the note body
2. **Given** a LinkedIn post is approved, **When** the MCP server executes the post action, **Then** the content appears on LinkedIn and the note moves from /Content_Queue to /Done
3. **Given** the user invokes the linkedin-draft agent skill with a topic (e.g., "draft post about Q1 revenue milestone"), **When** the AI generates the draft, **Then** the draft is saved to /Content_Queue for review and scheduling
4. **Given** LinkedIn API rate limits are reached, **When** the scheduler attempts to post, **Then** the post is rescheduled for the next available time slot and the user is notified

---

### User Story 5 - Claude Reasoning Loop for Plan Generation (Priority: P5)

As a business owner, I need the AI assistant to autonomously create Plan.md files for complex tasks, so I have structured execution plans without manually breaking down work.

**Why this priority**: This enables autonomous planning and task decomposition. This is P5 because it's an intelligence enhancement that builds on the action capabilities from P1-P4.

**Independent Test**: Can be fully tested by creating a note in /Needs_Action with a complex task description, triggering the reasoning loop, and verifying a Plan.md file is created with structured steps, success criteria, and dependencies.

**Acceptance Scenarios**:

1. **Given** a note in /Needs_Action contains a complex task (e.g., "Launch new product line"), **When** the reasoning loop automatically detects the note, **Then** a Plan.md file is created in the same folder with sections: Goal, Steps, Success Criteria, Dependencies, Risks
2. **Given** a Plan.md file exists, **When** the AI assistant executes a step, **Then** the plan is updated with step status (pending, in-progress, completed) and execution notes
3. **Given** a plan step fails, **When** the reasoning loop re-evaluates, **Then** the plan is updated with alternative approaches or escalation to user
4. **Given** all plan steps are completed, **When** the reasoning loop validates success criteria, **Then** the task note moves from /Needs_Action to /Done and a summary is added to Dashboard.md

---

### User Story 6 - Scheduled Task Execution (Priority: P6)

As a business owner, I need tasks to run automatically on a schedule (daily reports, weekly summaries, monthly reviews), so routine work happens without my intervention.

**Why this priority**: This enables time-based automation. This is P6 because it's an operational enhancement that leverages all previous capabilities.

**Independent Test**: Can be fully tested by creating a scheduled task (e.g., "Generate weekly summary every Monday at 9am"), waiting for the scheduled time, and verifying the task executes and creates the expected output in the vault.

**Acceptance Scenarios**:

1. **Given** a cron expression "0 9 * * 1" is configured for weekly summary, **When** Monday 9am arrives, **Then** the AI assistant generates a summary of the week's activity and saves it to /Reports
2. **Given** a scheduled task is configured, **When** the system is offline at the scheduled time, **Then** the task is queued and executes when the system comes back online
3. **Given** multiple scheduled tasks exist, **When** two tasks are scheduled for the same time, **Then** they execute sequentially in priority order without conflicts
4. **Given** a scheduled task fails, **When** the retry logic triggers, **Then** the task is retried up to 3 times with exponential backoff before marking as failed

---

### Edge Cases

- What happens when WhatsApp API credentials expire mid-operation?
- How does the system handle LinkedIn post character limits (3000 chars)?
- What happens when the approval queue grows beyond 50 pending actions?
- How does the system handle time zone differences for scheduled tasks?
- What happens when an MCP server action times out (e.g., slow email send)?
- How does the reasoning loop handle circular dependencies in plans?
- What happens when multiple watchers detect the same event (e.g., LinkedIn message also triggers email)?
- How does the system handle conflicting scheduled tasks (e.g., two posts scheduled for same time)?
- What happens when the reasoning loop incorrectly identifies a simple task as complex and generates an unnecessary plan?
- How does the system prevent reasoning loop from generating plans for every minor task in /Needs_Action?

## Requirements

### Functional Requirements

**Watcher Requirements**:
- **FR-001**: System MUST implement WhatsApp watcher using unofficial WhatsApp Web API (e.g., whatsapp-web.js library) monitoring the configured WhatsApp account
- **FR-002**: WhatsApp watcher MUST create notes in /Inbox with source: "whatsapp", sender name/phone, message text, and timestamp
- **FR-003**: System MUST implement LinkedIn watcher using unofficial LinkedIn API (e.g., linkedin-api library) monitoring notifications (messages, connection requests, post mentions)
- **FR-004**: LinkedIn watcher MUST create notes in /Inbox with source: "linkedin", sender profile URL, notification type, content, and timestamp
- **FR-005**: All watchers MUST run as independent processes with individual health checks and restart capability
- **FR-006**: System MUST log all watcher events to a centralized log file with timestamps, watcher name, event type, and status

**MCP Server Requirements**:
- **FR-007**: System MUST implement an MCP server exposing tools: send-email, linkedin-post (using unofficial LinkedIn API), whatsapp-send
- **FR-008**: MCP server MUST validate all tool parameters before execution (email format, character limits, required fields)
- **FR-009**: MCP server MUST return structured responses with success/failure status, action ID, and error details if applicable
- **FR-010**: MCP server MUST log all tool invocations with timestamp, tool name, parameters (sanitized), and result
- **FR-011**: MCP server MUST implement rate limiting per API (Gmail: 100/day, LinkedIn: 100/day, WhatsApp: 1000/day)

**Approval Workflow Requirements**:
- **FR-012**: System MUST classify actions by safety level: Level 0 (auto-execute), Level 1 (notify), Level 2 (confirm), Level 3 (explicit approval)
- **FR-013**: Level 2+ actions MUST be queued in obsidian-vault/Approvals/ as notes with action type, parameters, risk level, and timestamp
- **FR-014**: System MUST provide CLI commands for approval workflow: list-pending, approve <id>, reject <id> <reason>, approve-all
- **FR-015**: Users MUST check pending approvals via CLI polling command (approval-review) or by optionally setting up file watcher to monitor /Approvals folder
- **FR-016**: Approved actions MUST execute immediately and move from /Approvals to /Done with execution timestamp
- **FR-017**: Rejected actions MUST move from /Approvals to /Rejected with rejection reason and timestamp
- **FR-018**: Pending approvals older than 24 hours MUST auto-expire and move to /Expired

**LinkedIn Auto-Posting Requirements**:
- **FR-019**: System MUST monitor obsidian-vault/Content_Queue/ for notes with frontmatter field "schedule: <datetime>"
- **FR-020**: System MUST queue scheduled LinkedIn posts for approval at the specified time
- **FR-021**: System MUST support post templates with variables (e.g., {{company_name}}, {{date}}, {{milestone}})
- **FR-022**: LinkedIn posts MUST respect character limits (3000 chars) and truncate with "..." if exceeded
- **FR-023**: System MUST track post performance (views, likes, comments) and store metrics in note frontmatter
- **FR-024**: System MUST provide linkedin-draft agent skill that generates post content when explicitly invoked by user with topic/context (no automatic milestone detection)

**Reasoning Loop Requirements**:
- **FR-025**: System MUST implement a reasoning loop agent skill that automatically monitors /Needs_Action folder and analyzes new notes for task complexity
- **FR-026**: Reasoning loop MUST automatically generate Plan.md files when task complexity exceeds threshold (e.g., task description >100 words, contains multiple verbs/actions, or includes terms like "launch", "implement", "design")
- **FR-027**: Plan.md files MUST include sections: Goal, Context, Steps (with dependencies), Success Criteria, Risks, Rollback Procedure
- **FR-028**: Reasoning loop MUST validate plans against success criteria before marking tasks complete
- **FR-029**: Reasoning loop MUST update plan status as steps execute (pending → in-progress → completed → validated)
- **FR-030**: Reasoning loop MUST escalate to user when success criteria cannot be met or risks materialize

**Scheduling Requirements**:
- **FR-031**: System MUST support cron expressions for recurring tasks (Unix/Linux) and Task Scheduler XML (Windows)
- **FR-032**: System MUST store scheduled tasks in obsidian-vault/Schedules/ with cron expression, task description, and last run timestamp
- **FR-033**: System MUST execute scheduled tasks with retry logic (3 attempts with exponential backoff: 1s, 2s, 4s)
- **FR-034**: System MUST handle missed schedules (system offline) by executing tasks on next startup if within 24-hour window

**Agent Skills Requirements**:
- **FR-035**: All new AI functionality MUST be implemented as agent skills following .claude/skills/*/SKILL.md pattern
- **FR-036**: System MUST implement agent skills: watcher-status, mcp-invoke, approval-review (CLI polling), linkedin-draft (explicit invocation only), reasoning-plan (with automatic monitoring), schedule-task
- **FR-037**: Agent skills MUST include documentation: purpose, parameters, examples, error handling

### Key Entities

- **Watcher**: Background process monitoring external channel (Gmail, WhatsApp, LinkedIn) with health status, last check timestamp, and error count
- **Event**: Detected change from watcher with source channel, event type, content, timestamp, and processing status
- **MCP Server**: Service exposing tools for external actions with tool registry, rate limits, and execution logs
- **Action**: Requested operation with action type, parameters, safety level, status (pending/approved/rejected/executed), and audit trail
- **Approval Queue**: Collection of pending Level 2+ actions awaiting user review with priority ordering and timeout policies
- **Content Queue**: Folder containing scheduled LinkedIn posts with frontmatter: schedule datetime, post content, status, and performance metrics
- **Plan**: Structured execution plan for complex task with goal, steps (with dependencies), success criteria, risks, and current status
- **Schedule**: Recurring task definition with cron expression, task description, last run timestamp, next run timestamp, and execution history

## Success Criteria

### Measurable Outcomes

- **SC-001**: All three watchers (Gmail, WhatsApp, LinkedIn) run continuously for 7 days without crashes
- **SC-002**: Watchers detect and process new events within one polling interval (3 minutes for Gmail, 5 minutes for WhatsApp/LinkedIn)
- **SC-003**: MCP server responds to tool invocations in under 2 seconds (excluding external API latency)
- **SC-004**: Approval workflow processes user decisions (approve/reject) in under 1 second
- **SC-005**: LinkedIn posts are published within 5 minutes of approval
- **SC-006**: Reasoning loop generates Plan.md files with 5-10 actionable steps for complex tasks
- **SC-007**: Scheduled tasks execute within 1 minute of their scheduled time
- **SC-008**: System handles 50+ events per day across all watchers without performance degradation
- **SC-009**: 95% of MCP server actions succeed on first attempt (excluding external API failures)
- **SC-010**: Users can review and approve pending actions in under 30 seconds via CLI

## Constraints

### Technical Constraints

- Must build on Bronze Tier foundation (Obsidian vault, Gmail watcher, agent skills)
- Must use Python 3.11+ with uv package manager for all watcher scripts
- Must implement MCP server following Model Context Protocol specification
- Must use OAuth2 for all external API authentication (Gmail, LinkedIn, WhatsApp Business)
- Must store all credentials in OS keychain (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- Must use cron (Unix/Linux) or Task Scheduler (Windows) for scheduling
- Must implement all AI functionality as agent skills following .claude/skills/ pattern

### Business Constraints

- Estimated implementation time: 20-30 hours
- Must deliver functional assistant capabilities (Silver Tier scope)
- Must not include features beyond Silver Tier requirements (no Gold tier features like advanced analytics, mobile apps, or multi-user support)
- Must maintain backward compatibility with Bronze Tier vault structure

### Security Constraints

- All external actions (Level 2+) MUST require human approval before execution
- API credentials MUST be stored in OS keychain, never in code or config files
- Sensitive content (passwords, financial data) MUST be redacted in logs
- Rate limits MUST be enforced to prevent API abuse (Gmail: 100/day, LinkedIn: 100/day)
- Approval queue MUST auto-expire actions after 24 hours to prevent stale approvals
- MCP server MUST validate all inputs to prevent injection attacks

### Operational Constraints

- All watchers must be startable/stoppable via simple CLI commands
- System must work on Windows, macOS, and Linux
- System must recover gracefully from network failures and API outages
- Approval workflow must be accessible via CLI (no GUI required for MVP)
- Scheduled tasks must persist across system restarts
- All components must run on user's local machine (no server deployment required)

## Assumptions

- User has completed Bronze Tier implementation (Obsidian vault, Gmail watcher, agent skills)
- User has WhatsApp account and will use unofficial WhatsApp Web API (e.g., whatsapp-web.js) with understanding of ToS implications; migration path to official WhatsApp Business API documented for production use
- User has LinkedIn account and will use unofficial LinkedIn API (e.g., linkedin-api library) with understanding of ToS implications; migration path to official LinkedIn API documented for production use
- User will manually configure API credentials for WhatsApp and LinkedIn
- User will manually start watcher processes (no automatic startup on boot in Silver Tier)
- User will monitor approval queue at least once per day
- User will create initial content for LinkedIn posts in /Content_Queue
- Vault will contain fewer than 5000 notes (Silver Tier scale)
- User has basic familiarity with cron expressions or Task Scheduler
- User will manually review and approve all LinkedIn posts before publishing

## Out of Scope

The following are explicitly excluded from Silver Tier:

- Advanced analytics and reporting dashboards
- Mobile app or web interface for approval workflow
- Real-time notifications (push notifications, SMS alerts)
- Multi-user support or team collaboration features
- Automatic content generation for LinkedIn posts (automatic milestone detection and post generation without user request; AI-assisted drafting with explicit user invocation IS in scope via linkedin-draft skill)
- Integration with additional channels (Twitter, Facebook, Instagram, Slack)
- Advanced scheduling features (recurring patterns, dependencies, conditional execution)
- Backup and disaster recovery automation
- Performance optimization for large vaults (10,000+ notes)
- Custom MCP server plugins or extensions
- Integration with CRM systems (Salesforce, HubSpot)
- Financial transaction automation (deferred to Gold Tier)
- Advanced reasoning capabilities (multi-step planning, self-correction)
- Distributed deployment or cloud hosting
- API rate limit optimization or quota management
- A/B testing for LinkedIn post performance
