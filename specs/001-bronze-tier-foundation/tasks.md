# Tasks: Bronze Tier Foundation

**Input**: Design documents from `/specs/001-bronze-tier-foundation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in specification - test tasks omitted per requirements

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure per plan.md
- Vault: `obsidian-vault/`
- Watchers: `watchers/`
- Skills: `.claude/skills/vault-operations/`
- Scripts: `scripts/`
- Tests: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: `watchers/`, `scripts/`, `tests/unit/`, `tests/integration/`
- [X] T002 Create Python dependencies file at `watchers/pyproject.toml` with uv project configuration and dependencies: google-api-python-client, google-auth-oauthlib, pyyaml, python-dotenv
- [X] T003 [P] Create `.gitignore` entries for `credentials.json`, `watchers/.auth/`, `watchers/.env`, `obsidian-vault/`, `uv.lock`
- [X] T004 [P] Create environment template at `watchers/.env.example` with GMAIL_LABEL, POLL_INTERVAL, CREDENTIALS_PATH, TOKEN_PATH
- [ ] T005 [P] Create watcher logs directory at `watchers/logs/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities that multiple user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create Python utility module at `watchers/utils.py` with filename sanitization function (remove unsafe chars, truncate to 50 chars, lowercase)
- [X] T007 [P] Create YAML frontmatter helper functions in `watchers/vault_utils.py` (generate_frontmatter, parse_frontmatter)
- [X] T008 [P] Create timestamp formatting utilities in `watchers/utils.py` (format_timestamp_filename, format_iso8601)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Obsidian Vault Initialization (Priority: P1) 🎯 MVP

**Goal**: Create structured Obsidian vault with folders, configuration, Dashboard.md, and Company_Handbook.md

**Independent Test**: Verify vault directory exists with /Inbox, /Needs_Action, /Done folders, .obsidian configuration, Dashboard.md and Company_Handbook.md are accessible and editable, vault opens successfully in Obsidian application

### Implementation for User Story 1

- [X] T009 [P] [US1] Create vault initialization script at `scripts/setup_vault.py` with main function and argument parsing
- [X] T010 [P] [US1] Implement vault directory creation in `scripts/setup_vault.py`: create `obsidian-vault/` root directory
- [X] T011 [P] [US1] Implement folder creation in `scripts/setup_vault.py`: create `obsidian-vault/Inbox/`, `obsidian-vault/Needs_Action/`, `obsidian-vault/Done/`
- [X] T012 [US1] Create .obsidian configuration directory at `obsidian-vault/.obsidian/`
- [X] T013 [US1] Create minimal workspace.json at `obsidian-vault/.obsidian/workspace.json` with main workspace structure opening Dashboard.md by default
- [X] T014 [US1] Create Dashboard.md template at `obsidian-vault/Dashboard.md` with sections: Last Updated, Folder Status (Inbox/Needs_Action/Done counts with links), Recent Activity (placeholder for 10 notes), Quick Links
- [X] T015 [US1] Create Company_Handbook.md template at `obsidian-vault/Company_Handbook.md` with sections: Business Information, Key Contacts (table), Business Processes, Guidelines, Resources
- [X] T016 [US1] Add success logging and verification to `scripts/setup_vault.py` (print created directories and files)
- [X] T017 [US1] Add --force flag to `scripts/setup_vault.py` to reinitialize existing vault

**Checkpoint**: At this point, User Story 1 should be fully functional - vault can be opened in Obsidian with all folders and documents visible

---

## Phase 4: User Story 2 - Claude Code Vault Integration (Priority: P2)

**Goal**: Enable Claude Code to read, write, and update vault files using built-in tools

**Independent Test**: Claude Code creates a new note in /Inbox with proper frontmatter, reads an existing note and displays full content, updates Dashboard.md with new content, moves a note from /Inbox to /Needs_Action and Dashboard reflects the change

### Implementation for User Story 2

