# Tasks: Silver Tier Functional Assistant

**Input**: Design documents from `/specs/001-silver-tier-functional/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are excluded per template guidelines.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md, this is a multi-component distributed system:
- `watchers/` - Python watcher processes
- `mcp-servers/digital-fte-server/` - MCP server
- `.claude/skills/` - Agent skills
- `obsidian-vault/` - Obsidian vault folders
- `scripts/` - Utility scripts
- `tests/` - Test suites

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create watchers/ directory structure with subdirectories: gmail_watcher/, whatsapp_watcher/, linkedin_watcher/, shared/
- [ ] T002 [P] Initialize watchers Python project with uv in watchers/pyproject.toml
- [ ] T003 [P] Initialize mcp-servers/digital-fte-server/ directory and Python project with uv
- [ ] T004 [P] Install Node.js dependencies for WhatsApp bridge in watchers/whatsapp_watcher/package.json
- [ ] T005 [P] Create obsidian-vault new folders: Approvals/, Rejected/, Expired/, Content_Queue/, Schedules/, Reports/
- [ ] T006 [P] Create scripts/setup/ directory with install_watchers.py and configure_apis.py
- [ ] T007 [P] Create scripts/scheduler/ directory structure
- [ ] T008 [P] Create tests/ directory structure: watchers/, mcp_server/, agent_skills/, integration/, fixtures/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create SQLite schema in watchers/shared/database.py with tables: watchers, events, actions
- [ ] T010 [P] Implement shared event logger in watchers/shared/event_logger.py
- [ ] T011 [P] Implement shared health check module in watchers/shared/health_check.py
- [ ] T012 [P] Implement shared vault writer in watchers/shared/vault_writer.py for creating Obsidian notes
- [ ] T013 [P] Create API configuration script in scripts/setup/configure_apis.py for Gmail, WhatsApp, LinkedIn OAuth2/session setup
- [ ] T014 Implement OS keychain integration in watchers/shared/keychain.py for credential storage (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- [ ] T015 [P] Create watcher base class in watchers/shared/base_watcher.py with polling loop, health checks, error handling
- [ ] T016 [P] Create test fixtures in tests/fixtures/mock_apis.py for Gmail, WhatsApp, LinkedIn API mocking
- [ ] T017 [P] Create sample event fixtures in tests/fixtures/sample_events.json

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Multi-Channel Watcher System (Priority: P1) 🎯 MVP

**Goal**: Monitor Gmail, WhatsApp, and LinkedIn simultaneously, capturing all communications in Obsidian vault

**Independent Test**: Send test email, WhatsApp message, and LinkedIn notification, verify three separate notes appear in obsidian-vault/Inbox/ within polling interval with channel-specific metadata

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement WhatsApp watcher in watchers/whatsapp_watcher/watcher.py using base_watcher.py
- [ ] T019 [P] [US1] Create WhatsApp Node.js bridge in watchers/whatsapp_watcher/bridge.js using whatsapp-web.js library
- [ ] T020 [P] [US1] Implement WhatsApp watcher config in watchers/whatsapp_watcher/config.py with session path and QR timeout
- [ ] T021 [P] [US1] Implement LinkedIn watcher in watchers/linkedin_watcher/watcher.py using linkedin-api library
- [ ] T022 [P] [US1] Implement LinkedIn watcher config in watchers/linkedin_watcher/config.py with session cookies and notification types
- [ ] T023 [US1] Update shared event logger to support WhatsApp and LinkedIn event schemas per contracts/watcher-events.json
- [ ] T024 [US1] Implement watcher startup script in scripts/setup/install_watchers.py to launch all 3 watchers as daemon processes
- [ ] T025 [US1] Add graceful degradation logic: ensure individual watcher failures don't crash other watchers
- [ ] T026 [US1] Implement centralized logging to watchers/logs/ with rotation policy

**Checkpoint**: At this point, all 3 watchers should run continuously, detect events, and create notes in /Inbox independently

---

## Phase 4: User Story 2 - MCP Server for External Actions (Priority: P2)

**Goal**: Enable AI assistant to send emails and post to LinkedIn via MCP server with proper validation and rate limiting

**Independent Test**: Invoke MCP server's send-email tool with test parameters and verify email is sent, then invoke linkedin-post tool and verify post appears on LinkedIn

### Implementation for User Story 2

- [X] T027 [P] [US2] Create FastAPI MCP server in mcp-servers/digital-fte-server/server.py with /tools/list, /tools/invoke, /health endpoints
- [X] T028 [P] [US2] Implement send-email tool in mcp-servers/digital-fte-server/tools/send_email.py using Gmail API
- [X] T029 [P] [US2] Implement linkedin-post tool in mcp-servers/digital-fte-server/tools/linkedin_post.py using unofficial LinkedIn API
- [X] T030 [P] [US2] Implement whatsapp-send tool in mcp-servers/digital-fte-server/tools/whatsapp_send.py using WhatsApp bridge
- [X] T031 [US2] Implement input validator in mcp-servers/digital-fte-server/validator.py using Pydantic models per contracts/mcp-server.json
- [X] T032 [US2] Implement rate limiter in mcp-servers/digital-fte-server/rate_limiter.py with token bucket algorithm (Gmail: 100/day, LinkedIn: 100/day, WhatsApp: 1000/day)
- [X] T033 [US2] Add tool invocation logging to SQLite actions table with timestamp, tool name, sanitized parameters, result
- [X] T034 [US2] Implement error handling with structured responses (success/failure status, action ID, error details, retry-after)
- [X] T035 [US2] Create MCP server startup script with uvicorn configuration

**Checkpoint**: MCP server should respond to tool invocations, validate inputs, enforce rate limits, and execute external actions

---

## Phase 5: User Story 3 - Human-in-the-Loop Approval Workflow (Priority: P3)

**Goal**: Require user approval for sensitive actions (Level 2+) before execution, preventing unauthorized emails or social media posts

**Independent Test**: Have Claude Code attempt to send email, verify action is queued in /Approvals, approve via CLI command, confirm email is then sent

### Implementation for User Story 3

- [X] T036 [P] [US3] Implement action safety classifier in mcp-servers/digital-fte-server/approval/classifier.py (Level 0-3 classification)
- [X] T037 [P] [US3] Implement approval queue manager in mcp-servers/digital-fte-server/approval/queue.py to create notes in obsidian-vault/Approvals/
- [X] T038 [US3] Implement approval middleware in MCP server to intercept Level 2+ actions before execution
- [X] T039 [US3] Implement action executor in mcp-servers/digital-fte-server/approval/executor.py to execute approved actions and move notes to /Done
- [X] T040 [US3] Create approval-review agent skill in .claude/skills/approval-review/SKILL.md with CLI commands: list-pending, approve, reject, approve-all
- [X] T041 [US3] Implement approval expiration logic: auto-expire pending actions after 24 hours and move to /Expired
- [X] T042 [US3] Add rejection handling: move rejected actions to /Rejected with rejection reason
- [X] T043 [US3] Update action audit trail in SQLite with state transitions (pending → approved → executed)

**Checkpoint**: All Level 2+ actions should queue for approval, execute only after user approval, and maintain complete audit trail

---

## Phase 6: User Story 4 - LinkedIn Auto-Posting for Business Development (Priority: P4)

**Goal**: Automatically post business updates to LinkedIn on schedule with approval workflow integration

**Independent Test**: Create business update note in obsidian-vault/Content_Queue/ with schedule, wait for scheduled time, approve post, verify it appears on LinkedIn

### Implementation for User Story 4

- [X] T044 [P] [US4] Implement Content Queue monitor in scripts/scheduler/content_queue_monitor.py to scan /Content_Queue for scheduled posts
- [X] T045 [P] [US4] Create linkedin-draft agent skill in .claude/skills/linkedin-draft/SKILL.md for AI-assisted post drafting
- [X] T046 [US4] Implement post template variable substitution ({{company_name}}, {{date}}, {{milestone}}) in scripts/scheduler/template_engine.py
- [X] T047 [US4] Add LinkedIn character limit enforcement (3000 chars) with truncation logic
- [X] T048 [US4] Implement post performance tracking: fetch views, likes, comments from LinkedIn API and update note frontmatter
- [X] T049 [US4] Add rescheduling logic for rate limit errors: calculate next available time slot
- [X] T050 [US4] Integrate Content Queue monitor with approval workflow: queue posts for approval at scheduled time

**Checkpoint**: Scheduled LinkedIn posts should queue for approval at specified time, publish after approval, and track performance metrics

---

## Phase 7: User Story 5 - Claude Reasoning Loop for Plan Generation (Priority: P5)

**Goal**: Autonomously generate Plan.md files for complex tasks with structured steps, success criteria, and dependencies

**Independent Test**: Create note in /Needs_Action with complex task description, verify Plan.md file is created with structured sections within 30 seconds

### Implementation for User Story 5

- [X] T051 [P] [US5] Implement complexity detection algorithm in .claude/skills/reasoning-plan/complexity_scorer.py with multi-factor heuristic (word count, action verbs, dependencies)
- [X] T052 [P] [US5] Create reasoning-plan agent skill in .claude/skills/reasoning-plan/SKILL.md with automatic /Needs_Action monitoring
- [X] T053 [US5] Implement Plan.md generator in .claude/skills/reasoning-plan/plan_generator.py with sections: Goal, Context, Steps, Success Criteria, Risks, Rollback Procedure
- [X] T054 [US5] Add plan status tracking: update step status (pending → in-progress → completed → validated) as agent executes
- [X] T055 [US5] Implement success criteria validation: check all criteria met before marking task complete
- [X] T056 [US5] Add plan re-evaluation logic: update plan with alternative approaches when steps fail
- [X] T057 [US5] Implement task completion workflow: move task from /Needs_Action to /Done and update Dashboard.md summary
- [X] T058 [US5] Add complexity threshold configuration in .claude/skills/reasoning-plan/config.py (default: 25)

**Checkpoint**: Complex tasks should automatically trigger Plan.md generation, track execution progress, and validate completion

---

## Phase 8: User Story 6 - Scheduled Task Execution (Priority: P6)

**Goal**: Run tasks automatically on schedule (daily reports, weekly summaries) with retry logic and missed schedule handling

**Independent Test**: Create scheduled task with cron expression "0 9 * * 1", wait for Monday 9am, verify task executes and creates output in /Reports

### Implementation for User Story 6

- [X] T059 [P] [US6] Implement cron manager in scripts/scheduler/cron_manager.py for Unix/Linux crontab manipulation
- [X] T060 [P] [US6] Implement Task Scheduler manager in scripts/scheduler/taskscheduler_manager.py for Windows XML import
- [X] T061 [US6] Create platform detection logic in scripts/scheduler/__init__.py to select appropriate scheduler
- [X] T062 [US6] Implement task executor in scripts/scheduler/task_executor.py with retry logic (3 attempts, exponential backoff: 1s, 2s, 4s)
- [X] T063 [US6] Add missed schedule handling: check last_run_timestamp on startup, execute if within 24-hour window
- [X] T064 [US6] Implement schedule storage in obsidian-vault/Schedules/ with YAML frontmatter (cron expression, last_run, next_run)
- [X] T065 [US6] Create schedule-task agent skill in .claude/skills/schedule-task/SKILL.md for creating/managing scheduled tasks
- [X] T066 [US6] Add execution history tracking: store last 100 executions with status, duration, error messages
- [X] T067 [US6] Implement conflict resolution: execute tasks sequentially in priority order when scheduled for same time

**Checkpoint**: Scheduled tasks should execute at specified times, retry on failure, handle missed schedules, and persist across restarts

---

## Phase 9: Agent Skills & Integration

**Purpose**: Implement remaining agent skills and cross-component integration

- [X] T068 [P] Create watcher-status agent skill in .claude/skills/watcher-status/SKILL.md to check health of all 3 watchers
- [X] T069 [P] Create mcp-invoke agent skill in .claude/skills/mcp-invoke/SKILL.md to invoke MCP server tools from Claude Code
- [X] T070 Implement watcher health check aggregation: query all watchers and report status (healthy/degraded/unhealthy)
- [X] T071 Add MCP server registration to Claude Code: configure MCP server URL in .claude/config
- [X] T072 Create quickstart validation script in scripts/setup/validate_setup.py to run all verification tests from quickstart.md
- [X] T073 Document agent skill usage examples in each SKILL.md file with parameters, examples, error handling

**Checkpoint**: All 6 agent skills should be functional and documented, enabling full AI assistant capabilities

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T074 [P] Add comprehensive error handling across all watchers with specific error messages per edge case
- [X] T075 [P] Implement PII redaction in all log files (email addresses, phone numbers, sensitive content)
- [X] T076 [P] Add rate limit monitoring dashboard: track daily usage for Gmail, LinkedIn, WhatsApp
- [X] T077 [P] Create migration documentation in docs/migration-to-official-apis.md for WhatsApp and LinkedIn
- [X] T078 Code cleanup: remove debug logging, optimize polling intervals, refactor duplicate code
- [X] T079 Security hardening: validate all file paths, sanitize user inputs, check permissions
- [X] T080 Performance optimization: reduce vault write latency, optimize SQLite queries, cache API responses
- [X] T081 Run quickstart.md validation: execute all 6 verification tests and confirm passing
- [X] T082 Update README.md with setup instructions, architecture diagram, troubleshooting guide

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 (Watchers): Can start after Foundational - No dependencies on other stories
  - US2 (MCP Server): Can start after Foundational - No dependencies on other stories
  - US3 (Approval): Depends on US2 (MCP Server must exist to intercept actions)
  - US4 (LinkedIn Scheduling): Depends on US2 (MCP Server) and US3 (Approval workflow)
  - US5 (Reasoning Loop): Can start after Foundational - No dependencies on other stories
  - US6 (Scheduler): Can start after Foundational - No dependencies on other stories
- **Agent Skills (Phase 9)**: Depends on US1, US2, US3 completion
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Foundational (Phase 2) - BLOCKS ALL
    ├── US1 (Watchers) - Independent
    ├── US2 (MCP Server) - Independent
    │   ├── US3 (Approval) - Depends on US2
    │   │   └── US4 (LinkedIn Scheduling) - Depends on US2 + US3
    ├── US5 (Reasoning Loop) - Independent
    └── US6 (Scheduler) - Independent
```

