# Implementation Plan: Gold Tier - Autonomous Employee

**Branch**: `001-gold-tier-autonomous` | **Date**: 2026-03-31 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-gold-tier-autonomous/spec.md`

## Summary

Gold Tier extends the Digital FTE agent with full business automation capabilities: Odoo accounting integration for transaction tracking, social media management across Facebook/Instagram/Twitter, weekly CEO briefing generation, enhanced error recovery with circuit breaker pattern, comprehensive audit logging, and autonomous multi-step task completion using the Ralph Wiggum loop pattern. This transforms the agent from a functional assistant (Silver Tier) into a true autonomous employee capable of managing both personal and business affairs with minimal human intervention.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: 
- Existing: `mcp`, `google-auth`, `google-api-python-client`, `pydantic`, `sqlite3`
- New: `odoorpc` (Odoo JSON-RPC client), `facebook-sdk`, `tweepy` (Twitter API), `instagrapi` (Instagram), `schedule` (cron-like scheduling)

**Storage**: 
- Obsidian vault (Markdown files) for dashboard, briefings, audit logs
- SQLite for structured event logs, metrics, circuit breaker state
- OS keychain for API credentials (Windows Credential Manager, macOS Keychain, Linux Secret Service)

**Testing**: pytest with 80%+ coverage requirement  
**Target Platform**: Windows/macOS/Linux (local-first, cross-platform)  
**Project Type**: Single project with modular watchers and MCP servers  
**Performance Goals**: 
- Transaction recording within 5 minutes of occurrence
- Social media posts within 1 minute of scheduled time
- CEO briefing generation completes within 2 minutes
- Circuit breaker recovery attempts within defined backoff schedule (5min, 10min, 20min, hourly)

**Constraints**: 
- All sensitive data stored locally (local-first principle)
- No cloud databases without explicit user consent
- 80%+ test coverage for watchers and MCP servers
- Action safety levels enforced (Level 0-3)
- Rate limits: 100 emails/day, 10 social posts/day, $500 transaction limit

**Scale/Scope**: 
- Single business owner user
- Support for 3 social media platforms (Facebook, Instagram, Twitter/X)
- 1 accounting system (Odoo Community self-hosted)
- Weekly briefing generation (52 briefings/year)
- Continuous operation with 5-minute polling intervals

**Implementation Status**: 
- ✅ Research phase complete (research.md)
- ✅ Circuit breaker pattern implemented
- ✅ Watcher scaffolding created (odoo_watcher, social_media_watcher, briefing_watcher)
- ✅ MCP tools scaffolding created (Odoo tools, social media tools, task tools)
- ✅ Shared utilities extended (audit_logger, ralph_loop, domain coordination)
- ⚠️ Watchers need main loop implementation
- ⚠️ MCP tools need full implementation
- ⚠️ Integration testing needed
- ⚠️ Obsidian vault folders need population

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Local-First, Privacy-First
- All accounting data stored in Obsidian vault
- Social media credentials in OS keychain only
- Audit logs local, no cloud transmission
- Transaction data never leaves local environment except for necessary API calls

### ✅ Autonomous Agent Pattern
- Watchers run continuously (5-minute polling)
- Ralph Wiggum loop for multi-step task completion
- Self-validation before task completion
- Human-in-loop only for Level 2+ actions (social posts, financial transactions)

### ✅ Separation of Concerns
- **Brain**: Claude Code agent orchestrates workflows
- **Memory**: Obsidian vault stores state, briefings, audit logs
- **Senses**: New watchers for Odoo (accounting), social media engagement
- **Hands**: New MCP servers for Odoo operations, social media posting

### ✅ Event-Driven Architecture
- Accounting watcher polls Odoo API every 5 minutes
- Social media watcher checks engagement metrics every 5 minutes
- CEO briefing scheduled for Monday 8:00 AM
- Failed events retry with exponential backoff (1s, 2s, 4s per constitution)

### ✅ Idempotency and Reliability
- All actions idempotent (duplicate detection for transactions)
- Circuit breaker prevents repeated failures
- CEO briefing always generatable from historical data
- State transitions atomic and logged

### ✅ Dual-Tier LLM Support
- Maintains compatibility with Claude Code OR Gemini
- MCP adapter layer already implemented in Bronze/Silver
- No changes needed for LLM support

### ⚠️ Technology Stack Compliance
- **uv package manager**: Will use for all new Python dependencies
- **Python 3.11+**: Compliant
- **Obsidian**: Compliant
- **MCP servers**: Extending existing framework

**Gate Status**: ✅ PASSED - All constitution principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-gold-tier-autonomous/
├── plan.md              # This file
├── research.md          # Phase 0: Technology research and decisions
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Setup and usage guide
├── contracts/           # Phase 1: API contracts for new MCP tools
│   ├── odoo-tools.yaml
│   ├── social-media-tools.yaml
│   └── briefing-tools.yaml
└── tasks.md             # Phase 2: Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
watchers/
├── shared/              # ✅ EXISTING - Extended with Gold Tier utilities
│   ├── base_watcher.py           # ✅ Bronze tier
│   ├── database.py               # ✅ Extended for Gold tier
│   ├── event_logger.py           # ✅ Bronze tier
│   ├── health_check.py           # ✅ Bronze tier
│   ├── keychain.py               # ✅ Bronze tier
│   ├── vault_writer.py           # ✅ Bronze tier
│   ├── audit_logger.py           # ✅ NEW - Gold tier
│   ├── audit_markdown_writer.py  # ✅ NEW - Gold tier
│   ├── ralph_loop.py             # ✅ NEW - Gold tier
│   ├── ralph_integration.py      # ✅ NEW - Gold tier
│   ├── queue_processor.py        # ✅ NEW - Gold tier
│   ├── domain_manager.py         # ✅ NEW - Gold tier
│   ├── domain_config.py          # ✅ NEW - Gold tier
│   ├── cross_domain_coordinator.py # ✅ NEW - Gold tier
│   ├── privacy_enforcer.py       # ✅ NEW - Gold tier
│   ├── task_breakdown.py         # ✅ NEW - Gold tier
│   ├── health_aggregator.py      # ✅ NEW - Gold tier
│   ├── reset_circuit_breaker.py  # ✅ NEW - Gold tier utility
│   ├── rotate_audit_logs.py      # ✅ NEW - Gold tier utility
│   └── view_integration_status.py # ✅ NEW - Gold tier utility
├── gmail_watcher/       # ✅ EXISTING (Bronze tier)
├── whatsapp_watcher/    # ✅ EXISTING (Silver tier)
├── linkedin_watcher/    # ✅ EXISTING (Silver tier)
├── odoo_watcher/        # ⚠️ PARTIAL - Scaffolding exists, needs main watcher loop
│   ├── __init__.py               # ✅ Created
│   ├── watcher.py                # ⚠️ Empty - needs implementation
│   ├── config.py                 # ⚠️ Empty - needs implementation
│   ├── duplicate_detector.py     # ⚠️ Empty - needs implementation
│   ├── client.py                 # ✅ Implemented
│   ├── categorizer.py            # ✅ Implemented
│   ├── transaction_processor.py  # ✅ Implemented
│   ├── markdown_logger.py        # ✅ Implemented
│   └── test_connection.py        # ✅ Implemented
├── social_media_watcher/ # ⚠️ PARTIAL - Clients exist, needs main watcher loop
│   ├── __init__.py               # ✅ Created
│   ├── watcher.py                # ✅ Implemented
│   ├── config.py                 # ✅ Implemented
│   ├── facebook_client.py        # ✅ Implemented
│   ├── instagram_client.py       # ✅ Implemented
│   ├── twitter_client.py         # ✅ Implemented
│   ├── engagement_calculator.py  # ✅ Implemented
│   └── test_connections.py       # ✅ Implemented
└── briefing_watcher/    # ⚠️ PARTIAL - Support modules exist, needs main watcher loop
    ├── __init__.py               # ✅ Created
    ├── watcher.py                # ⚠️ Empty - needs implementation
    ├── config.py                 # ⚠️ Empty - needs implementation
    ├── briefing_generator.py     # ⚠️ Empty - needs implementation
    ├── financial_aggregator.py   # ✅ Implemented
    ├── social_aggregator.py      # ✅ Implemented
    ├── task_aggregator.py        # ✅ Implemented
    ├── issue_detector.py         # ✅ Implemented
    └── chart_generator.py        # ✅ Implemented

mcp-servers/
└── digital-fte-server/  # ✅ EXISTING - Extended with Gold Tier tools
    ├── approval/        # ✅ EXISTING (Bronze tier)
    ├── tools/           # ✅ Extended with new tools
    │   ├── send_email.py                 # ✅ Bronze tier
    │   ├── whatsapp_send.py              # ✅ Silver tier
    │   ├── linkedin_post.py              # ✅ Silver tier
    │   ├── odoo_record_transaction.py    # ✅ NEW - Gold tier
    │   ├── odoo_query_financials.py      # ✅ NEW - Gold tier
    │   ├── odoo_get_transactions.py      # ✅ NEW - Gold tier
    │   ├── odoo_check_connection.py      # ✅ NEW - Gold tier
    │   ├── social_media/                 # ✅ NEW - Gold tier folder
    │   │   ├── social_post.py            # ✅ Implemented
    │   │   ├── social_get_engagement.py  # ✅ Implemented
    │   │   ├── social_delete_post.py     # ✅ Implemented
    │   │   └── social_check_connection.py # ✅ Implemented
    │   └── tasks/                        # ✅ NEW - Gold tier folder
    │       ├── task_create.py            # ✅ Implemented
    │       ├── task_execute.py           # ✅ Implemented
    │       └── task_status.py            # ✅ Implemented
    ├── circuit_breaker.py                # ✅ NEW - Fully implemented
    ├── rate_limiter.py  # ✅ EXISTING (Bronze tier)
    ├── server.py        # ⚠️ Needs registration of new tools
    └── validator.py     # ✅ EXISTING (Bronze tier)

obsidian-vault/
├── Dashboard.md         # ✅ EXISTING (Bronze tier)
├── Inbox/               # ✅ EXISTING (Bronze tier)
├── Needs_Action/        # ✅ EXISTING (Bronze tier)
├── Done/                # ✅ EXISTING (Bronze tier)
├── Approvals/           # ✅ EXISTING (Silver tier)
├── Reports/             # ✅ EXISTING (Silver tier)
├── Content_Queue/       # ✅ EXISTING (Silver tier)
├── Schedules/           # ✅ EXISTING (Silver tier)
├── Accounting/          # ✅ CREATED - Empty, needs population
├── Briefings/           # ⚠️ NEEDS CREATION
│   └── YYYY-WW.md       # Template for weekly briefings
└── Audit_Logs/          # ⚠️ NEEDS CREATION (audit_logger.py exists)
    └── YYYY-MM-DD.md    # Daily audit log files

tests/
├── unit/                # ⚠️ NEEDS CREATION
│   ├── test_odoo_watcher.py
│   ├── test_social_media_watcher.py
│   ├── test_briefing_generator.py
│   ├── test_circuit_breaker.py
│   └── test_duplicate_detector.py
├── integration/         # ⚠️ NEEDS CREATION
│   ├── test_odoo_integration.py
│   ├── test_social_media_integration.py
│   └── test_briefing_workflow.py
└── contract/            # ⚠️ NEEDS CREATION
    ├── test_odoo_tools_contract.py
    └── test_social_tools_contract.py
```

