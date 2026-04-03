# Implementation Plan: Platinum Tier - Always-On Cloud + Local Executive

**Branch**: `001-platinum-tier` | **Date**: 2026-04-03 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-platinum-tier/spec.md`

## Summary

Platinum Tier extends Gold Tier's autonomous employee capabilities with a dual-agent architecture: a cloud agent running 24/7 for continuous monitoring and draft generation, and a local agent maintaining control over approvals and sensitive operations. The agents coordinate through a synchronized Obsidian vault using file-based handoffs with claim-by-move semantics to prevent duplicate work. Cloud-hosted Odoo provides 24/7 accounting, while comprehensive health monitoring ensures operational reliability. This architecture maintains privacy-first principles by keeping write credentials and sensitive data (WhatsApp sessions, banking) exclusively on the local machine.

**Key Innovation**: Work-zone specialization enables secure cloud operation without violating privacy principles - cloud agent has read-only monitoring credentials and generates drafts, while local agent retains all write credentials and approval authority.

## Technical Context

**Language/Version**: Python 3.11+ (existing watchers and MCP servers)  
**Primary Dependencies**: 
- Existing: `uv` (package manager), `mcp` (Model Context Protocol), `google-auth`, `requests`, `markdown`
- New: `gitpython` (vault sync), `systemd` (cloud agent daemon), `monit` (health monitoring)

**Storage**: 
- Obsidian vault (Markdown files) - synchronized between cloud and local via Git
- SQLite (audit logs, health metrics) - separate databases on cloud and local
- OS keychain (credentials) - local only for write credentials, cloud for read-only credentials

**Testing**: 
- `pytest` (unit tests for coordination logic, sync handlers, health checks)
- Integration tests (dual-agent scenarios, sync failure recovery, race condition handling)
- End-to-end tests (demo scenario: email arrives → cloud drafts → local approves → send)

**Target Platform**: 
- Local: Windows/macOS/Linux (existing)
- Cloud: Linux VM (Ubuntu 22.04 LTS recommended) on Oracle Cloud Free Tier, AWS, or equivalent

**Project Type**: Distributed system with dual agents (cloud + local)

**Performance Goals**: 
- Vault sync latency: <60 seconds (95th percentile)
- Draft generation: <5 minutes from event detection
- Health check cycle: 5 minutes
- Alert delivery: <2 minutes from failure detection

**Constraints**: 
- Cloud agent: Read-only API credentials only (no write access)
- Local agent: Exclusive access to WhatsApp sessions, banking credentials
- Vault sync: Markdown/state files only (no secrets, no binaries)
- Single-writer rule: Only local agent writes to Dashboard.md

**Scale/Scope**: 
- 2 agent instances (1 cloud, 1 local)
- 5 coordination directories (/Needs_Action/, /In_Progress/, /Pending_Approval/, /Done/, /Updates/)
- 4 work domains (email, social, accounting, banking)
- 30-day operational target without manual intervention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Local-First, Privacy-First (NON-NEGOTIABLE)
- **Status**: PASS
- **Rationale**: Cloud agent has read-only credentials only. Write credentials (email send, social post, banking, WhatsApp) remain exclusively on local machine. Vault sync excludes all credential files (.env, tokens, sessions). Sensitive data never leaves local environment except for necessary API calls executed by local agent.

### ✅ Autonomous Agent Pattern
- **Status**: PASS
- **Rationale**: Cloud agent runs 24/7 with watchers on 5-minute schedule. Local agent processes approvals autonomously when online. Both agents use Ralph Wiggum loop pattern for task completion. Human-in-the-loop only for approvals (Level 2+ actions).

### ✅ Separation of Concerns
- **Status**: PASS
- **Rationale**: Clear boundaries maintained:
  - Brain: Claude/Gemini (both agents use same LLM choice)
  - Memory: Obsidian vault (synchronized between agents)
  - Senses: Watchers (cloud monitors, local executes)
  - Hands: MCP servers (local agent only for write operations)

### ✅ Event-Driven Architecture
- **Status**: PASS
- **Rationale**: Cloud watchers emit events → cloud agent generates drafts → vault sync triggers local agent → local agent processes approvals. Failed events retryable with exponential backoff (existing circuit breaker pattern).

### ✅ Idempotency and Reliability
- **Status**: PASS
- **Rationale**: Atomic write pattern (write to .tmp, rename) ensures no partial writes. Logical timestamps handle clock skew. Claim-by-move prevents duplicate work. Extended sync failure triggers queue-and-halt to prevent data loss.

### ✅ Dual-Tier LLM Support
- **Status**: PASS
- **Rationale**: Both cloud and local agents use same LLM choice (Claude or Gemini) configured at setup. No changes to LLM architecture required.

### Additional Gates

#### ✅ No New Projects
- **Status**: PASS
- **Rationale**: Extends existing `watchers/` and `mcp-servers/` projects. No new top-level projects created.

#### ✅ Complexity Justification
- **Status**: PASS
- **Rationale**: Dual-agent architecture is necessary to achieve 24/7 operation while maintaining privacy-first principles. Alternative (single cloud agent with all credentials) violates constitution. Alternative (local-only agent) cannot provide 24/7 monitoring.

## Project Structure

### Documentation (this feature)

```text
specs/001-platinum-tier/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   ├── vault-sync.schema.json
│   ├── coordination.schema.json
│   ├── health-check.schema.json
│   └── agent-config.schema.json
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