### Within Each User Story

- Parallel tasks marked [P] can run simultaneously (different files)
- Sequential tasks must complete in order (dependencies on previous tasks)
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 (Setup)**: T002, T003, T004, T005, T006, T007, T008 can all run in parallel
- **Phase 2 (Foundational)**: T010, T011, T012, T013, T014, T015, T016, T017 can run in parallel after T009
- **Phase 3 (US1)**: T018, T019, T020, T021, T022 can run in parallel
- **Phase 4 (US2)**: T027, T028, T029, T030 can run in parallel
- **Phase 5 (US3)**: T036, T037 can run in parallel
- **Phase 6 (US4)**: T044, T045 can run in parallel
- **Phase 7 (US5)**: T051, T052 can run in parallel
- **Phase 8 (US6)**: T059, T060 can run in parallel
- **Phase 9**: T068, T069 can run in parallel
- **Phase 10**: T074, T075, T076, T077 can run in parallel

**After Foundational completes**: US1, US2, US5, US6 can all start in parallel (if team capacity allows)

---

## Parallel Example: User Story 1 (Watchers)

```bash
# Launch all watcher implementations in parallel:
Task T018: "Implement WhatsApp watcher in watchers/whatsapp_watcher/watcher.py"
Task T019: "Create WhatsApp Node.js bridge in watchers/whatsapp_watcher/bridge.js"
Task T020: "Implement WhatsApp watcher config in watchers/whatsapp_watcher/config.py"
Task T021: "Implement LinkedIn watcher in watchers/linkedin_watcher/watcher.py"
Task T022: "Implement LinkedIn watcher config in watchers/linkedin_watcher/config.py"

# All 5 tasks work on different files with no dependencies
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T017) - CRITICAL
3. Complete Phase 3: User Story 1 (T018-T026)
4. **STOP and VALIDATE**: Run independent test - send test messages, verify notes created
5. Deploy/demo if ready - Multi-channel monitoring is now functional

**Estimated Effort**: 8-12 hours for MVP (Setup + Foundational + US1)

### Incremental Delivery

1. **Foundation** (T001-T017): Setup + Foundational → 4-6 hours
2. **MVP** (T018-T026): Add US1 (Watchers) → Test independently → 4-6 hours
3. **Active Assistant** (T027-T043): Add US2 (MCP) + US3 (Approval) → Test independently → 6-8 hours
4. **Business Value** (T044-T050): Add US4 (LinkedIn Scheduling) → Test independently → 3-4 hours
5. **Intelligence** (T051-T058): Add US5 (Reasoning Loop) → Test independently → 3-4 hours
6. **Automation** (T059-T067): Add US6 (Scheduler) → Test independently → 3-4 hours
7. **Polish** (T068-T082): Integration + Polish → 2-3 hours

**Total Estimated Effort**: 25-35 hours (within 20-30 hour target with optimization)

### Parallel Team Strategy

With 3 developers after Foundational phase completes:

1. **Team completes Setup + Foundational together** (T001-T017)
2. **Parallel development**:
   - Developer A: US1 (Watchers) + US5 (Reasoning Loop)
   - Developer B: US2 (MCP Server) → US3 (Approval)
   - Developer C: US6 (Scheduler) + Agent Skills
3. **Integration**: US4 (LinkedIn Scheduling) requires US2 + US3
4. **Polish**: All developers contribute to Phase 10

**Estimated Effort with 3 developers**: 12-15 hours wall-clock time

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution compliance verified in plan.md - all tasks align with principles
- Tests are NOT included per specification (no explicit test request)
- Focus on minimal viable implementation per 20-30 hour constraint
