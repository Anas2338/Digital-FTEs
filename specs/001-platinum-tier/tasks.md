# Tasks: Platinum Tier - Always-On Cloud + Local Executive

**Input**: Design documents from `/specs/001-platinum-tier/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are omitted per template guidelines.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md project structure:
- **New directories**: `cloud/`, `sync/`, `coordination/`
- **Existing**: `watchers/`, `mcp-servers/`, `obsidian-vault/`
- **Vault coordination**: `obsidian-vault/In_Progress/`, `obsidian-vault/Pending_Approval/`, `obsidian-vault/Updates/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure for Platinum Tier

- [x] T001 Create cloud agent directory structure: cloud/agent/, cloud/watchers/, cloud/health/, cloud/deployment/
- [x] T002 Create vault sync directory structure: sync/ with git_sync.py, conflict_resolver.py, atomic_writer.py, sync_monitor.py
- [x] T003 Create coordination directory structure: coordination/ with claim_manager.py, logical_clock.py, work_queue.py, approval_processor.py, dashboard_merger.py
- [x] T004 Create vault coordination directories: obsidian-vault/In_Progress/{cloud,local}/, obsidian-vault/Pending_Approval/{email,social,accounting}/, obsidian-vault/Updates/
- [x] T005 [P] Create .gitignore for vault sync exclusions (secrets, binaries, sessions) in obsidian-vault/.gitignore.vault
- [x] T006 [P] Install Python dependencies with uv: gitpython, systemd-python (cloud agent requirements)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Implement Lamport timestamp class in coordination/logical_clock.py (LamportTimestamp, LamportClock with tick/update methods)
- [x] T008 [P] Implement atomic write pattern in sync/atomic_writer.py (write to .tmp, then rename for data integrity)
- [x] T009 [P] Create Agent Configuration entity schema in obsidian-vault/config/agent-config.json (agent_id, credential_scope, vault_path, sync_config, health_config)
- [x] T010 Implement base coordination utilities in coordination/work_queue.py (WorkQueueItem class, status transitions, file path helpers)
- [x] T011 [P] Create vault sync .gitignore template excluding .env, *.session, credentials.json, tokens/ in sync/.gitignore.vault

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cloud Agent 24/7 Operation (Priority: P1) 🎯 MVP

**Goal**: Deploy cloud agent running continuously on cloud VM, monitoring email/social media, generating drafts even when local is offline

**Independent Test**: Deploy cloud agent, shut down local machine, send test email, verify cloud agent detects and creates draft in vault

### Implementation for User Story 1

- [x] T012 [P] [US1] Create cloud agent main entry point in cloud/agent/cloud_agent.py (agent loop, watcher orchestration, error handling)
- [x] T013 [P] [US1] Implement cloud agent configuration manager in cloud/agent/config.py (load agent-config.json, validate read-only credentials)
- [x] T014 [P] [US1] Implement read-only credential manager in cloud/agent/credential_manager.py (load from cloud .env, enforce read-only scope)
- [x] T015 [US1] Create cloud-specific Gmail watcher in cloud/watchers/gmail_watcher_cloud.py (read-only monitoring, draft generation)
- [x] T016 [US1] Create cloud-specific social media watcher in cloud/watchers/social_watcher_cloud.py (read-only monitoring, post draft generation)
- [x] T017 [US1] Implement draft generator in cloud/agent/draft_generator.py (email reply drafts, social post drafts using LLM)
- [x] T018 [US1] Create systemd service unit file in cloud/deployment/cloud-agent.service (auto-restart, resource limits, logging)
- [x] T019 [US1] Create cloud VM setup script in cloud/deployment/setup_cloud_vm.sh (install dependencies, create cloudagent user, configure firewall)
- [x] T020 [US1] Create cloud agent installation script in cloud/deployment/install_dependencies.sh (Python 3.11, uv, git, nginx, postgresql)
- [x] T021 [US1] Create systemd configuration script in cloud/deployment/configure_systemd.sh (enable cloud-agent.service, configure restart policies)
- [x] T022 [US1] Create cloud .env template in cloud/.env.cloud.template (read-only Gmail, social media, Odoo credentials)
- [x] T023 [US1] Update cloud agent to write drafts to vault using atomic write pattern (integrate atomic_writer.py)

