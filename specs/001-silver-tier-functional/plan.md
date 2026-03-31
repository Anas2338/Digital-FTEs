# Implementation Plan: Silver Tier Functional Assistant

**Branch**: `001-silver-tier-functional` | **Date**: 2026-03-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-silver-tier-functional/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a functional AI assistant that monitors multiple communication channels (Gmail, WhatsApp, LinkedIn), executes external actions via MCP server with human-in-the-loop approval, automatically generates execution plans for complex tasks, and schedules recurring automation. All functionality implemented as agent skills following the constitution's Brain-Memory-Senses-Hands architecture pattern.

## Technical Context

**Language/Version**: Python 3.11+ (watchers and MCP server), Node.js 18+ (whatsapp-web.js dependency)
**Primary Dependencies**:
- Python: uv (package manager), whatsapp-web.js (via subprocess), linkedin-api, google-auth (Gmail OAuth2), pydantic (validation), fastapi (MCP server), schedule (task scheduling)
- Node.js: whatsapp-web.js, puppeteer (LinkedIn automation fallback)
**Storage**: Obsidian vault (Markdown files with YAML frontmatter), SQLite (watcher logs, action audit trail)
**Testing**: pytest (unit/integration), pytest-asyncio (async tests), pytest-mock (API mocking)
**Target Platform**: Windows 10+, macOS 12+, Linux (Ubuntu 20.04+) - cross-platform CLI tools
**Project Type**: Multi-component distributed system (3 independent watchers + 1 MCP server + 6 agent skills)
**Performance Goals**:
- Watcher polling: 3 min (Gmail), 5 min (WhatsApp/LinkedIn)
- MCP server response: <2s (excluding external API latency)
- Uptime: 7 days continuous operation without crashes
- Throughput: 50+ events/day across all watchers
**Constraints**:
- Rate limits: Gmail 100/day, LinkedIn 100/day, WhatsApp 1000/day
- Implementation time: 20-30 hours
- Approval latency: 24-hour auto-expire for pending actions
- Character limits: LinkedIn 3000 chars
**Scale/Scope**:
- Vault size: <5000 notes
- Concurrent watchers: 3 independent processes
- Agent skills: 6 new skills (watcher-status, mcp-invoke, approval-review, linkedin-draft, reasoning-plan, schedule-task)
- Scheduled tasks: Support for cron expressions and Task Scheduler XML

## Constitution Check (Post-Design Re-evaluation)

*Re-evaluated after Phase 1 design completion*

### Core Principles Compliance

**I. Local-First, Privacy-First** ✅ PASS
- **Design Validation**:
  - All watcher data flows to Obsidian vault (data-model.md: Event → Vault Note)
  - SQLite used only for queryable logs (non-sensitive metadata)
  - API credentials abstracted via OS keychain (quickstart.md: setup instructions)
  - No cloud storage dependencies in architecture
- **Evidence**: data-model.md Entity Relationships, quickstart.md Security Checklist

**II. Autonomous Agent Pattern** ✅ PASS
- **Design Validation**:
  - Watchers run as independent daemon processes (quickstart.md: Start Watchers section)
  - Approval workflow implements HITL for Level 2+ actions (data-model.md: Action entity state transitions)
  - Reasoning loop validates task completion (data-model.md: Plan entity with success criteria validation)
  - Agent skills provide all AI functionality (6 skills defined in project structure)
- **Evidence**: data-model.md Action state machine, contracts/mcp-server.json tool definitions

**III. Separation of Concerns** ✅ PASS
- **Design Validation**:
  - Brain: 6 agent skills in .claude/skills/ (watcher-status, mcp-invoke, approval-review, linkedin-draft, reasoning-plan, schedule-task)
  - Memory: Obsidian vault with 9 folders (data-model.md: Storage Strategy)
  - Senses: 3 independent watcher processes (contracts/watcher-events.json: event schemas)
  - Hands: MCP server with 3 tools (contracts/mcp-server.json: OpenAPI spec)
- **Evidence**: Project Structure section, contracts/ directory