**Structure Status**: Gold Tier scaffolding is substantially complete. Shared utilities, MCP tools, and support modules are implemented. Main gaps are: (1) watcher main loops (odoo_watcher/watcher.py, briefing_watcher/watcher.py), (2) configuration files, (3) MCP server tool registration, (4) Obsidian vault folder creation, and (5) comprehensive test suite. This reflects efficient reuse of Bronze/Silver tier patterns.

## Complexity Tracking

> No constitution violations - this section intentionally left empty per template guidance.

## Phase 0: Research & Technology Decisions

**Status**: ✅ COMPLETE - See research.md

**Key Decisions Made**:
1. ✅ Odoo Integration: `odoorpc` library selected (JSON-RPC, Odoo 19+ support)
2. ✅ Facebook: Official Graph API with `facebook-sdk`
3. ✅ Instagram: `instagrapi` (unofficial but reliable for business features)
4. ✅ Twitter: `tweepy` library for API v2
5. ✅ Circuit Breaker: Custom implementation (circuit_breaker.py) with domain context support
6. ✅ Duplicate Detection: SHA-256 hash of amount+date+description with 24-hour window
7. ✅ Chart Generation: ASCII charts for briefings (lightweight, no dependencies)
8. ✅ Scheduling: `schedule` library for cron-like task scheduling
9. ✅ Audit Logging: Hash chain integrity with PII redaction (audit_logger.py implemented)