**Checkpoint**: Cloud agent deployed and running 24/7, generating drafts when local is offline

---

## Phase 4: User Story 2 - Work-Zone Specialization (Priority: P1)

**Goal**: Implement work-zone separation where cloud drafts, local approves and executes, maintaining security

**Independent Test**: Trigger email while local offline, verify cloud creates draft in /Pending_Approval/email/, bring local online, approve draft, verify local sends email via MCP

### Implementation for User Story 2

- [x] T024 [P] [US2] Create Draft Approval entity in coordination/draft_approval.py (approval_id, draft_type, approval_status, created_by, approved_by with logical timestamps)
- [x] T025 [P] [US2] Create Work Queue Item entity in coordination/work_queue_item.py (item_id, domain, item_type, status, created_at, claimed_by with logical timestamps)
- [x] T026 [US2] Implement approval processor in coordination/approval_processor.py (monitor /Pending_Approval/, present to user via Dashboard.md, process approvals, track approval rate for SC-011)
- [x] T027 [US2] Implement Dashboard.md merger in coordination/dashboard_merger.py (merge /Updates/ from cloud into Dashboard.md, single-writer rule enforcement)
- [x] T028 [US2] Update cloud agent to write drafts to /Pending_Approval/{domain}/ with Draft Approval metadata
- [x] T029 [US2] Update local agent to monitor /Pending_Approval/ directories and update Dashboard.md with pending approvals section
- [x] T030 [US2] Implement local agent approval workflow: read Dashboard.md approvals, execute via MCP, log action, move to /Done/
- [x] T031 [US2] Add work-zone validation: cloud agent rejects write operations, local agent rejects draft generation for sensitive domains (banking, whatsapp)
- [x] T032 [US2] Create action plan writer for cloud agent in cloud/agent/action_plan_writer.py (write to /Needs_Action/{domain}/ for tasks requiring local execution)

**Checkpoint**: Work-zone specialization functional - cloud drafts, local approves and executes

---

## Phase 5: User Story 3 - Vault Synchronization and Coordination (Priority: P1)

**Goal**: Implement Git-based vault sync with claim-by-move coordination to prevent duplicate work

**Independent Test**: Cloud creates task in /Needs_Action/, verify sync to local within 60s, local claims task (moves to /In_Progress/local/), verify cloud respects claim

### Implementation for User Story 3

- [x] T033 [P] [US3] Implement Git sync manager in sync/git_sync.py (pull, commit, push with atomic operations, retry on conflict)
- [x] T034 [P] [US3] Implement conflict resolver in sync/conflict_resolver.py (detect Git merge conflicts, resolve using logical timestamps, first-write-wins)
- [x] T035 [P] [US3] Implement sync monitor in sync/sync_monitor.py (track last_sync_at, sync_lag_seconds, detect failures >5 minutes)
- [x] T036 [P] [US3] Create Sync Status entity in sync/sync_status.py (agent_id, last_sync_at, sync_lag, sync_health, consecutive_failures, queued_operations)
- [x] T037 [US3] Implement claim manager in coordination/claim_manager.py (claim-by-move: move file from /Needs_Action/ to /In_Progress/{agent}/, handle race conditions)
- [x] T038 [US3] Implement race detector in coordination/race_detector.py (detect simultaneous claims using Git push failures, resolve with logical timestamps)
- [x] T039 [US3] Create vault sync systemd timer in cloud/deployment/vault-sync.timer (trigger every 30 seconds)
- [x] T040 [US3] Create vault sync service in cloud/deployment/vault-sync.service (run git_sync.py, handle failures)
- [x] T041 [US3] Create sync script for cloud agent in cloud/deployment/sync-vault.sh (git pull --rebase, git add, git commit, git push with error handling)
- [x] T042 [US3] Implement extended sync failure handler: queue operations locally, halt cross-agent coordination when sync lag >1 hour
- [x] T043 [US3] Create local sync script for Windows/macOS/Linux (PowerShell/bash) with scheduled task/cron configuration
- [x] T044 [US3] Add sync status monitoring to both agents: check .sync-status/{agent_id}.json, alert on sync_health: "failed"

