# Feature Specification: Platinum Tier - Always-On Cloud + Local Executive

**Feature Branch**: `001-platinum-tier`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "Platinum Tier: Always-On Cloud + Local Executive (Production-ish AI Employee) - All Gold requirements plus: Run the AI Employee on Cloud 24/7 (always-on watchers + orchestrator + health monitoring). Work-Zone Specialization (Cloud owns: Email triage + draft replies + social post drafts/scheduling; Local owns: approvals, WhatsApp session, payments/banking, final send/post actions). Delegation via Synced Vault with claim-by-move rule. Deploy Odoo Community on Cloud VM (24/7) with HTTPS, backups, and health monitoring. Optional A2A Upgrade (Phase 2)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cloud Agent 24/7 Operation (Priority: P1)

As a business owner, I need an AI agent running continuously in the cloud so that my business operations are monitored and managed even when my local machine is offline or I'm away from my desk.

**Why this priority**: This is the foundational capability that differentiates Platinum from Gold. Without 24/7 cloud operation, all other Platinum features are impossible. This enables true "always-on" business management.

**Independent Test**: Can be fully tested by deploying the cloud agent, shutting down the local machine, triggering events (send test emails), and verifying the cloud agent processes them. Delivers immediate value by enabling business continuity.

**Acceptance Scenarios**:

1. **Given** the cloud agent is deployed and running, **When** the local machine is offline, **Then** the cloud agent continues monitoring email, social media, and other integrations without interruption
2. **Given** the cloud agent detects a new event (email, transaction), **When** processing the event, **Then** the agent creates appropriate draft responses or action plans in the synced vault
3. **Given** the cloud agent encounters an error, **When** the error occurs, **Then** health monitoring detects the issue and alerts the user via configured notification channels

---

### User Story 2 - Work-Zone Specialization and Delegation (Priority: P1)

As a business owner, I need the cloud agent to handle draft work (email triage, reply drafts, social post drafts) while my local agent retains control over approvals and final execution so that I maintain security and control over sensitive operations while benefiting from 24/7 automation.

**Why this priority**: This is the core architectural pattern that enables secure cloud operation. Without proper work-zone separation, sensitive credentials would need to be in the cloud, violating privacy-first principles.

**Independent Test**: Can be tested by triggering an email while local is offline, verifying cloud creates draft, then bringing local online and verifying local handles approval and sending. Delivers the demo requirement and proves the architecture works.

**Acceptance Scenarios**:

1. **Given** a new email arrives while local agent is offline, **When** the cloud agent processes it, **Then** the cloud agent creates a draft reply and writes it to /Pending_Approval/email/ in the synced vault
2. **Given** a draft reply exists in /Pending_Approval/email/, **When** the local agent comes online and user approves, **Then** the local agent executes the send action via MCP, logs the action, and moves the task to /Done/
3. **Given** the cloud agent needs to schedule a social media post, **When** creating the draft, **Then** the cloud agent writes the draft to /Pending_Approval/social/ and waits for local agent approval before any posting occurs
4. **Given** a banking or payment action is required, **When** the cloud agent detects this need, **Then** the cloud agent creates an action plan in /Needs_Action/banking/ without attempting to access banking credentials or execute the action

---

### User Story 3 - Vault Synchronization and Coordination (Priority: P1)

As a business owner using both cloud and local agents, I need the agents to coordinate their work through a synchronized vault so that they can collaborate effectively without conflicts or duplicate work.

**Why this priority**: Without reliable synchronization and coordination, the two agents would work at cross-purposes, creating duplicate actions or losing work. This is essential infrastructure for the dual-agent architecture.

**Independent Test**: Can be tested by creating tasks in cloud agent, verifying they sync to local, having local claim a task, and verifying cloud respects the claim. Delivers coordination that prevents wasted work.

**Acceptance Scenarios**:

1. **Given** the cloud agent writes a file to /Needs_Action/email/, **When** the vault synchronizes, **Then** the local agent sees the file within 60 seconds and can process it
2. **Given** multiple tasks exist in /Needs_Action/, **When** an agent claims a task by moving it to /In_Progress/<agent-name>/, **Then** the other agent detects the claim and does not attempt to work on that task
3. **Given** the cloud agent writes updates to /Updates/, **When** the local agent processes these updates, **Then** the local agent merges them into Dashboard.md without conflicts
4. **Given** vault synchronization fails or is delayed, **When** the delay exceeds 5 minutes, **Then** both agents detect the sync issue and alert the user

---

### User Story 4 - Cloud-Hosted Odoo Accounting (Priority: P2)

As a business owner, I need my accounting system (Odoo) running 24/7 in the cloud so that business transactions are recorded in real-time regardless of whether my local machine is running.

**Why this priority**: Cloud-hosted Odoo enables the cloud agent to perform accounting operations continuously. This is high value but depends on the foundational cloud infrastructure being operational first.

**Independent Test**: Can be tested by deploying Odoo to cloud, configuring HTTPS access, creating test transactions via cloud agent, and verifying they're recorded correctly. Delivers 24/7 accounting automation.

**Acceptance Scenarios**:

1. **Given** Odoo is deployed on the cloud VM, **When** the cloud agent detects a business transaction, **Then** the agent creates a draft accounting entry in /Pending_Approval/accounting/ for local agent review
2. **Given** the local agent approves an accounting entry, **When** the approval is processed, **Then** the entry is posted to Odoo via MCP and logged in the audit trail
3. **Given** Odoo is running on the cloud VM, **When** daily backups are scheduled, **Then** backups are created automatically and stored securely with 30-day retention
4. **Given** Odoo becomes unavailable, **When** health monitoring detects the failure, **Then** the system alerts the user and queues accounting operations for later execution

---

### User Story 5 - Health Monitoring and Alerting (Priority: P2)

As a business owner relying on cloud infrastructure, I need comprehensive health monitoring of all cloud services so that I'm immediately notified of any issues and can take corrective action before business operations are impacted.

**Why this priority**: Production systems require monitoring. Without it, silent failures could go undetected for hours or days, causing business disruption.

**Independent Test**: Can be tested by simulating various failure scenarios (agent crash, Odoo down, sync failure) and verifying alerts are sent promptly. Delivers operational confidence.

**Acceptance Scenarios**:

1. **Given** the cloud agent is running, **When** health checks run every 5 minutes, **Then** the system verifies agent responsiveness, vault sync status, and external API connectivity
2. **Given** a health check fails, **When** the failure is detected, **Then** the system sends an alert via configured channels (email, SMS, push notification) within 2 minutes
3. **Given** Odoo or other cloud services become unresponsive, **When** health monitoring detects the issue, **Then** the system attempts automatic recovery (restart service) and alerts the user if recovery fails
4. **Given** vault synchronization is delayed or failing, **When** the sync lag exceeds 5 minutes, **Then** both agents pause non-critical operations and alert the user

---

### User Story 6 - Agent-to-Agent Messaging (Phase 2) (Priority: P3)

As a business owner with mature cloud infrastructure, I need agents to communicate directly via structured messages so that coordination is faster and more efficient than file-based handoffs.

**Why this priority**: This is an optimization of the file-based coordination. It's valuable for performance but not essential for MVP. Phase 2 upgrade after the core system is stable.

**Independent Test**: Can be tested by implementing A2A messaging for one workflow (e.g., email drafting), measuring latency improvement, and verifying vault still maintains audit records. Delivers performance optimization.

**Acceptance Scenarios**:

1. **Given** A2A messaging is enabled, **When** the cloud agent completes a draft, **Then** the agent sends a direct message to the local agent with the draft content and approval request
2. **Given** the local agent receives an A2A message, **When** processing the message, **Then** the agent still writes the approval decision to the vault for audit trail purposes
3. **Given** A2A messaging fails or times out, **When** the failure is detected, **Then** the system falls back to file-based coordination automatically