**Existing Structure** (Gold Tier - DO NOT DUPLICATE):
```text
watchers/                          # Existing - Python 3.11+ watchers
├── gmail_watcher/                 # Email monitoring
├── whatsapp_watcher/              # WhatsApp (local only)
├── odoo_watcher/                  # Accounting transactions
├── social_media_watcher/          # Facebook, Instagram, Twitter
├── briefing_watcher/              # Weekly CEO briefing
├── shared/                        # Shared utilities
│   ├── base_watcher.py
│   ├── circuit_breaker.py
│   ├── ralph_loop.py
│   ├── audit_logger.py
│   ├── vault_writer.py
│   └── keychain.py
└── .env                           # Local credentials (NOT synced)

mcp-servers/digital-fte-server/    # Existing - MCP action server
├── server.py                      # Main MCP server
├── tools/                         # Action tools
│   ├── send_email.py
│   ├── whatsapp_send.py
│   ├── linkedin_post.py
│   ├── odoo_record_transaction.py
│   └── generate_briefing.py
├── approval/                      # Approval workflow
│   ├── queue.py
│   ├── classifier.py
│   └── executor.py
└── .env                           # Local credentials (NOT synced)

obsidian-vault/                    # Existing - Obsidian knowledge base
├── Dashboard.md                   # Main dashboard (local writes only)
├── Needs_Action/                  # Existing - task queue
├── Done/                          # Existing - completed tasks
├── Inbox/                         # Existing - incoming items
├── Approvals/                     # Existing - approval records
├── Audit_Logs/                    # Existing - action logs
├── Briefings/                     # Existing - weekly briefings
└── Accounting/                    # Existing - financial records

scripts/                           # Existing - setup and validation
├── setup_vault.py
├── verify_credentials.py
├── verify_constitution.py
└── daily_health_check.py
```