**Checkpoint**: Vault sync operational with <60s latency, claim-by-move prevents duplicate work

---

## Phase 6: User Story 4 - Cloud-Hosted Odoo Accounting (Priority: P2)

**Goal**: Deploy Odoo Community Edition on cloud VM with HTTPS, backups, and cloud agent integration for 24/7 accounting

**Independent Test**: Deploy Odoo to cloud, configure HTTPS, create test transaction via cloud agent, verify draft accounting entry in /Pending_Approval/accounting/, approve locally, verify posted to Odoo

### Implementation for User Story 4

- [ ] T045 [P] [US4] Create Odoo installation script in cloud/deployment/setup_odoo.sh (install PostgreSQL, Odoo 17.0, configure database)
- [ ] T046 [P] [US4] Create SSL configuration script in cloud/deployment/configure_ssl.sh (nginx reverse proxy, Let's Encrypt certbot)
- [ ] T047 [P] [US4] Create Odoo backup script in cloud/deployment/odoo-backup.sh (pg_dump, filestore tar, 30-day retention)
- [ ] T048 [US4] Configure Odoo systemd service with resource limits (2-3 workers, 256MB shared_buffers)
- [ ] T049 [US4] Create cloud-specific Odoo watcher in cloud/watchers/odoo_watcher_cloud.py (monitor transactions, generate draft accounting entries)
- [ ] T050 [US4] Update cloud agent to write accounting drafts to /Pending_Approval/accounting/ with transaction metadata
- [ ] T051 [US4] Update local agent approval workflow to handle accounting entries: approve, post to Odoo via MCP, log in audit trail
- [ ] T052 [US4] Add Odoo health check endpoint monitoring in cloud agent (check /web/health every 5 minutes)
- [ ] T053 [US4] Configure daily Odoo backup cron job in /etc/cron.daily/odoo-backup

**Checkpoint**: Odoo running 24/7 on cloud with HTTPS, automated backups, cloud agent creating draft accounting entries

---

## Phase 7: User Story 5 - Health Monitoring and Alerting (Priority: P2)

**Goal**: Implement Monit-based health monitoring with automatic recovery and multi-channel alerting

**Independent Test**: Simulate failures (stop cloud agent, stop Odoo, break vault sync), verify health checks detect within 5 minutes, alerts sent within 2 minutes, automatic recovery attempted

### Implementation for User Story 5

- [ ] T054 [P] [US5] Create Health Check Result entity in cloud/health/health_check.py (check_id, agent_id, check_type, status, latency_ms, error_message, recovery_attempted)
- [ ] T055 [P] [US5] Implement health monitor orchestrator in cloud/health/health_monitor.py (run checks every 5 minutes, coordinate recovery, trigger alerts, calculate 30-day rolling uptime for SC-001)
- [ ] T056 [P] [US5] Implement agent health check in cloud/health/agent_health.py (HTTP ping to agent endpoint, verify responsiveness)
- [ ] T057 [P] [US5] Implement sync health check in cloud/health/sync_health.py (check sync_lag from Sync Status, alert if >5 minutes)
- [ ] T058 [P] [US5] Implement service health check in cloud/health/service_health.py (check Odoo /web/health, API connectivity tests)
- [ ] T059 [P] [US5] Implement alerter in cloud/health/alerter.py (send alerts via email/SMS/push, support Twilio, Pushover, ntfy.sh)
- [ ] T060 [US5] Create Monit configuration file in cloud/deployment/monitrc (check cloud-agent process, vault sync timestamp, Odoo health)
- [ ] T061 [US5] Create alert script in cloud/deployment/alert.sh (send SMS via Twilio, push via Pushover/ntfy.sh)
- [ ] T062 [US5] Configure Monit to restart services after 2 failed checks, alert after 3 restart attempts
- [ ] T063 [US5] Create health check SQLite database schema in cloud/health/health_checks.db (store check results, 90-day retention, track manual interventions for SC-008)
- [ ] T064 [US5] Implement automatic recovery logic: restart cloud-agent.service, restart odoo.service, trigger vault sync
- [ ] T065 [US5] Add health monitoring to local agent: monitor local services, vault sync status, alert on failures

**Checkpoint**: Health monitoring operational with 5-minute checks, 2-minute alerts, automatic recovery

---

## Phase 8: User Story 6 - Agent-to-Agent Messaging (Priority: P3) [OPTIONAL - Phase 2]

**Goal**: Implement direct A2A messaging for faster coordination while maintaining vault audit trail

**Independent Test**: Implement A2A for email drafting, measure latency improvement vs file-based, verify vault still logs all decisions

**Note**: This is a Phase 2 optimization, not required for MVP. Include only if time permits after US1-US5 are stable.

### Implementation for User Story 6

- [ ] T066 [P] [US6] Create A2A Message entity in coordination/a2a_message.py (message_id, sender, recipient, timestamp, payload)
- [ ] T067 [P] [US6] Implement A2A messaging protocol in coordination/a2a_protocol.py (send message, receive message, fallback to file-based)
- [ ] T068 [US6] Add A2A messaging to cloud agent for draft notifications (send message to local when draft ready)
- [ ] T069 [US6] Add A2A message receiver to local agent (process messages, still write approval to vault for audit)
- [ ] T070 [US6] Implement fallback logic: if A2A fails or times out, use file-based coordination automatically
- [ ] T071 [US6] Add A2A latency metrics to health monitoring (compare with file-based sync latency)

**Checkpoint**: A2A messaging operational as optimization, vault audit trail maintained

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final deployment validation

- [ ] T072 [P] Create comprehensive deployment guide in specs/001-platinum-tier/DEPLOYMENT.md (step-by-step cloud VM setup)
- [ ] T073 [P] Create troubleshooting guide in specs/001-platinum-tier/TROUBLESHOOTING.md (common issues, log locations, recovery procedures)
- [ ] T074 [P] Add logging to all coordination operations (claim, release, sync, conflict resolution) with structured format
- [ ] T075 [P] Implement audit trail for all agent actions: log which agent performed each operation with logical timestamps
- [ ] T076 Run quickstart.md validation: execute all 7 phases, verify demo scenario completes successfully
- [ ] T077 Security audit: verify cloud agent has read-only credentials only, no secrets in vault sync, WhatsApp sessions local-only
- [ ] T078 Performance tuning: optimize vault sync frequency, tune Odoo workers, adjust health check intervals
- [ ] T079 [P] Create monitoring dashboard template in obsidian-vault/Monitoring_Dashboard.md (agent status, sync health, Odoo uptime)
- [ ] T080 Final integration test: run demo scenario end-to-end (email arrives while local offline → cloud drafts → local approves → send)
- [ ] T081 [P] Implement credential rotation scheduler in cloud/agent/credential_rotator.py (90-day rotation cycle per FR-042, alert 7 days before expiry)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1 stories) can proceed in parallel after Foundational
  - US4, US5 (P2 stories) depend on US1 (cloud agent operational)
  - US6 (P3 story) depends on US1-US5 being stable (Phase 2 optimization)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Integrates with US1 but independently testable