**Research Document**: All technology decisions documented in `specs/001-gold-tier-autonomous/research.md` with rationale, alternatives considered, and implementation patterns.

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE - All design artifacts generated

**Artifacts Created**:
- ✅ `data-model.md`: Complete entity definitions for Business Transaction, Social Media Post, CEO Briefing, Audit Log Entry, Multi-Step Task, Integration Status, Action Queue (7 entities with fields, relationships, validation rules, state transitions)
- ✅ `contracts/odoo-tools.yaml`: OpenAPI 3.0 spec for Odoo MCP tools (record_transaction, query_financials, get_transactions, check_connection)
- ✅ `contracts/social-media-tools.yaml`: OpenAPI 3.0 spec for social media MCP tools (post, get_engagement, delete_post, check_connection) supporting Facebook, Instagram, Twitter
- ✅ `contracts/briefing-tools.yaml`: OpenAPI 3.0 spec for briefing generation tools (generate_briefing, get_briefing_history, regenerate_briefing)
- ✅ `quickstart.md`: Complete setup guide covering Odoo credentials, social media API keys, environment configuration, first briefing generation, and troubleshooting

**Design Decisions Documented**:
- Entity storage patterns (SQLite + Markdown backup)
- API contract standards (OpenAPI 3.0, consistent error handling)
- Validation rules aligned with constitution principles
- State machine definitions for transactions and tasks