- [X] T018 [P] [US2] Create dashboard update script at `scripts/update_dashboard.py` with main function
- [X] T019 [US2] Implement folder scanning in `scripts/update_dashboard.py`: count .md files in Inbox/, Needs_Action/, Done/ using glob or os.walk
- [X] T020 [US2] Implement note metadata extraction in `scripts/update_dashboard.py`: read frontmatter from all notes, extract created timestamps
- [X] T021 [US2] Implement recent activity generation in `scripts/update_dashboard.py`: sort notes by created timestamp descending, take first 10, format as wikilinks with timestamps
- [X] T022 [US2] Implement dashboard regeneration in `scripts/update_dashboard.py`: generate markdown from template with current counts and recent notes, write to Dashboard.md atomically (use temp file + rename pattern for atomicity)
- [X] T023 [US2] Add timestamp formatting to `scripts/update_dashboard.py`: Last Updated field with current datetime
- [X] T024 [US2] Create note creation helper at `scripts/create_note.py` with parameters: folder, title, content, sender (optional), email_date (optional), tags (optional)
- [X] T025 [US2] Implement filename generation in `scripts/create_note.py`: timestamp + sanitized title using utils.py functions
- [X] T026 [US2] Implement frontmatter generation in `scripts/create_note.py`: use vault_utils.py to create YAML with title, created, source, sender, email_date, status, tags
- [X] T027 [US2] Implement note body formatting in `scripts/create_note.py`: markdown structure with metadata header and content
- [X] T028 [US2] Implement file write in `scripts/create_note.py`: write to obsidian-vault/{folder}/{filename}.md
- [X] T029 [US2] Add dashboard update call to `scripts/create_note.py`: automatically update dashboard after note creation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - vault exists and can be programmatically manipulated

---

## Phase 5: User Story 3 - Agent Skills for Vault Operations (Priority: P3)

**Goal**: Create vault-operations agent skill with 5 operations (create, read, move, update-dashboard, search)

**Independent Test**: Invoke vault-create-note skill and verify note created with proper metadata, invoke vault-move-note and verify file relocated with status updated, invoke vault-search and verify matching notes returned, invoke vault-update-dashboard and verify dashboard refreshed

### Implementation for User Story 3

- [X] T030 [P] [US3] Create skill directory at `.claude/skills/vault-operations/`
- [X] T031 [US3] Create SKILL.md at `.claude/skills/vault-operations/SKILL.md` with frontmatter: name="vault-operations", description with triggers (creating notes, reading vault, moving files, updating dashboard, searching)
- [X] T032 [US3] Document Create Note operation in SKILL.md: parameters (folder, title, content, sender, email_date, tags), behavior (sanitize, generate filename, create frontmatter, write file, update dashboard), example usage
- [X] T033 [US3] Document Read Note operation in SKILL.md: parameters (path), behavior (read file, parse frontmatter, extract body), tool usage (Read tool), example usage
- [X] T034 [US3] Document Move Note operation in SKILL.md: parameters (source_path, target_folder), behavior (verify source exists, move file with mv, update status field, update dashboard), tool usage (Bash tool for mv), example usage
- [X] T035 [US3] Document Update Dashboard operation in SKILL.md: no parameters, behavior (count files, read frontmatter, sort by created, generate markdown, write Dashboard.md), tool usage (Bash for find/wc, Read/Write tools), example usage
- [X] T036 [US3] Document Search Vault operation in SKILL.md: parameters (query, case_sensitive, max_results), behavior (use Grep tool with pattern, return matches with excerpts), tool usage (Grep tool), example usage
- [X] T037 [US3] Add tool usage patterns section to SKILL.md: Read tool (read notes), Write tool (create/update notes), Grep tool (search), Glob tool (list notes), Bash tool (move/count files)
- [X] T038 [US3] Add workflow examples to SKILL.md: Create New Note workflow (4 steps), Update Dashboard workflow (4 steps)
- [X] T039 [P] [US3] Create references directory at `.claude/skills/vault-operations/references/` (optional)
- [X] T040 [P] [US3] Create frontmatter schema reference at `.claude/skills/vault-operations/references/frontmatter-schema.md` with field specifications from data-model.md (optional)

**Checkpoint**: All user stories 1-3 should now be independently functional - vault exists, can be manipulated programmatically, and has agent skill interface

---

## Phase 6: User Story 4 - Watcher Script Implementation (Priority: P4)

**Goal**: Implement Gmail watcher that monitors labeled emails and creates vault notes every 3 minutes