**IV. Event-Driven Architecture** ✅ PASS
- **Design Validation**:
  - Watchers emit structured events (contracts/watcher-events.json: GmailEvent, WhatsAppEvent, LinkedInEvent)
  - Events create vault notes asynchronously (data-model.md: Event processing_status state machine)
  - Retry logic with exponential backoff (data-model.md: Schedule entity retry_count 0-3)
  - Graceful degradation via independent watcher processes (quickstart.md: health checks)
- **Evidence**: contracts/watcher-events.json, data-model.md Event entity

**V. Idempotency and Reliability** ✅ PASS
- **Design Validation**:
  - Actions have unique IDs and audit trails (data-model.md: Action entity with audit_trail array)
  - State transitions are atomic (data-model.md: all entities have explicit state machines)
  - Approval queue prevents duplicate execution (data-model.md: Action status prevents re-execution)
  - Missed schedules handled on startup (data-model.md: Schedule entity with last_run_timestamp)
- **Evidence**: data-model.md Action entity, Schedule entity

**VI. Dual-Tier LLM Support** ✅ PASS (with documentation)
- **Design Validation**:
  - Agent skills use MCP protocol (LLM-agnostic) (contracts/mcp-server.json)
  - Research documented Gemini compatibility path (research.md: Topic 1)
  - MCP adapter layer handles protocol translation (research.md: no skill-specific changes needed)
  - Test plan includes both Claude and Gemini execution paths (research.md: Implementation Notes)
- **Evidence**: research.md Topic 1, contracts/mcp-server.json

### Technology Stack Compliance

✅ **PASS** - All requirements validated in design:
- Python 3.11+ with uv: Confirmed in quickstart.md dependencies
- Obsidian vault: Confirmed in data-model.md storage strategy
- MCP server: Confirmed in contracts/mcp-server.json OpenAPI spec
- OAuth2/unofficial APIs: Confirmed in research.md Topics 2-3
- OS keychain: Confirmed in quickstart.md setup steps
- Agent skills: Confirmed in project structure (6 skills)

### Security & Privacy Compliance

✅ **PASS** - All requirements validated in design:
- Action safety levels: Confirmed in data-model.md Action entity (safety_level 0-3)
- OS keychain storage: Confirmed in quickstart.md configure_apis.py
- Rate limiting: Confirmed in contracts/mcp-server.json RateLimitError schema
- Audit trail: Confirmed in data-model.md Action entity (audit_trail field)
- Input validation: Confirmed in contracts/mcp-server.json parameter schemas
- PII redaction: Confirmed in quickstart.md Security Checklist

### Code Quality Compliance

✅ **PASS** - Test strategy documented:
- 80%+ coverage plan: Confirmed in research.md Topic 7
- Test pyramid defined: Unit (70%), Contract (20%), Integration (10%)
- Mocking strategy: Confirmed for all external APIs
- CI/CD integration: Confirmed with pytest coverage reporting
- **Evidence**: research.md Topic 7 "Test Strategy for 80%+ Coverage"

### Final Gate Decision

**STATUS**: ✅ **PASS - READY FOR IMPLEMENTATION**

All constitution principles satisfied by design. No violations or concerns identified. Architecture aligns with Brain-Memory-Senses-Hands pattern. Security and privacy requirements fully addressed. Test strategy meets 80%+ coverage requirement.

**Proceed to Phase 2**: Run `/sp.tasks` to generate implementation task list.

## Project Structure

### Documentation (this feature)