---

### Edge Cases

- What happens when vault synchronization fails for an extended period (hours)?
- How does the system handle clock skew between cloud and local agents?
- What happens if both agents attempt to claim the same task simultaneously?
- How does the system handle partial file writes during synchronization?
- What happens when the cloud VM runs out of disk space?
- How does the system handle network partitions between cloud and local?
- What happens if Odoo database becomes corrupted?
- How does the system handle cloud provider outages?
- What happens when local agent is offline for days and returns with stale state?
- How does the system handle conflicting updates to Dashboard.md?
- What happens when cloud agent credentials expire?
- How does the system handle timezone differences between cloud VM and local machine?

## Requirements *(mandatory)*

### Functional Requirements

#### Cloud Agent Deployment and Operation

- **FR-001**: System MUST support deploying the AI agent to a cloud VM (Oracle Cloud Free Tier, AWS, or equivalent)
- **FR-002**: Cloud agent MUST run continuously (24/7) with automatic restart on failure
- **FR-003**: Cloud agent MUST run all watchers (email, social media monitoring) on the same schedule as local agent (every 5 minutes)
- **FR-004**: Cloud agent MUST have access to read-only API credentials for monitoring services (Gmail, social media)
- **FR-005**: Cloud agent MUST NOT have access to write credentials (email send, social post, banking, WhatsApp)
- **FR-006**: Cloud agent MUST operate with the same LLM choice (Claude or Gemini) as configured for local agent

#### Work-Zone Specialization

- **FR-007**: Cloud agent MUST handle email triage, draft reply generation, and social post draft creation
- **FR-008**: Local agent MUST handle all approval workflows, final execution of sends/posts, banking operations, and WhatsApp interactions
- **FR-009**: Cloud agent MUST write all draft work to /Pending_Approval/<domain>/ directories in the synced vault
- **FR-010**: Local agent MUST monitor /Pending_Approval/ directories and present drafts to user for approval via Dashboard.md with a pending approvals section where user can review and mark items as approved
- **FR-011**: Cloud agent MUST write action plans (not drafts) to /Needs_Action/<domain>/ for tasks requiring local execution
- **FR-012**: Cloud agent MUST write status updates to /Updates/ directory for local agent to merge into Dashboard.md
- **FR-013**: Local agent MUST maintain exclusive write access to Dashboard.md (single-writer rule)

#### Vault Synchronization