**Independent Test**: Send test email with "ToVault" label, verify note appears in obsidian-vault/Inbox/ within 3 minutes with email subject, sender, plain text body, and timestamp, verify watcher logs activity, verify Dashboard.md reflects new inbox item

### Implementation for User Story 4

- [X] T041 [P] [US4] Create Gmail authentication module at `watchers/gmail_auth.py` with authenticate_gmail() function
- [X] T042 [US4] Implement OAuth2 flow in `watchers/gmail_auth.py`: load credentials.json, check for existing token.json, refresh if expired, run local server flow if needed, save token to watchers/.auth/token.json
- [X] T043 [US4] Add SCOPES constant in `watchers/gmail_auth.py`: ['https://www.googleapis.com/auth/gmail.readonly']
- [X] T044 [P] [US4] Create Gmail operations module at `watchers/gmail_operations.py` with get_label_id() function
- [X] T045 [US4] Implement label retrieval in `watchers/gmail_operations.py`: list labels, find by name, create if doesn't exist, return label ID
- [X] T046 [US4] Implement message listing in `watchers/gmail_operations.py`: get_messages_with_label(service, label_id) returns list of message IDs
- [X] T047 [US4] Implement message details extraction in `watchers/gmail_operations.py`: get_message_details(service, message_id) returns dict with subject, sender, date, body, timestamp
- [X] T048 [US4] Implement plain text body extraction in `watchers/gmail_operations.py`: extract_body(payload) handles multipart messages, prefers text/plain, falls back to HTML with tag stripping, base64 decodes
- [X] T049 [P] [US4] Create error handling module at `watchers/error_handler.py` with GmailErrorHandler class
- [X] T050 [US4] Implement transient error detection in `watchers/error_handler.py`: is_transient_error() checks for 429, 500, 502, 503, 504, ConnectionError, TimeoutError
- [X] T051 [US4] Implement exponential backoff in `watchers/error_handler.py`: exponential_backoff_retry(func, max_retries=3) with delays 1s, 2s, 4s
- [X] T052 [P] [US4] Create main watcher script at `watchers/gmail_watcher.py` with GmailWatcher class
- [X] T053 [US4] Implement watcher initialization in `watchers/gmail_watcher.py`: __init__ with label_name, poll_interval, setup_logging()
- [X] T054 [US4] Implement logging setup in `watchers/gmail_watcher.py`: configure logging to watchers/logs/gmail-watcher.log and console, INFO level
- [X] T055 [US4] Implement watcher initialize() in `watchers/gmail_watcher.py`: authenticate Gmail, get label ID, initialize last_message_id to None
- [X] T056 [US4] Implement process_new_messages() in `watchers/gmail_watcher.py`: get messages since last_message_id, loop through messages, extract details with retry, create vault note, update last_message_id
- [X] T057 [US4] Implement create_vault_note() in `watchers/gmail_watcher.py`: generate filename from timestamp and sanitized subject, create frontmatter with email fields, format body with metadata header, write to obsidian-vault/Inbox/, call dashboard update script via subprocess.run(['python', 'scripts/update_dashboard.py'])
- [X] T058 [US4] Implement main run() loop in `watchers/gmail_watcher.py`: initialize, infinite loop with process_new_messages(), sleep poll_interval, handle KeyboardInterrupt, log errors and continue
- [X] T059 [US4] Add environment variable loading to `watchers/gmail_watcher.py`: load from .env using python-dotenv, get GMAIL_LABEL, POLL_INTERVAL, CREDENTIALS_PATH, TOKEN_PATH
- [X] T060 [US4] Add command-line entry point to `watchers/gmail_watcher.py`: if __name__ == '__main__' block, create GmailWatcher instance, call run()
- [ ] T061 [US4] Add error logging for failed message processing in `watchers/gmail_watcher.py`: log error but continue with next message (don't crash watcher)

**Checkpoint**: All user stories should now be independently functional - complete Bronze Tier system with automated email capture

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T062 [P] Create README.md at project root with Bronze Tier overview, features list, setup instructions reference to quickstart.md
- [X] T063 [P] Validate quickstart.md instructions: verify all steps are accurate, all file paths correct, all commands work
- [X] T064 [P] Add error handling improvements: ensure all scripts have try-except blocks with meaningful error messages, proper exit codes, validate folder names (Inbox/Needs_Action/Done only), check file paths exist before operations, verify environment variables are set
- [X] T065 [P] Add input validation: validate folder names in create_note.py, validate file paths exist before operations, validate environment variables are set
- [X] T066 Create integration test script at `tests/integration/test_end_to_end.py`: initialize vault, create test note, update dashboard, verify all operations (optional - can be manual testing)
- [X] T067 [P] Performance validation: create 100 test notes in vault, verify note creation time < 2s, dashboard update < 5s, no performance degradation (validates SC-007)
- [ ] T068 [P] Reliability validation: run watcher for 24 hours, verify continuous operation without crashes, check logs for errors, validate uptime meets SC-008 (optional - can be manual testing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - provides utilities for all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase - creates vault structure
- **User Story 2 (Phase 4)**: Depends on User Story 1 (vault must exist) - adds programmatic access
- **User Story 3 (Phase 5)**: Depends on User Story 2 (vault operations must work) - adds agent skill interface
- **User Story 4 (Phase 6)**: Depends on User Story 1 (vault must exist) and User Story 2 (note creation must work) - adds automation
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (vault must exist first) - Builds on vault structure
- **User Story 3 (P3)**: Depends on User Story 2 (vault operations must work) - Wraps operations in skill interface
- **User Story 4 (P4)**: Depends on User Story 1 (vault structure) and User Story 2 (note creation) - Adds automation layer

### Within Each User Story

- Setup and Foundational tasks can run in parallel where marked [P]
- User Story 1: Most tasks can run in parallel (different files)
- User Story 2: Dashboard update depends on note creation utilities
- User Story 3: SKILL.md sections can be written in parallel
- User Story 4: Authentication, operations, error handling can be developed in parallel, then integrated in main watcher

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- All Foundational tasks marked [P] can run in parallel (T007, T008)
- User Story 1: T009-T011 can run in parallel (different scripts/folders), T014-T015 can run in parallel (different files)
- User Story 2: T018-T023 (dashboard) and T024-T028 (note creation) can run in parallel (different files)
- User Story 3: T032-T036 (documentation sections) can run in parallel, T039-T040 can run in parallel
- User Story 4: T041-T043 (auth), T044-T048 (operations), T049-T051 (error handling) can run in parallel (different modules)
- Polish: All tasks marked [P] can run in parallel (T062-T065)

---

## Parallel Example: User Story 1

```bash
# Launch vault structure tasks together:
Task: "Create vault initialization script at scripts/setup_vault.py"
Task: "Implement vault directory creation in scripts/setup_vault.py"
Task: "Implement folder creation in scripts/setup_vault.py"

# Launch template creation tasks together:
Task: "Create Dashboard.md template at obsidian-vault/Dashboard.md"
Task: "Create Company_Handbook.md template at obsidian-vault/Company_Handbook.md"
```

---

## Parallel Example: User Story 4

```bash
# Launch module development in parallel:
Task: "Create Gmail authentication module at watchers/gmail_auth.py"
Task: "Create Gmail operations module at watchers/gmail_operations.py"
Task: "Create error handling module at watchers/error_handler.py"

# Then integrate in main watcher:
Task: "Create main watcher script at watchers/gmail_watcher.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (utilities)
3. Complete Phase 3: User Story 1 (vault initialization)
4. **STOP and VALIDATE**: Run `python scripts/setup_vault.py`, open vault in Obsidian, verify all folders and files present
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (open in Obsidian) → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (create/read notes programmatically) → Deploy/Demo
4. Add User Story 3 → Test independently (invoke agent skills) → Deploy/Demo
5. Add User Story 4 → Test independently (send test email, verify note created) → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (vault structure)
   - Developer B: User Story 2 (vault operations) - waits for US1 vault to exist
   - Developer C: User Story 3 (agent skills) - waits for US2 operations to work
   - Developer D: User Story 4 (watcher) - waits for US1 vault and US2 note creation
3. Stories complete sequentially due to dependencies, but modules within stories can be parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No test tasks included (not requested in specification)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Total tasks: 68 (T001-T068)
- MVP scope: Phases 1-3 (T001-T017) = 17 tasks for basic vault
- Full Bronze Tier: All phases (T001-T068) = 68 tasks