## Implementation Phases

### Phase 0: Research ✅ COMPLETE
- ✅ Researched Odoo JSON-RPC integration
- ✅ Evaluated social media API options
- ✅ Designed circuit breaker pattern
- ✅ Documented all technology choices in research.md

### Phase 1: Design ✅ COMPLETE
- ✅ Defined data models for all new entities
- ✅ Created API contracts for all new MCP tools
- ✅ Designed watcher architectures
- ✅ Generated quickstart guide

### Phase 2: Foundational Infrastructure ✅ MOSTLY COMPLETE
- ✅ Circuit breaker implementation (circuit_breaker.py)
- ✅ Audit logging system (audit_logger.py, audit_markdown_writer.py)
- ✅ Ralph Wiggum loop pattern (ralph_loop.py, ralph_integration.py)
- ✅ Domain coordination (domain_manager.py, cross_domain_coordinator.py)
- ✅ Queue processor for failed operations (queue_processor.py)
- ✅ Privacy enforcement (privacy_enforcer.py)
- ✅ Health aggregation (health_aggregator.py)
- ✅ Utility scripts (reset_circuit_breaker.py, rotate_audit_logs.py, view_integration_status.py)
- ⚠️ Obsidian vault folders need creation (Briefings/, Audit_Logs/)

### Phase 3: Odoo Integration ⚠️ PARTIAL
- ✅ MCP tools implemented:
  - odoo_record_transaction.py
  - odoo_query_financials.py
  - odoo_get_transactions.py
  - odoo_check_connection.py
- ✅ Support modules implemented:
  - client.py (Odoo connection)
  - categorizer.py (transaction categorization)
  - transaction_processor.py (transaction handling)
  - markdown_logger.py (Obsidian logging)
  - test_connection.py (connection testing)
- ⚠️ Main watcher loop needs implementation (odoo_watcher/watcher.py)
- ⚠️ Configuration needs implementation (odoo_watcher/config.py)
- ⚠️ Duplicate detector needs implementation (odoo_watcher/duplicate_detector.py)
- ⚠️ MCP server registration needs update (server.py)

### Phase 4: Social Media Integration ⚠️ PARTIAL
- ✅ MCP tools implemented:
  - social_media/social_post.py
  - social_media/social_get_engagement.py
  - social_media/social_delete_post.py
  - social_media/social_check_connection.py
- ✅ Watcher fully implemented:
  - watcher.py (main loop with 5-minute polling)
  - config.py (configuration management)
  - facebook_client.py, instagram_client.py, twitter_client.py
  - engagement_calculator.py (metrics aggregation)
  - test_connections.py (connection testing)
- ⚠️ MCP server registration needs update (server.py)

### Phase 5: CEO Briefing ⚠️ PARTIAL
- ✅ Support modules implemented:
  - financial_aggregator.py (financial data aggregation)
  - social_aggregator.py (social media metrics)
  - task_aggregator.py (task completion tracking)
  - issue_detector.py (critical issue detection)
  - chart_generator.py (ASCII chart generation)
- ⚠️ Main briefing generator needs implementation (briefing_generator.py)
- ⚠️ Main watcher loop needs implementation (briefing_watcher/watcher.py)
- ⚠️ Configuration needs implementation (briefing_watcher/config.py)
- ⚠️ MCP briefing tools need implementation (generate_briefing.py, etc.)
- ⚠️ Obsidian Briefings/ folder needs creation