- **FR-014**: System MUST support vault synchronization using Git
- **FR-015**: Vault sync MUST complete within 60 seconds under normal conditions
- **FR-016**: Vault sync MUST include only markdown files and state files (no secrets, no binary credentials)
- **FR-017**: System MUST detect sync failures and alert user when sync lag exceeds 5 minutes; if sync remains broken for extended periods (1+ hours), agents MUST queue operations locally and halt cross-agent coordination
- **FR-018**: System MUST handle merge conflicts in vault files gracefully (prefer local agent's version for Dashboard.md, use logical timestamps for other files to determine first-write-wins)
- **FR-019**: Vault sync MUST preserve file timestamps and modification history
- **FR-019a**: Agents MUST use atomic write pattern (write to .tmp files first, then atomically rename to final name) to prevent partial file writes during synchronization

#### Coordination and Claim-by-Move

- **FR-020**: System MUST implement claim-by-move rule: first agent to move a file from /Needs_Action/ to /In_Progress/<agent-name>/ owns the task
- **FR-021**: Agents MUST check /In_Progress/ directories before claiming tasks from /Needs_Action/
- **FR-022**: Agents MUST move completed tasks from /In_Progress/<agent-name>/ to /Done/ with completion timestamp using logical timestamps (sequence numbers) for ordering to handle clock skew between cloud and local agents
- **FR-023**: System MUST detect and resolve race conditions when both agents attempt to claim the same task using file system atomic operations combined with the sync tool's conflict resolution (Git merge conflicts or Syncthing conflict files); resolution uses first-write-wins based on logical timestamps
- **FR-024**: Agents MUST respect claimed tasks and not attempt to work on tasks in another agent's /In_Progress/ directory

#### Cloud-Hosted Odoo

- **FR-025**: System MUST support deploying Odoo Community Edition to the same cloud VM as the agent
- **FR-026**: Odoo MUST be accessible via HTTPS with valid SSL certificate
- **FR-027**: Odoo MUST have automated daily backups with 30-day retention
- **FR-028**: Cloud agent MUST integrate with Odoo via MCP for draft-only accounting actions
- **FR-029**: Local agent MUST handle final approval and posting of accounting entries to Odoo
- **FR-030**: System MUST monitor Odoo health and alert on failures

#### Health Monitoring

- **FR-031**: System MUST run health checks every 5 minutes on cloud agent, Odoo, and vault sync status
- **FR-032**: Health checks MUST verify agent responsiveness, service availability, and API connectivity
- **FR-033**: System MUST send alerts within 2 minutes of detecting health check failures
- **FR-034**: System MUST support multiple alert channels (email, SMS, push notification)
- **FR-035**: System MUST attempt automatic recovery (service restart) before alerting user
- **FR-036**: System MUST log all health check results and recovery attempts

#### Security and Secrets Management

- **FR-037**: Cloud agent MUST NOT store or access write-level API credentials (email send, social post, banking)
- **FR-038**: Cloud agent MUST use read-only API credentials stored in cloud VM's secure storage
- **FR-039**: Local agent MUST maintain exclusive access to WhatsApp session files
- **FR-040**: Vault synchronization MUST exclude .env files, credential files, and WhatsApp session data
- **FR-041**: Cloud VM MUST use encrypted storage for all sensitive data
- **FR-042**: System MUST rotate cloud API credentials every 90 days

#### Agent-to-Agent Messaging (Phase 2)

- **FR-043**: System MUST support optional A2A messaging protocol for direct agent communication
- **FR-044**: A2A messages MUST still result in vault file writes for audit trail purposes
- **FR-045**: System MUST fall back to file-based coordination if A2A messaging fails
- **FR-046**: A2A messages MUST include message ID, sender, recipient, timestamp, and payload

### Key Entities

- **Cloud Agent**: AI agent instance running 24/7 on cloud VM with read-only monitoring credentials and draft-generation capabilities
- **Local Agent**: AI agent instance running on user's local machine with full credentials and approval/execution authority
- **Synced Vault**: Obsidian vault synchronized between cloud and local containing work queues, drafts, approvals, and audit logs
- **Work Queue Directory**: Structured directories for agent coordination (/Needs_Action/, /In_Progress/, /Pending_Approval/, /Done/, /Updates/)
- **Task Claim**: File movement from /Needs_Action/ to /In_Progress/<agent>/ indicating ownership
- **Draft Approval**: User decision on cloud-generated drafts stored in /Pending_Approval/
- **Health Check Result**: Status report from monitoring system indicating service health
- **Cloud VM**: Virtual machine hosting cloud agent, Odoo, and supporting services
- **A2A Message**: Direct message between agents with structured payload (Phase 2)

## Clarifications

### Session 2026-04-03

- Q: How should the system technically detect and enforce "first write wins" when both agents try to move the same file from /Needs_Action/ to their respective /In_Progress/ directories at nearly the same time? → A: Use file system atomic operations with the sync tool's conflict resolution - leverage Git merge conflicts or Syncthing conflict files to detect races
- Q: After alerting the user about sync failure, what should the agents do if synchronization remains broken for an extended period (e.g., 1+ hours)? → A: Queue operations locally and halt cross-agent coordination - both agents continue local work but don't create new cross-agent tasks
- Q: How should the local agent present pending approvals to the user when it comes online? → A: Dashboard notification with approval queue - agent updates Dashboard.md with pending approvals section, user reviews and marks approved
- Q: How should the system handle time-based operations when cloud and local agents have different system clocks? → A: Use logical timestamps (sequence numbers) for ordering - agents use incrementing counters instead of wall-clock time for operation ordering
- Q: How should agents detect and handle files that were only partially written during synchronization? → A: Use atomic write pattern (write to temp, then rename) - agents write to .tmp files first, then atomically rename to final name

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cloud agent maintains 99.5% uptime over 30-day period
- **SC-002**: Email drafts are created by cloud agent within 5 minutes of email arrival, even when local is offline
- **SC-003**: Vault synchronization completes within 60 seconds in 95% of cases
- **SC-004**: Zero task conflicts or duplicate work due to claim-by-move coordination
- **SC-005**: Local agent processes pending approvals within 2 minutes of coming online
- **SC-006**: Odoo maintains 99% uptime with successful daily backups
- **SC-007**: Health monitoring detects failures within 5 minutes and alerts within 2 minutes
- **SC-008**: Cloud agent operates for 30 days without requiring manual intervention
- **SC-009**: User can be away from local machine for 7 days while cloud agent continues business monitoring
- **SC-010**: Demo scenario (email arrives while local offline → cloud drafts → local approves → send) completes successfully in under 5 minutes from local coming online

### User Satisfaction Metrics

- **SC-011**: Users report confidence in cloud agent's draft quality (measured via approval rate ≥80% for cloud-generated drafts)
- **SC-012**: Users feel secure with work-zone separation (measured via security audit showing zero credential leaks to cloud)
- **SC-013**: Users find health monitoring alerts actionable and timely (measured by alert response time <30 minutes and false positive rate <5%)

## Assumptions

- Gold Tier (autonomous employee with Odoo, social media, CEO briefing) is fully functional
- User has access to a cloud VM (Oracle Cloud Free Tier, AWS, or equivalent) with sufficient resources (2 CPU, 4GB RAM minimum)
- User has Git or Syncthing configured for vault synchronization
- User's local machine comes online at least once per day for approval workflows
- Cloud VM has reliable internet connectivity with <100ms latency to major APIs
- User has separate read-only and write API credentials for external services
- Odoo Community Edition can be deployed on the same VM as the agent without resource conflicts
- User is comfortable with basic cloud infrastructure management (SSH, service monitoring)

## Dependencies

- Gold Tier implementation (autonomous employee, Odoo integration, social media, CEO briefing)
- Cloud VM provisioning and access credentials
- Git or Syncthing installation and configuration
- SSL certificate for Odoo HTTPS access
- Health monitoring infrastructure (monitoring service or custom implementation)
- Separate read-only API credentials for cloud agent

## Out of Scope

- Multi-region cloud deployment (single region only)
- High-availability clustering (single VM deployment)
- Real-time A2A messaging in Phase 1 (file-based coordination only)
- Automatic cloud VM provisioning (manual setup required)
- Cloud cost optimization and auto-scaling
- Disaster recovery across cloud providers
- Mobile app for approvals (desktop/CLI only)
- Voice-based approval workflows
- Blockchain-based audit trails
- Multi-tenant cloud deployment

## Security & Privacy Considerations

- Cloud agent has read-only access to monitoring APIs only (no write credentials)
- WhatsApp session files never leave local machine
- Banking credentials never stored in cloud
- Vault sync excludes all credential files (.env, tokens, sessions)
- Cloud VM uses encrypted storage (AES-256)
- All communication between cloud and local uses encrypted channels
- Odoo database encrypted at rest
- Health monitoring alerts do not include sensitive data
- Cloud agent logs redact any accidentally captured credentials
- User maintains ability to revoke cloud agent access at any time
- Audit trail shows which agent performed each action

## Compliance Requirements

- Cloud deployment complies with data residency requirements (user chooses region)
- Vault synchronization maintains audit trail integrity
- Health monitoring logs retained for 90 days for incident investigation
- Odoo backups encrypted and stored securely
- System supports data export for regulatory compliance
- Agent actions attributable to specific agent (cloud vs local) in audit logs