**New Structure** (Platinum Tier - TO BE CREATED):
```text
# Cloud deployment artifacts
cloud/                             # NEW - Cloud agent deployment
├── agent/                         # Cloud agent runtime
│   ├── cloud_agent.py             # Main cloud agent entry point
│   ├── config.py                  # Cloud-specific configuration
│   ├── credential_manager.py      # Read-only credential management
│   └── draft_generator.py         # Draft generation logic
├── watchers/                      # Cloud watcher configurations
│   ├── gmail_watcher_cloud.py     # Email monitoring (read-only)
│   ├── social_watcher_cloud.py    # Social media monitoring (read-only)
│   └── odoo_watcher_cloud.py      # Accounting monitoring (read-only)
├── health/                        # Health monitoring
│   ├── health_monitor.py          # Main health check orchestrator
│   ├── agent_health.py            # Agent responsiveness checks
│   ├── sync_health.py             # Vault sync status checks
│   ├── service_health.py          # Odoo/API connectivity checks
│   └── alerter.py                 # Alert delivery (email, SMS, push)
├── deployment/                    # Deployment scripts
│   ├── setup_cloud_vm.sh          # VM initialization script
│   ├── install_dependencies.sh    # Install Python, uv, Git/Syncthing
│   ├── configure_systemd.sh       # Setup systemd services
│   ├── setup_odoo.sh              # Deploy Odoo Community Edition
│   └── configure_ssl.sh           # Setup HTTPS for Odoo
├── .env.cloud.template            # Template for cloud credentials (read-only)
└── README.md                      # Cloud deployment guide

# Vault synchronization
sync/                              # NEW - Vault sync coordination
├── sync_manager.py                # Main sync orchestrator
├── git_sync.py                    # Git-based synchronization
├── syncthing_sync.py              # Syncthing-based synchronization
├── conflict_resolver.py           # Handle merge conflicts
├── atomic_writer.py               # Atomic write pattern (.tmp → rename)
├── sync_monitor.py                # Detect sync lag and failures
└── .gitignore.vault               # Vault sync exclusions (secrets, binaries)

# Agent coordination
coordination/                      # NEW - Dual-agent coordination
├── claim_manager.py               # Claim-by-move implementation
├── logical_clock.py               # Logical timestamps (sequence numbers)
├── work_queue.py                  # Work queue management
├── approval_processor.py          # Local agent approval workflow
├── dashboard_merger.py            # Merge /Updates/ into Dashboard.md
└── race_detector.py               # Detect and resolve race conditions

# Vault directory structure (NEW coordination directories)
obsidian-vault/
├── In_Progress/                   # NEW - Claimed tasks
│   ├── cloud/                     # Cloud agent's claimed tasks
│   └── local/                     # Local agent's claimed tasks
├── Pending_Approval/              # NEW - Drafts awaiting approval
│   ├── email/                     # Email reply drafts
│   ├── social/                    # Social media post drafts
│   └── accounting/                # Accounting entry drafts
└── Updates/                       # NEW - Cloud agent status updates

# Testing
tests/
├── platinum/                      # NEW - Platinum tier tests
│   ├── test_cloud_agent.py        # Cloud agent unit tests
│   ├── test_vault_sync.py         # Sync mechanism tests
│   ├── test_coordination.py       # Claim-by-move tests
│   ├── test_race_conditions.py    # Race condition handling
│   ├── test_health_monitoring.py  # Health check tests
│   ├── test_approval_workflow.py  # Approval processing tests
│   └── test_demo_scenario.py      # End-to-end demo test
└── integration/
    └── test_dual_agent.py         # Dual-agent integration tests
```

**Structure Decision**: Extends existing single-agent architecture with new `cloud/`, `sync/`, and `coordination/` directories. Existing `watchers/` and `mcp-servers/` remain unchanged but are used by both agents with different credential scopes. New coordination directories added to `obsidian-vault/` for dual-agent handoffs.

## Complexity Tracking

No constitution violations requiring justification. All complexity is necessary and justified:
- Dual-agent architecture: Required to achieve 24/7 operation while maintaining privacy-first principles
- Vault synchronization: Required for agent coordination without direct network communication
- Claim-by-move pattern: Simplest coordination mechanism that works with file-based sync
- Logical timestamps: Required to handle clock skew in distributed system

## Phase 0: Research & Technical Decisions

### Research Tasks

#### 1. Vault Synchronization Technology Choice
**Question**: Git vs Syncthing for vault synchronization?

**Research Areas**:
- Git: Conflict resolution mechanisms, merge strategies, performance with frequent small commits
- Syncthing: Conflict file handling, sync latency, resource usage, setup complexity
- Comparison: Latency, reliability, conflict detection, ease of deployment

**Decision Criteria**:
- Sync latency <60 seconds (95th percentile)
- Reliable conflict detection for race conditions
- Easy setup on both local and cloud
- Low resource overhead on cloud VM

#### 2. Health Monitoring Infrastructure
**Question**: Custom health monitoring vs existing tools (Prometheus, Grafana, Uptime Kuma)?

**Research Areas**:
- Custom: Python-based health checks, alert delivery via email/SMS/push
- Prometheus + Grafana: Metrics collection, visualization, alerting
- Uptime Kuma: Simple uptime monitoring, notification channels
- Comparison: Setup complexity, resource usage, alert delivery reliability

**Decision Criteria**:
- 5-minute health check cycle
- <2 minute alert delivery
- Support for email, SMS, push notifications
- Minimal resource overhead on cloud VM

#### 3. Cloud VM Systemd Service Configuration
**Question**: How to configure systemd for cloud agent auto-restart and logging?

**Research Areas**:
- Systemd service units for Python applications
- Restart policies (on-failure, always)
- Logging with journald
- Resource limits (memory, CPU)

**Decision Criteria**:
- Automatic restart on failure
- Logs accessible via journalctl
- Resource limits to prevent runaway processes

#### 4. Odoo Cloud Deployment
**Question**: Docker vs native installation for Odoo on cloud VM?

**Research Areas**:
- Docker: Official Odoo images, docker-compose setup, backup strategies
- Native: PostgreSQL + Odoo installation, systemd service, backup scripts
- Comparison: Resource usage, backup complexity, SSL configuration