- **User Story 3 (P1)**: Can start after Foundational - Required by US2 for coordination
- **User Story 4 (P2)**: Depends on US1 (cloud agent running) - Independently testable once US1 complete
- **User Story 5 (P2)**: Depends on US1 (cloud agent running) - Independently testable once US1 complete
- **User Story 6 (P3)**: Depends on US1-US5 stable - Optional optimization

### Within Each User Story

- Foundational entities (Lamport timestamps, atomic writes) before story-specific entities
- Entity classes before services that use them
- Services before agent integration
- Agent integration before deployment scripts
- Deployment scripts before validation

### Parallel Opportunities

- **Setup (Phase 1)**: T001-T006 can all run in parallel (different directories)
- **Foundational (Phase 2)**: T007-T011 marked [P] can run in parallel
- **US1**: T012-T014, T015-T016, T019-T020 can run in parallel (different files)
- **US2**: T024-T025, T026-T027 can run in parallel
- **US3**: T033-T036 can run in parallel
- **US4**: T045-T047 can run in parallel
- **US5**: T054-T059 can run in parallel
- **US6**: T066-T067 can run in parallel
- **Polish**: T072-T075, T079 can run in parallel

---

## Parallel Example: User Story 1 (Cloud Agent)

```bash
# Launch all parallel tasks for US1 together:
Task T012: "Create cloud agent main entry point in cloud/agent/cloud_agent.py"
Task T013: "Implement cloud agent configuration manager in cloud/agent/config.py"
Task T014: "Implement read-only credential manager in cloud/agent/credential_manager.py"

# Then launch watchers in parallel:
Task T015: "Create cloud-specific Gmail watcher in cloud/watchers/gmail_watcher_cloud.py"
Task T016: "Create cloud-specific social media watcher in cloud/watchers/social_watcher_cloud.py"

# Then launch deployment scripts in parallel:
Task T019: "Create cloud VM setup script in cloud/deployment/setup_cloud_vm.sh"
Task T020: "Create cloud agent installation script in cloud/deployment/install_dependencies.sh"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T011) - CRITICAL
3. Complete Phase 3: User Story 1 (T012-T023) - Cloud agent 24/7
4. Complete Phase 4: User Story 2 (T024-T032) - Work-zone specialization
5. Complete Phase 5: User Story 3 (T033-T044) - Vault sync and coordination
6. **STOP and VALIDATE**: Test demo scenario (email → cloud draft → local approve → send)
7. Deploy/demo if ready

**MVP Delivers**: 24/7 cloud agent with work-zone separation and vault coordination - core Platinum Tier value

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Cloud agent operational
3. Add US2 → Test independently → Work-zone separation functional
4. Add US3 → Test independently → Coordination working (MVP complete!)
5. Add US4 → Test independently → Cloud Odoo operational
6. Add US5 → Test independently → Health monitoring active
7. Add US6 (optional) → Test independently → A2A optimization
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T011)
2. Once Foundational is done:
   - Developer A: User Story 1 (T012-T023)
   - Developer B: User Story 2 (T024-T032)
   - Developer C: User Story 3 (T033-T044)
3. After US1 complete:
   - Developer D: User Story 4 (T045-T053)
   - Developer E: User Story 5 (T054-T065)
4. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 81 tasks
- Phase 1 (Setup): 6 tasks
- Phase 2 (Foundational): 5 tasks (BLOCKING)
- Phase 3 (US1 - Cloud Agent): 12 tasks
- Phase 4 (US2 - Work-Zone): 9 tasks
- Phase 5 (US3 - Vault Sync): 12 tasks
- Phase 6 (US4 - Odoo): 9 tasks
- Phase 7 (US5 - Health Monitoring): 12 tasks
- Phase 8 (US6 - A2A Messaging): 6 tasks [OPTIONAL]
- Phase 9 (Polish): 10 tasks

**Parallel Opportunities**: 35 tasks marked [P] can run in parallel within their phase

**MVP Scope**: Phases 1-5 (US1-US3) = 44 tasks for core Platinum Tier functionality

**Independent Test Criteria**:
- US1: Cloud agent processes events while local offline
- US2: Cloud drafts, local approves and executes
- US3: Agents coordinate via vault without conflicts
- US4: Odoo operational 24/7 with cloud agent integration
- US5: Health monitoring detects failures and alerts
- US6: A2A messaging improves latency while maintaining audit trail

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US6 (A2A messaging) is optional Phase 2 optimization - implement only after US1-US5 stable
- Tests are NOT included per specification (no explicit test requirements)