```text
specs/001-silver-tier-functional/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── mcp-server.json  # MCP server tool definitions (OpenAPI-style)
│   └── watcher-events.json  # Event schemas for watcher outputs
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
watchers/
├── gmail_watcher/       # Existing Bronze Tier watcher
│   ├── __init__.py
│   ├── watcher.py
│   └── config.py
├── whatsapp_watcher/    # NEW: WhatsApp monitoring
│   ├── __init__.py
│   ├── watcher.py       # Python wrapper for whatsapp-web.js
│   ├── bridge.js        # Node.js bridge to whatsapp-web.js
│   └── config.py
├── linkedin_watcher/    # NEW: LinkedIn monitoring
│   ├── __init__.py
│   ├── watcher.py       # Uses linkedin-api library
│   └── config.py
├── shared/              # NEW: Shared watcher utilities
│   ├── __init__.py
│   ├── event_logger.py  # Centralized logging (FR-006)
│   ├── health_check.py  # Health monitoring (FR-005)
│   └── vault_writer.py  # Obsidian note creation
└── pyproject.toml       # uv package configuration

mcp-servers/
├── digital-fte-server/  # NEW: Main MCP server
│   ├── __init__.py
│   ├── server.py        # FastAPI MCP server
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── send_email.py    # Gmail API integration
│   │   ├── linkedin_post.py # LinkedIn API integration
│   │   └── whatsapp_send.py # WhatsApp API integration
│   ├── approval/
│   │   ├── __init__.py
│   │   ├── queue.py         # Approval queue management (FR-013)
│   │   ├── classifier.py    # Action safety level classifier (FR-012)
│   │   └── executor.py      # Action execution after approval (FR-016)
│   ├── rate_limiter.py      # Rate limiting (FR-011)
│   └── validator.py         # Input validation (FR-008)
└── pyproject.toml

.claude/skills/
├── watcher-status/      # NEW: Monitor watcher health
│   └── SKILL.md
├── mcp-invoke/          # NEW: Invoke MCP server tools
│   └── SKILL.md
├── approval-review/     # NEW: Review pending approvals
│   └── SKILL.md
├── linkedin-draft/      # NEW: Draft LinkedIn posts
│   └── SKILL.md
├── reasoning-plan/      # NEW: Generate Plan.md files
│   └── SKILL.md
└── schedule-task/       # NEW: Schedule recurring tasks
    └── SKILL.md

obsidian-vault/
├── Inbox/               # Existing Bronze Tier
├── Needs_Action/        # Existing Bronze Tier
├── Done/                # Existing Bronze Tier
├── Approvals/           # NEW: Pending action approvals (FR-013)
├── Rejected/            # NEW: Rejected actions (FR-017)
├── Expired/             # NEW: Auto-expired approvals (FR-018)
├── Content_Queue/       # NEW: Scheduled LinkedIn posts (FR-019)
├── Schedules/           # NEW: Recurring task definitions (FR-032)
├── Reports/             # NEW: Generated reports (User Story 6)
└── Dashboard.md         # Existing Bronze Tier

scripts/
├── scheduler/           # NEW: Task scheduling infrastructure
│   ├── __init__.py
│   ├── cron_manager.py      # Unix/Linux cron integration (FR-031)
│   ├── taskscheduler_manager.py  # Windows Task Scheduler (FR-031)
│   └── task_executor.py     # Task execution with retry logic (FR-033)
└── setup/
    ├── install_watchers.py  # Watcher installation script
    └── configure_apis.py    # API credential setup

tests/
├── watchers/
│   ├── test_whatsapp_watcher.py
│   ├── test_linkedin_watcher.py
│   └── test_shared_utilities.py
├── mcp_server/
│   ├── test_tools.py
│   ├── test_approval_workflow.py
│   └── test_rate_limiter.py
├── agent_skills/
│   ├── test_watcher_status.py
│   ├── test_approval_review.py
│   └── test_reasoning_plan.py
├── integration/
│   ├── test_end_to_end_email.py
│   ├── test_end_to_end_linkedin.py
│   └── test_approval_flow.py
└── fixtures/
    ├── mock_apis.py
    └── sample_events.json
```

**Structure Decision**: Multi-component distributed system following constitution's Brain-Memory-Senses-Hands architecture. Watchers (Senses) are independent Python processes, MCP server (Hands) is a FastAPI service, Agent Skills (Brain) extend Claude Code, and Obsidian vault (Memory) provides persistent storage. This structure enables independent testing, deployment, and scaling of each component while maintaining clear separation of concerns.

## Complexity Tracking

**No violations requiring justification.** All constitution principles are satisfied by the proposed architecture. The multi-component structure (3 watchers + 1 MCP server + 6 agent skills) is necessary to meet the functional requirements and aligns with the constitution's Separation of Concerns principle (Brain-Memory-Senses-Hands architecture).