**Decision Criteria**:
- Fits within 4GB RAM constraint (shared with agent)
- Daily automated backups with 30-day retention
- HTTPS with valid SSL certificate
- Easy restore process

#### 5. Logical Timestamp Implementation
**Question**: Vector clocks vs Lamport timestamps for operation ordering?

**Research Areas**:
- Lamport timestamps: Simple counter-based ordering
- Vector clocks: Causality tracking across agents
- Comparison: Complexity, storage overhead, ordering guarantees

**Decision Criteria**:
- Sufficient for claim-by-move ordering
- Minimal storage overhead
- Simple implementation

**Output**: `research.md` with decisions, rationales, and alternatives considered for each research area.

## Phase 1: Design & Contracts

### Data Model

**File**: `data-model.md`

**Entities**:

1. **Agent Configuration**
   - agent_id: string (cloud | local)
   - agent_type: enum (cloud | local)
   - llm_provider: enum (claude | gemini)
   - credential_scope: enum (read_only | full)
   - vault_path: string
   - sync_enabled: boolean
   - health_check_interval: integer (seconds)

2. **Work Queue Item**
   - item_id: string (UUID)
   - domain: enum (email | social | accounting | banking)
   - item_type: enum (draft | action_plan | approval_request)
   - status: enum (pending | claimed | in_progress | completed | failed)
   - created_at: logical_timestamp
   - claimed_by: string (agent_id) | null
   - claimed_at: logical_timestamp | null
   - content: markdown_file_path
   - metadata: json

3. **Draft Approval**
   - approval_id: string (UUID)
   - draft_type: enum (email_reply | social_post | accounting_entry)
   - draft_content: markdown_file_path
   - created_by: string (agent_id = cloud)
   - created_at: logical_timestamp
   - approval_status: enum (pending | approved | rejected | expired)
   - approved_by: string (user_id) | null
   - approved_at: logical_timestamp | null
   - executed_at: logical_timestamp | null

4. **Sync Status**
   - last_sync_at: timestamp
   - sync_lag_seconds: integer
   - sync_method: enum (git | syncthing)
   - conflict_count: integer
   - last_conflict_at: timestamp | null
   - sync_health: enum (healthy | degraded | failed)

5. **Health Check Result**
   - check_id: string (UUID)
   - check_type: enum (agent_responsiveness | vault_sync | api_connectivity | odoo_health)
   - checked_at: timestamp
   - status: enum (pass | fail)
   - latency_ms: integer | null
   - error_message: string | null
   - recovery_attempted: boolean
   - recovery_successful: boolean | null

6. **Logical Timestamp**
   - agent_id: string
   - sequence_number: integer
   - wall_clock_time: timestamp (for human readability only)

### API Contracts

**Directory**: `contracts/`

#### 1. Vault Sync Schema (`vault-sync.schema.json`)
```json
{
  "sync_event": {
    "event_id": "uuid",
    "event_type": "file_created | file_modified | file_deleted | conflict_detected",
    "file_path": "string",
    "agent_id": "cloud | local",
    "logical_timestamp": {
      "agent_id": "string",
      "sequence_number": "integer"
    },
    "conflict_resolution": "local_wins | cloud_wins | manual_required"
  }
}
```

#### 2. Coordination Schema (`coordination.schema.json`)
```json
{
  "claim_request": {
    "item_id": "uuid",
    "agent_id": "cloud | local",
    "logical_timestamp": {
      "agent_id": "string",
      "sequence_number": "integer"
    }
  },
  "claim_response": {
    "success": "boolean",
    "claimed_by": "string",
    "conflict_detected": "boolean"
  }
}
```

#### 3. Health Check Schema (`health-check.schema.json`)
```json
{
  "health_check": {
    "check_id": "uuid",
    "check_type": "agent_responsiveness | vault_sync | api_connectivity | odoo_health",
    "status": "pass | fail",
    "checked_at": "iso8601_timestamp",
    "latency_ms": "integer",
    "details": {
      "error_message": "string",
      "recovery_attempted": "boolean",
      "recovery_successful": "boolean"
    }
  },
  "alert": {
    "alert_id": "uuid",
    "severity": "critical | warning | info",
    "message": "string",
    "channels": ["email", "sms", "push"],
    "sent_at": "iso8601_timestamp"
  }
}
```