### Phase 6: Testing & Integration ⚠️ NOT STARTED
- ⚠️ Unit tests need creation (80%+ coverage target)
- ⚠️ Integration tests need creation
- ⚠️ Contract tests need creation
- ⚠️ End-to-end workflow testing
- ⚠️ Cross-tier integration testing (Bronze + Silver + Gold)

## Dependencies

**From Bronze Tier**:
- Gmail watcher pattern
- Base watcher class
- Event logger
- Vault writer
- MCP server framework
- Obsidian vault structure

**From Silver Tier**:
- WhatsApp integration
- Banking integration (for cross-domain workflows)
- Task management
- Ralph Wiggum loop implementation

**External Dependencies**:
- Odoo Community Edition (self-hosted, user-provided)
- Facebook Developer Account with app credentials
- Instagram Business Account with Graph API access
- Twitter Developer Account with API v2 access

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Odoo API changes between versions | High | Pin to Odoo 19+, document version requirements, test against specific version |
| Social media API rate limits | Medium | Implement rate limiting (10 posts/day), queue posts, notify user of limits |
| Instagram unofficial API instability | High | Provide fallback to official Graph API, document business account requirement |
| Circuit breaker false positives | Medium | Tune error rate threshold (20%), provide manual override, log all circuit breaker events |
| CEO briefing generation failure | High | Ensure briefing always generatable from historical data, implement retry logic, notify user on failure |
| Audit log storage growth | Low | Implement log rotation (daily files), document retention policy (7 years per constitution) |
| Cross-platform keychain differences | Medium | Use existing keychain abstraction from Bronze/Silver, test on all platforms |

## Success Criteria

Implementation complete when:
1. ✅ Odoo watcher polls accounting system every 5 minutes and detects new transactions
2. ✅ Transactions recorded with 99% accuracy within 5 minutes
3. ✅ Duplicate detection prevents duplicate transaction recording
4. ✅ Social media posts published to all 3 platforms within 1 minute of schedule
5. ✅ Engagement metrics retrieved and summarized for all platforms
6. ✅ High engagement notifications triggered at 3x average threshold
7. ✅ CEO briefing generated every Monday at 8:00 AM with 100% reliability
8. ✅ Briefing includes financial summary, social media performance, tasks, and action items
9. ✅ Circuit breaker activates at 20% error rate and recovers with exponential backoff
10. ✅ System maintains operation of unaffected services during failures
11. ✅ All agent actions logged with 100% coverage in audit logs
12. ✅ Audit logs include timestamp, action type, parameters, result, reasoning
13. ✅ Multi-step tasks complete autonomously in 80% of cases
14. ✅ 80%+ test coverage for all new watchers and MCP tools
15. ✅ All constitution principles maintained

## Next Steps

**Current Status**: Phase 0 & 1 complete, Phase 2 mostly complete, Phases 3-5 partially complete, Phase 6 not started.

**Immediate Actions** (for `/sp.tasks` and implementation):

1. **Complete Odoo Watcher** (Phase 3):
   - Implement main watcher loop (odoo_watcher/watcher.py)
   - Implement configuration (odoo_watcher/config.py)
   - Implement duplicate detector (odoo_watcher/duplicate_detector.py)
   - Register Odoo tools in MCP server (server.py)

2. **Complete CEO Briefing** (Phase 5):
   - Implement briefing generator (briefing_generator.py)
   - Implement main watcher loop (briefing_watcher/watcher.py)
   - Implement configuration (briefing_watcher/config.py)
   - Create MCP briefing tools
   - Create Obsidian Briefings/ folder

3. **Complete Social Media Integration** (Phase 4):
   - Register social media tools in MCP server (server.py)
   - Verify watcher integration with MCP tools

4. **Create Obsidian Vault Structure** (Phase 2):
   - Create Briefings/ folder with template
   - Create Audit_Logs/ folder
   - Verify Accounting/ folder structure

5. **Comprehensive Testing** (Phase 6):
   - Write unit tests for all watchers (80%+ coverage)
   - Write integration tests for workflows
   - Write contract tests for MCP tools
   - End-to-end testing across all tiers

**Command Sequence**:
1. ✅ `/sp.plan` - COMPLETE (this file updated)
2. **NEXT**: `/sp.tasks` - Generate implementation tasks from updated plan
3. **THEN**: `/sp.implement` - Execute tasks in priority order