#### 4. Agent Config Schema (`agent-config.schema.json`)
```json
{
  "agent_config": {
    "agent_id": "cloud | local",
    "agent_type": "cloud | local",
    "llm_provider": "claude | gemini",
    "credential_scope": "read_only | full",
    "vault_path": "string",
    "sync_config": {
      "enabled": "boolean",
      "method": "git | syncthing",
      "remote_url": "string",
      "sync_interval_seconds": "integer"
    },
    "health_config": {
      "check_interval_seconds": "integer",
      "alert_channels": ["email", "sms", "push"],
      "alert_threshold_failures": "integer"
    }
  }
}
```

### Quickstart Guide

**File**: `quickstart.md`

**Sections**:
1. Prerequisites (Gold Tier complete, cloud VM access, Git/Syncthing installed)
2. Cloud VM Setup (provision VM, install dependencies, configure firewall)
3. Vault Synchronization Setup (Git remote or Syncthing peers)
4. Cloud Agent Deployment (copy code, configure credentials, start systemd service)
5. Odoo Cloud Deployment (install Odoo, configure HTTPS, setup backups)
6. Health Monitoring Setup (configure checks, test alerts)
7. Demo Scenario Walkthrough (trigger email, verify cloud draft, approve locally, verify send)
8. Troubleshooting (common issues, log locations, recovery procedures)

## Phase 2: Task Breakdown

**Note**: Task breakdown is performed by `/sp.tasks` command, not `/sp.plan`. This section is a placeholder.

Tasks will be generated from:
- User stories (6 stories with acceptance scenarios)
- Functional requirements (46 requirements across 7 categories)
- Research decisions (5 research areas)
- Design artifacts (data model, contracts, quickstart)

Expected task categories:
1. Vault synchronization implementation
2. Cloud agent deployment and configuration
3. Coordination mechanism (claim-by-move, logical timestamps)
4. Approval workflow (Dashboard.md integration)
5. Health monitoring and alerting
6. Odoo cloud deployment
7. Testing (unit, integration, end-to-end)
8. Documentation and deployment guides

## Implementation Phases

### Phase 0: Research (Current)
- [ ] Research vault sync technology (Git vs Syncthing)
- [ ] Research health monitoring infrastructure
- [ ] Research systemd service configuration
- [ ] Research Odoo cloud deployment
- [ ] Research logical timestamp implementation
- [ ] Document decisions in `research.md`

### Phase 1: Design (Next)
- [ ] Create `data-model.md` with 6 entities
- [ ] Create `contracts/` with 4 schema files
- [ ] Create `quickstart.md` with 8 sections
- [ ] Update agent context files

### Phase 2: Task Generation (After Phase 1)
- [ ] Run `/sp.tasks` to generate task breakdown
- [ ] Review and prioritize tasks
- [ ] Begin implementation

## Success Metrics

**Phase 0 Complete When**:
- All 5 research areas have documented decisions
- `research.md` exists with rationales and alternatives
- No unresolved technical questions remain

**Phase 1 Complete When**:
- `data-model.md` defines all 6 entities
- `contracts/` contains all 4 schema files
- `quickstart.md` provides complete deployment guide
- Agent context files updated

**Phase 2 Ready When**:
- Phase 0 and Phase 1 complete
- `/sp.tasks` command can be executed
- Implementation can begin immediately after task generation

## Risk Mitigation

**Risk**: Vault sync latency exceeds 60 seconds
- **Mitigation**: Research phase will benchmark both Git and Syncthing under realistic load

**Risk**: Race conditions cause duplicate work despite claim-by-move
- **Mitigation**: Comprehensive testing of race condition scenarios, fallback to manual resolution

**Risk**: Cloud VM resource constraints (4GB RAM shared between agent and Odoo)
- **Mitigation**: Research phase will validate resource usage, consider Odoo Docker with memory limits

**Risk**: Health monitoring false positives cause alert fatigue
- **Mitigation**: Tune alert thresholds during testing, implement alert aggregation

**Risk**: Extended sync failure causes data loss
- **Mitigation**: Queue-and-halt strategy (clarified in spec) prevents operations during sync failure

## Next Steps

1. **Execute Phase 0**: Launch research agents for 5 research areas
2. **Review research findings**: Validate decisions against success criteria
3. **Execute Phase 1**: Generate design artifacts (data-model, contracts, quickstart)
4. **Validate design**: Ensure all functional requirements covered
5. **Execute Phase 2**: Run `/sp.tasks` to generate implementation tasks
6. **Begin implementation**: Start with P1 user stories (cloud agent, work-zone specialization, vault sync)
